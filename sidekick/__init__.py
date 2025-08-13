"""
Sidekick - AI Studio code synchronization server.

Sidekick enhances your AI Studio experience by facilitating code editing
in your editor of choice through bidirectional WebSocket synchronization.
"""

__version__ = "0.1.0"
__author__ = "Sidekick Team"
__email__ = "team@sidekick.dev"

from .server import SidekickServer
from .cli import main

__all__ = ["SidekickServer", "main"]