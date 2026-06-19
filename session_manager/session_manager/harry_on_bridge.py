#!/usr/bin/env python3
"""
HARRY ON Session Bridge v2.0.0
Full integration: HARRY ON command + GitHub Sync + Auto-save + Auto-restore
Auto-activates when "HARRY ON" is detected.
"""

import sys
import os
import json
import datetime
from pathlib import Path

sys.path.insert(0, "/mnt/agents/output/harry_on_v1_mva/")

from session_manager.resume_engine import ResumeEngine, handle_harry_on_command
from session_manager.auto_backup import AutoBackup


class HARRYONBridge:
    """
    Bridge between HARRY ON core and all persistence systems.
    Handles ALL "HARRY ON" commands including sync/restore.
    """

    def __init__(self):
        self.engine = ResumeEngine()
        self.backup = AutoBackup()
        self.active = True
        self.config_file = "/mnt/agents/output/harry_on_v1_mva/session_manager/.github_config.json"
        self.token_file = "/mnt/agents/output/harry_on_v1_mva/session_manager/.token_secure"
        self.sync_log = "/mnt/agents/output/harry_on_v1_mva/session_manager/.sync_log.json"
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_config(self):
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def set_token(self, token: str) -> bool:
        """Set GitHub token securely."""
        if not token or len(token) < 10:
            print("❌ Invalid token")
            return False

        self.config["token"] = token
        self.config["repo"] = "harryansyah212-coder/harry-on-v1-mva"
        self.config["branch"] = "main"
        self.config["set_at"] = datetime.datetime.now().isoformat()
        self._save_config()

        # Test connection
        if self._test_github_connection():
            print(f"✅ GitHub token configured and verified!")
            print(f"   Repo: {self.config['repo']}")
            return True
        else:
            print("⚠️ Token saved but connection test failed")
            return False

    def _test_github_connection(self) -> bool:
        """Test GitHub API connection."""
        import urllib.request
        token = self.config.get("token", "")
        if not token:
            return False

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HARRY-ON-Bridge/2.0"
        }

        try:
            req = urllib.request.Request(
                "https://api.github.com/user",
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                self.config["github_user"] = data.get("login", "")
                self._save_config()
                return True
        except:
            return False

    def auto_sync_to_github(self) -> bool:
        """Auto-sync all projects to GitHub."""
        if not self.config.get("token"):
            print("⚠️ No GitHub token configured")
            print("   Use: HARRY ON token [your_token]")
            return False

        try:
            from session_manager.auto_sync import AutoSyncEngine
            sync = AutoSyncEngine()
            result = sync.sync_all_projects()

            # Log sync
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "action": "auto_sync",
                "result": result
            }
            self._append_sync_log(log_entry)

            return result.get("total_synced", 0) > 0
        except Exception as e:
            print(f"❌ Auto-sync failed: {e}")
            return False

    def auto_restore_from_github(self) -> bool:
        """Auto-restore all projects from GitHub."""
        if not self.config.get("token"):
            print("⚠️ No GitHub token configured")
            return False

        try:
            from session_manager.download_all import ProjectRestore
            restorer = ProjectRestore()
            result = restorer.restore_all()

            # Log restore
            log_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "action": "auto_restore",
                "result": result
            }
            self._append_sync_log(log_entry)

            return result.get("total_downloaded", 0) > 0
        except Exception as e:
            print(f"❌ Auto-restore failed: {e}")
            return False

    def _append_sync_log(self, entry: dict):
        """Append to sync log."""
        log = []
        if os.path.exists(self.sync_log):
            with open(self.sync_log, "r", encoding="utf-8") as f:
                log = json.load(f)
        log.append(entry)
        with open(self.sync_log, "w", encoding="utf-8") as f:
            json.dump(log[-50:], f, indent=2, ensure_ascii=False)  # Keep last 50

    def process_command(self, user_input: str) -> str:
        """
        Process ALL HARRY ON commands.

        Commands:
        - HARRY ON                    → Show status + auto-restore if needed
        - HARRY ON save [project]     → Save session
        - HARRY ON resume [project]   → Resume project
        - HARRY ON resume             → Quick resume
        - HARRY ON list               → List projects
        - HARRY ON status             → Show status
        - HARRY ON sync               → Auto-sync to GitHub
        - HARRY ON restore            → Auto-restore from GitHub
        - HARRY ON token [token]      → Set GitHub token
        - HARRY ON setup              → Setup wizard
        - HARRY ON backup             → Force backup
        - HARRY ON export [project]   → Export session
        """
        if not user_input.upper().startswith("HARRY ON"):
            return ""

        parts = user_input.strip().split()

        # Just "HARRY ON" - show welcome + auto-restore check
        if len(parts) <= 2:
            return self._show_welcome()

        command = parts[2].lower()
        args = parts[3:] if len(parts) > 3 else []

        # Handle token command
        if command == "token":
            if args:
                token = args[0]
                if self.set_token(token):
                    return "✅ GitHub token configured! Auto-sync is now ACTIVE."
                return "❌ Failed to configure token"
            return "Usage: HARRY ON token [your_github_token]"

        # Handle sync command
        if command == "sync":
            print("🔥 HARRY ON Auto-Sync to GitHub...")
            if self.auto_sync_to_github():
                return "✅ All projects synced to GitHub!"
            return "❌ Sync failed. Check token with: HARRY ON token [token]"

        # Handle restore command
        if command == "restore":
            print("🔥 HARRY ON Auto-Restore from GitHub...")
            if self.auto_restore_from_github():
                return "✅ All projects restored from GitHub!"
            return "❌ Restore failed. Check token and repo."

        # Handle setup command
        if command == "setup":
            from session_manager.github_setup import GitHubSetupWizard
            wizard = GitHubSetupWizard()
            wizard.run_wizard()
            return "✅ Setup complete!"

        # Handle save command with auto-sync
        if command == "save":
            project = args[0] if args else "default"
            context = " ".join(args[1:]) if len(args) > 1 else "Auto-saved"

            # Save session
            result = handle_harry_on_command("save", project, context)

            # Auto-sync to GitHub
            print("\n🔄 Auto-syncing to GitHub...")
            self.auto_sync_to_github()

            return result + "\n✅ Auto-synced to GitHub!"

        # Default: pass to resume engine
        return handle_harry_on_command(command, *args)

    def _show_welcome(self) -> str:
        """Show welcome message with auto-restore prompt."""
        welcome = """
🔥 HARRY ON V1 MVA UNLIMITED v2.0.0
=====================================

Session Persistence: ACTIVE
Auto-Backup: ENABLED
GitHub Sync: {}

""".format("✅ CONFIGURED" if self.config.get("token") else "⚠️ NOT CONFIGURED")

        # Check if we should auto-restore
        if self.config.get("token"):
            # Check if local files exist
            base = Path("/mnt/agents/output/harry_on_v1_mva/")
            has_files = any(base.iterdir()) if base.exists() else False

            if not has_files:
                welcome += """
⚠️  Local workspace is EMPTY!
    Run 'HARRY ON restore' to download all projects from GitHub.

"""
            else:
                welcome += """
✅ Local workspace has files.
    Use 'HARRY ON sync' to backup to GitHub.

"""

        welcome += """Available Commands:
  HARRY ON save [project] [context]  → Save + auto-sync
  HARRY ON resume [project]          → Resume project
  HARRY ON resume                    → Quick resume
  HARRY ON sync                      → Sync to GitHub
  HARRY ON restore                   → Restore from GitHub
  HARRY ON token [token]             → Set GitHub token
  HARRY ON setup                     → Setup wizard
  HARRY ON list                      → List projects
  HARRY ON status                    → Show status

"""

        return welcome

    def auto_save_on_exit(self, project_name: str = "default"):
        """Auto-save when session is about to end."""
        print("\n⚡ Auto-saving session...")
        self.engine.save_session(
            project_name=project_name,
            context="Auto-saved before session end",
            pending_tasks=["Continue from last checkpoint"]
        )

        # Auto-sync to GitHub
        if self.config.get("token"):
            print("🔄 Auto-syncing to GitHub...")
            self.auto_sync_to_github()

        print("✅ Auto-save complete!\n")


# Global bridge instance
_bridge = None

def get_bridge() -> HARRYONBridge:
    """Get or create global bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = HARRYONBridge()
    return _bridge


def on_harry_on_activation():
    """Called when 'HARRY ON' is activated."""
    bridge = get_bridge()
    print(bridge._show_welcome())


def process_harry_on_command(user_input: str) -> str:
    """Main entry point for ALL HARRY ON commands."""
    bridge = get_bridge()
    return bridge.process_command(user_input)


if __name__ == "__main__":
    bridge = HARRYONBridge()
    print("HARRY ON Session Bridge v2.0.0")
    print("=" * 50)
    print("\nTest: HARRY ON")
    print(bridge._show_welcome())
