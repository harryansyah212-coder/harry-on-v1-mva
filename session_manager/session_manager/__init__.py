#!/usr/bin/env python3
"""
HARRY ON Session Manager Package v2.0.0
Cross-Session Persistence + GitHub Sync + Universal Token

Main entry point:
    from session_manager import harry_on_command
    response = harry_on_command("HARRY ON sync")
"""

from .session_manager import SessionManager, get_session_manager
from .project_registry import ProjectRegistry
from .resume_engine import ResumeEngine, handle_harry_on_command
from .auto_backup import AutoBackup
from .github_sync import GitHubSync
from .universal_token import UniversalTokenManager, set_universal_token, get_universal_token
from .harry_on_command_processor import HARRYONCommandProcessor, harry_on_command

__version__ = "2.0.0"
__author__ = "HARRY ON V1 MVA UNLIMITED v2.0.0"
__all__ = [
    "SessionManager",
    "get_session_manager",
    "ProjectRegistry",
    "ResumeEngine",
    "AutoBackup",
    "GitHubSync",
    "UniversalTokenManager",
    "set_universal_token",
    "get_universal_token",
    "HARRYONCommandProcessor",
    "harry_on_command",
    "handle_harry_on_command"
]
