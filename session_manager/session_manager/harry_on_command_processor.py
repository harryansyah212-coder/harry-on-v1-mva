#!/usr/bin/env python3
"""
HARRY ON Command Processor v3.0.0
THE MAIN ENTRY POINT for all HARRY ON commands.

This file is called whenever user types "HARRY ON" in chat.
It auto-detects token, auto-restores projects, and handles all commands.
"""

import sys
import os
import json
import datetime
from pathlib import Path

# Ensure path
sys.path.insert(0, "/mnt/agents/output/harry_on_v1_mva/")

from session_manager.universal_token import get_token_manager, set_universal_token
from session_manager.resume_engine import ResumeEngine


class HARRYONCommandProcessor:
    """
    Main command processor for HARRY ON.
    Auto-handles token, sync, restore, and all project commands.
    """

    def __init__(self):
        self.token_manager = get_token_manager()
        self.engine = ResumeEngine()
        self.welcome_shown = False

    def process(self, user_input: str) -> str:
        """
        Process any user input that starts with "HARRY ON".

        Returns response string.
        """
        if not user_input.upper().startswith("HARRY ON"):
            return ""

        parts = user_input.strip().split()

        # === CASE 1: Just "HARRY ON" ===
        if len(parts) <= 2:
            return self._handle_welcome()

        command = parts[2].lower()
        args = parts[3:] if len(parts) > 3 else []

        # === CASE 2: Token commands ===
        if command == "token":
            return self._handle_token(args)

        # === CASE 3: Sync commands ===
        if command == "sync":
            return self._handle_sync()

        if command == "restore":
            return self._handle_restore()

        # === CASE 4: Save/Resume ===
        if command == "save":
            return self._handle_save(args)

        if command == "resume":
            return self._handle_resume(args)

        if command == "list":
            return self._handle_list()

        if command == "status":
            return self._handle_status(args)

        # === CASE 5: Setup ===
        if command == "setup":
            return self._handle_setup()

        if command == "backup":
            return self._handle_backup()

        # === DEFAULT: Unknown command ===
        return self._handle_help()

    def _handle_welcome(self) -> str:
        """Handle bare 'HARRY ON' command."""
        token_status = "✅ ACTIVE" if self.token_manager.is_configured() else "⚠️ NOT SET"

        # Check if local files exist
        base = Path("/mnt/agents/output/harry_on_v1_mva/")
        has_files = False
        file_count = 0
        if base.exists():
            file_count = sum(1 for _, _, files in os.walk(base) for f in files)
            has_files = file_count > 0

        welcome = f"""
🔥 HARRY ON V1 MVA UNLIMITED v2.0.0
=====================================

GitHub Sync: {token_status}
Local Files: {file_count} files

"""

        # Auto-restore prompt if token exists but no local files
        if self.token_manager.is_configured() and not has_files:
            welcome += """⚠️  Workspace is EMPTY but GitHub sync is configured!
    → Run 'HARRY ON restore' to download all projects

"""

        welcome += """Commands:
  HARRY ON token [token]     → Set GitHub token (one-time)
  HARRY ON sync              → Save all to GitHub
  HARRY ON restore           → Restore all from GitHub
  HARRY ON save [project]    → Save session + sync
  HARRY ON resume [project]  → Resume project
  HARRY ON list              → List all projects
  HARRY ON status            → Show system status
  HARRY ON setup             → Run setup wizard

"""

        return welcome

    def _handle_token(self, args: list) -> str:
        """Handle token command."""
        if not args:
            if self.token_manager.is_configured():
                token = self.token_manager.get_token()
                masked = "*" * (len(token) - 4) + token[-4:] if len(token) > 4 else "****"
                return f"✅ Token configured: {masked}\n   Repo: {self.token_manager.repo}"
            return "❌ No token set.\nUsage: HARRY ON token [your_github_token]"

        token = args[0]
        if set_universal_token(token):
            # Test connection
            if self.token_manager.test_connection():
                return "✅ Token saved and verified!\n✅ GitHub sync is now ACTIVE across ALL sessions!"
            return "⚠️ Token saved but connection test failed. Check token validity."
        return "❌ Failed to save token"

    def _handle_sync(self) -> str:
        """Handle sync to GitHub."""
        if not self.token_manager.is_configured():
            return "❌ No token configured!\nSet token: HARRY ON token [your_token]"

        try:
            from session_manager.auto_sync import AutoSyncEngine
            sync = AutoSyncEngine()
            result = sync.sync_all_projects()

            synced = result.get("total_synced", 0)
            failed = result.get("total_failed", 0)

            return f"✅ SYNC COMPLETE\n   Synced: {synced} files\n   Failed: {failed} files\n   Repo: https://github.com/{self.token_manager.repo}"
        except Exception as e:
            return f"❌ Sync failed: {str(e)}"

    def _handle_restore(self) -> str:
        """Handle restore from GitHub."""
        if not self.token_manager.is_configured():
            return "❌ No token configured!\nSet token: HARRY ON token [your_token]"

        try:
            from session_manager.download_all import ProjectRestore
            restorer = ProjectRestore()
            result = restorer.restore_all()

            downloaded = result.get("total_downloaded", 0)
            failed = result.get("total_failed", 0)

            return f"✅ RESTORE COMPLETE\n   Downloaded: {downloaded} files\n   Failed: {failed} files\n   Location: /mnt/agents/output/harry_on_v1_mva/"
        except Exception as e:
            return f"❌ Restore failed: {str(e)}"

    def _handle_save(self, args: list) -> str:
        """Handle save session."""
        project = args[0] if args else "default"
        context = " ".join(args[1:]) if len(args) > 1 else "Session saved"

        # Save checkpoint
        checkpoint = self.engine.save_session(project, context=context)

        # Auto-sync if token available
        sync_msg = ""
        if self.token_manager.is_configured():
            try:
                from session_manager.auto_sync import AutoSyncEngine
                sync = AutoSyncEngine()
                sync.sync_all_projects()
                sync_msg = "\n✅ Auto-synced to GitHub!"
            except:
                sync_msg = "\n⚠️ Auto-sync failed"

        return f"✅ Session saved: {project}{sync_msg}"

    def _handle_resume(self, args: list) -> str:
        """Handle resume project."""
        if not args:
            # Quick resume
            return self.engine.quick_resume()

        project_name = args[0]
        return self.engine.resume_project(project_name)

    def _handle_list(self) -> str:
        """Handle list projects."""
        sessions = self.engine.list_all_sessions()
        if not sessions:
            return "📋 No saved sessions found.\n   Save one: HARRY ON save [project_name]"

        result = "📋 SAVED SESSIONS:\n"
        for s in sessions:
            result += f"  • {s['name']} ({s['type']}) - {s['checkpoints']} checkpoints - {s['status']}\n"
        return result

    def _handle_status(self, args: list) -> str:
        """Handle status command."""
        token_status = "✅ ACTIVE" if self.token_manager.is_configured() else "⚠️ NOT SET"

        base = Path("/mnt/agents/output/harry_on_v1_mva/")
        file_count = 0
        if base.exists():
            file_count = sum(1 for _, _, files in os.walk(base) for f in files)

        sessions = self.engine.list_all_sessions()

        return f"""
🔥 HARRY ON SYSTEM STATUS
=========================

GitHub Sync:    {token_status}
Token:          {'*' * 20}{self.token_manager.get_token()[-4:] if self.token_manager.get_token() else 'N/A'}
Repo:           {self.token_manager.repo}
Branch:         {self.token_manager.branch}

Local Files:    {file_count} files
Saved Sessions: {len(sessions)} projects

Storage Paths:
  /mnt/agents/output/harry_on_v1_mva/
  GitHub: github.com/{self.token_manager.repo}
"""

    def _handle_setup(self) -> str:
        """Handle setup wizard."""
        from session_manager.github_setup import GitHubSetupWizard
        wizard = GitHubSetupWizard()
        wizard.run_wizard()
        return "✅ Setup complete!"

    def _handle_backup(self) -> str:
        """Handle force backup."""
        try:
            from session_manager.auto_backup import AutoBackup
            backup = AutoBackup()
            backup_id = backup.auto_backup_all()
            if backup_id:
                return f"✅ Backup created: {backup_id}"
            return "ℹ️ No changes to backup"
        except Exception as e:
            return f"❌ Backup failed: {e}"

    def _handle_help(self) -> str:
        """Show help."""
        return """
❓ Unknown command

Available commands:
  HARRY ON                    → Show welcome/status
  HARRY ON token [token]      → Set GitHub token
  HARRY ON sync               → Sync to GitHub
  HARRY ON restore            → Restore from GitHub
  HARRY ON save [project]     → Save session
  HARRY ON resume [project]   → Resume project
  HARRY ON resume             → Quick resume
  HARRY ON list               → List projects
  HARRY ON status             → System status
  HARRY ON setup              → Setup wizard
  HARRY ON backup             → Force backup
"""


# === MAIN ENTRY POINT ===
# This is what gets called when user types "HARRY ON"

_processor = None

def get_processor() -> HARRYONCommandProcessor:
    """Get or create global processor."""
    global _processor
    if _processor is None:
        _processor = HARRYONCommandProcessor()
    return _processor


def harry_on_command(user_input: str) -> str:
    """
    MAIN FUNCTION - Call this for ALL "HARRY ON" commands.

    Args:
        user_input: Full user input (e.g., "HARRY ON sync")

    Returns:
        Response string
    """
    processor = get_processor()
    return processor.process(user_input)


# For direct execution
if __name__ == "__main__":
    print("HARRY ON Command Processor v3.0.0")
    print("=" * 50)
    print("\nTesting: HARRY ON")
    print(harry_on_command("HARRY ON"))
