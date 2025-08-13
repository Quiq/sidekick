"""
CLI interface for Sidekick server.
"""

import os
import click
import uvicorn
from pathlib import Path

from .server import SidekickServer


@click.command()
@click.option(
    "--port",
    "-p",
    default=43001,
    type=int,
    help="Port to run the server on (default: 43001)"
)
@click.option(
    "--workspace",
    "-w",
    default=None,
    type=click.Path(),
    help="Workspace directory for synced code (default: ~/.aistudio)"
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["critical", "error", "warning", "info", "debug"]),
    help="Log level (default: info)"
)
def main(port: int, workspace: str, log_level: str):
    """
    Start the Sidekick server for AI Studio code synchronization.

    Sidekick enables bidirectional code synchronization between AI Studio
    and your local file system through WebSocket connections.
    """
    # Set default workspace if not provided
    if workspace is None:
        workspace = os.path.expanduser("~/.aistudio")

    # Ensure workspace directory exists
    workspace_path = Path(workspace)
    workspace_path.mkdir(parents=True, exist_ok=True)

    # Always use localhost for security
    host = "localhost"

    click.echo(f"🚀 Starting Sidekick server...")
    click.echo(f"   Host: {host}")
    click.echo(f"   Port: {port}")
    click.echo(f"   Workspace: {workspace}")
    click.echo(f"   WebSocket URL: ws://{host}:{port}/ws?tenant=<tenant>&projectId=<projectId>&sidekickVersion=<version>")
    click.echo()

    # Create and configure the server
    server = SidekickServer(workspace=workspace)
    app = server.create_app()

    # Run the server
    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level=log_level,
            access_log=True
        )
    except KeyboardInterrupt:
        click.echo("\n👋 Shutting down Sidekick server...")
    except Exception as e:
        click.echo(f"❌ Error starting server: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()