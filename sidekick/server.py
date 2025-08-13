"""
FastAPI server with WebSocket support for code synchronization.
"""

import json
import logging
import asyncio
import time
import hashlib
from pathlib import Path
from typing import Dict, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from packaging import version

from .file_manager import FileManager
from .watcher import FileWatcher
from . import __version__


logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for different project keys."""

    def __init__(self):
        # Map of project_key -> set of websockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_key: str):
        """Accept a new WebSocket connection for a project key."""
        await websocket.accept()
        if project_key not in self.active_connections:
            self.active_connections[project_key] = set()
        self.active_connections[project_key].add(websocket)
        logger.info(f"WebSocket connected for project: {project_key}")

    def disconnect(self, websocket: WebSocket, project_key: str):
        """Remove a WebSocket connection."""
        if project_key in self.active_connections:
            self.active_connections[project_key].discard(websocket)
            if not self.active_connections[project_key]:
                del self.active_connections[project_key]
        logger.info(f"WebSocket disconnected for project: {project_key}")

    async def send_to_project(self, project_key: str, message: dict):
        """Send a message to all connections for a specific project."""
        if project_key not in self.active_connections:
            return

        disconnected = set()
        for websocket in self.active_connections[project_key]:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                disconnected.add(websocket)

        # Clean up disconnected websockets
        for websocket in disconnected:
            self.disconnect(websocket, project_key)


class SidekickServer:
    """Main Sidekick server class."""

    def __init__(self, workspace: str):
        self.workspace = Path(workspace)
        self.file_manager = FileManager(self.workspace)
        self.connection_manager = ConnectionManager()
        self.file_watcher = None

        # Track content hashes to prevent sync loops
        # Format: {project_key: content_hash}
        self.content_hashes: Dict[str, str] = {}

        # Ensure workspace exists
        self.workspace.mkdir(parents=True, exist_ok=True)

        logger.info(f"Sidekick server initialized with workspace: {self.workspace}")

    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        app = FastAPI(
            title="Sidekick",
            description="AI Studio code synchronization server",
            version="0.1.0"
        )

        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return JSONResponse({
                "status": "healthy",
                "workspace": str(self.workspace),
                "active_connections": list(self.connection_manager.active_connections.keys()),
                "tenant_projects": self.file_manager.get_tenant_projects(),
                "timestamp": int(time.time() * 1000)
            })

        @app.websocket("/ws")
        async def websocket_endpoint(
            websocket: WebSocket,
            tenant: str = Query(..., description="Tenant identifier"),
            projectId: str = Query(..., description="Project identifier"),
            sidekickVersion: str = Query(..., description="Client Sidekick version")
        ):
            """WebSocket endpoint for code synchronization."""
            await self.handle_websocket_connection(websocket, tenant, projectId, sidekickVersion)

        # Start file watcher when app starts
        @app.on_event("startup")
        async def startup_event():
            """Initialize file watcher on startup."""
            self.file_watcher = FileWatcher(
                workspace=self.workspace,
                on_file_changed=self._on_file_changed
            )
            self.file_watcher.start()
            logger.info("File watcher started")

        @app.on_event("shutdown")
        async def shutdown_event():
            """Clean up resources on shutdown."""
            if self.file_watcher:
                self.file_watcher.stop()
                logger.info("File watcher stopped")

        return app

    async def handle_websocket_connection(self, websocket: WebSocket, tenant: str, project_id: str, client_version: str):
        """Handle a WebSocket connection for a specific tenant/project."""
        # Check client version if provided - must match exactly
        if client_version:
            try:
                client_ver = version.parse(client_version)
                server_ver = version.parse(__version__)

                if client_ver != server_ver:
                    logger.error(
                        f"Version mismatch: Client version {client_version} does not match server version {__version__}. "
                        f"Please run 'git pull' to update to the matching version."
                    )
                    await websocket.close(code=1008, reason="Version mismatch - please update Sidekick")
                    return
            except Exception as e:
                logger.error(f"Could not parse sidekick version '{client_version}': {e}")
                await websocket.close(code=1008, reason="Invalid version format")
                return

        connection_key = f"{tenant}/{project_id}"
        await self.connection_manager.connect(websocket, connection_key)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                await self._handle_message(tenant, project_id, message)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for {tenant}/{project_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket connection for {tenant}/{project_id}: {e}")
        finally:
            self.connection_manager.disconnect(websocket, connection_key)

    async def _handle_message(self, tenant: str, project_id: str, message: dict):
        """Handle incoming WebSocket messages."""
        message_type = message.get("type")

        if message_type == "codeUpdated":
            await self._handle_code_updated(tenant, project_id, message)
        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def _handle_code_updated(self, tenant: str, project_id: str, message: dict):
        """Handle codeUpdated message from client."""
        try:
            payload = message.get("payload", {})
            code = payload.get("code", "")
            project_key = f"{tenant}/{project_id}"

            # Calculate and store content hash to prevent sync loops
            content_hash = self._calculate_content_hash(code)
            self.content_hashes[project_key] = content_hash

            # Write code to file system
            success = await self.file_manager.write_code(tenant, project_id, code)

            if success:
                logger.info(f"Code updated for {tenant}/{project_id} (hash: {content_hash[:8]})")
            else:
                logger.error(f"Failed to write code for {tenant}/{project_id}")

        except Exception as e:
            logger.error(f"Error handling codeUpdated message: {e}")

    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content for loop prevention."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    async def _on_file_changed(self, tenant: str, projectId: str, file_path: Path):
        """Callback for when a file changes locally."""
        try:
            # Read the updated file content
            project_key = f"{tenant}/{projectId}"
            code = await self.file_manager.read_code(tenant, projectId)

            if code is not None:
                # Calculate hash of current content
                current_hash = self._calculate_content_hash(code)

                # Check if this content is the same as what we last processed
                # If so, skip sending to prevent sync loops
                if project_key in self.content_hashes and self.content_hashes[project_key] == current_hash:
                    logger.debug(f"Skipping file change notification for {project_key} - content hash matches (loop prevention)")
                    return

                # Update stored hash and send notification
                self.content_hashes[project_key] = current_hash

                # Send codeUpdated message to all connected clients for this project
                message = {
                    "type": "codeUpdated",
                    "payload": {
                        "code": code,
                        "timestamp": int(time.time() * 1000)
                    }
                }

                await self.connection_manager.send_to_project(project_key, message)
                logger.info(f"Sent file change notification for project: {project_key} (hash: {current_hash[:8]})")

        except Exception as e:
            logger.error(f"Error handling file change for {project_key}: {e}")