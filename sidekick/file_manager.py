"""
File system operations for code synchronization.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class FileManager:
    """Manages file system operations for code synchronization."""

    def __init__(self, workspace: Path):
        self.workspace = workspace

    def _get_project_dir(self, tenant: str, project_id: str) -> Path:
        """Get the directory path for a specific tenant/project."""
        return self.workspace / tenant / project_id

    def _get_functions_file(self, tenant: str, project_id: str) -> Path:
        """Get the functions.py file path for a specific tenant/project."""
        return self._get_project_dir(tenant, project_id) / "functions.py"

    async def write_code(self, tenant: str, project_id: str, code: str) -> bool:
        """
        Write code to the tenant/project's functions.py file.

        Args:
            tenant: The tenant identifier
            project_id: The project identifier
            code: The Python code to write

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure project directory exists
            project_dir = self._get_project_dir(tenant, project_id)
            project_dir.mkdir(parents=True, exist_ok=True)

            # Write code to functions.py
            functions_file = self._get_functions_file(tenant, project_id)

            # Use asyncio to write file without blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: functions_file.write_text(code, encoding='utf-8')
            )

            logger.info(f"Code written to {functions_file}")
            return True

        except Exception as e:
            logger.error(f"Error writing code for {tenant}/{project_id}: {e}")
            return False

    async def read_code(self, tenant: str, project_id: str) -> Optional[str]:
        """
        Read code from the tenant/project's functions.py file.

        Args:
            tenant: The tenant identifier
            project_id: The project identifier

        Returns:
            The code content if successful, None otherwise
        """
        try:
            functions_file = self._get_functions_file(tenant, project_id)

            if not functions_file.exists():
                logger.warning(f"Functions file does not exist: {functions_file}")
                return None

            # Use asyncio to read file without blocking
            code = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: functions_file.read_text(encoding='utf-8')
            )

            logger.debug(f"Code read from {functions_file}")
            return code

        except Exception as e:
            logger.error(f"Error reading code for {tenant}/{project_id}: {e}")
            return None

    def get_tenant_projects(self) -> list[tuple[str, str]]:
        """
        Get all existing tenant/project combinations in the workspace.

        Returns:
            List of (tenant, project_id) tuples
        """
        try:
            tenant_projects = []

            if not self.workspace.exists():
                return tenant_projects

            for tenant_dir in self.workspace.iterdir():
                if tenant_dir.is_dir():
                    for project_dir in tenant_dir.iterdir():
                        if project_dir.is_dir():
                            # Check if it has a functions.py file
                            functions_file = project_dir / "functions.py"
                            if functions_file.exists():
                                tenant_projects.append((tenant_dir.name, project_dir.name))

            return tenant_projects

        except Exception as e:
            logger.error(f"Error getting tenant projects: {e}")
            return []

    def project_exists(self, tenant: str, project_id: str) -> bool:
        """
        Check if a tenant/project exists in the workspace.

        Args:
            tenant: The tenant identifier
            project_id: The project identifier

        Returns:
            True if project exists, False otherwise
        """
        functions_file = self._get_functions_file(tenant, project_id)
        return functions_file.exists()

    async def delete_project(self, tenant: str, project_id: str) -> bool:
        """
        Delete a tenant/project and its files.

        Args:
            tenant: The tenant identifier
            project_id: The project identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            project_dir = self._get_project_dir(tenant, project_id)

            if not project_dir.exists():
                logger.warning(f"Project directory does not exist: {project_dir}")
                return True

            # Use asyncio to delete directory without blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._remove_directory(project_dir)
            )

            logger.info(f"Project deleted: {tenant}/{project_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting project {tenant}/{project_id}: {e}")
            return False

    def _remove_directory(self, directory: Path):
        """Recursively remove a directory and its contents."""
        import shutil
        shutil.rmtree(directory)