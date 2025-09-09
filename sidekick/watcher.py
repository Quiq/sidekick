"""
File system watcher for monitoring local code changes.
"""

import asyncio
import logging
from pathlib import Path
from typing import Callable, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent


logger = logging.getLogger(__name__)


class CodeFileHandler(FileSystemEventHandler):
    """Handler for file system events on functions.py files."""

    def __init__(self, workspace: Path, callback: Callable[[str, str, Path], None]):
        self.workspace = workspace
        self.callback = callback
        self._loop = None

    def set_event_loop(self, loop):
        """Set the asyncio event loop for async callbacks."""
        self._loop = loop

    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only handle functions.py files
        if file_path.name != "functions.py":
            return

        # Extract tenant and project_id from path
        try:
            # Path should be: workspace/projects/tenant/project_id/functions.py
            relative_path = file_path.relative_to(self.workspace)
            if len(relative_path.parts) == 4 and relative_path.parts[0] == "projects":  # projects/tenant/project_id/functions.py
                tenant = relative_path.parts[1]
                project_id = relative_path.parts[2]

                logger.info(f"File modified: {file_path} (tenant: {tenant}, project: {project_id})")

                # Schedule the callback in the event loop
                if self._loop and not self._loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        self.callback(tenant, project_id, file_path),
                        self._loop
                    )

        except ValueError:
            # File is not within workspace
            logger.debug(f"Ignoring file outside workspace: {file_path}")
        except Exception as e:
            logger.error(f"Error processing file modification event: {e}")


class FileWatcher:
    """Watches for changes to functions.py files in project directories."""

    def __init__(self, workspace: Path, on_file_changed: Callable[[str, str, Path], None]):
        self.workspace = workspace
        self.on_file_changed = on_file_changed
        self.observer: Optional[Observer] = None
        self.handler: Optional[CodeFileHandler] = None
        self._loop = None

    def start(self):
        """Start watching for file changes."""
        try:
            # Get the current event loop
            self._loop = asyncio.get_event_loop()

            # Create handler and observer
            self.handler = CodeFileHandler(self.workspace, self.on_file_changed)
            self.handler.set_event_loop(self._loop)

            self.observer = Observer()
            self.observer.schedule(
                self.handler,
                str(self.workspace),
                recursive=True
            )

            self.observer.start()
            logger.info(f"File watcher started for workspace: {self.workspace}")

        except Exception as e:
            logger.error(f"Error starting file watcher: {e}")
            raise

    def stop(self):
        """Stop watching for file changes."""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5.0)
                self.observer = None

            self.handler = None
            self._loop = None

            logger.info("File watcher stopped")

        except Exception as e:
            logger.error(f"Error stopping file watcher: {e}")

    def is_running(self) -> bool:
        """Check if the file watcher is currently running."""
        return self.observer is not None and self.observer.is_alive()

