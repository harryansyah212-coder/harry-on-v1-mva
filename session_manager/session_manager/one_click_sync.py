#!/usr/bin/env python3
"""
HARRY ON One-Click Sync v1.0.0
The EASIEST way to sync projects.

Usage:
    python one_click_sync.py save    → Save & sync all projects to GitHub
    python one_click_sync.py restore → Restore all projects from GitHub
    python one_click_sync.py status   → Check sync status
"""

import sys
import os

# Add to path
sys.path.insert(0, "/mnt/agents/output/harry_on_v1_mva/")

from session_manager.auto_sync import AutoSyncEngine, sync_now
from session_manager.download_all import ProjectRestore, restore_now
from session_manager.github_setup import GitHubSetupWizard


def save_all():
    """Save all projects to GitHub."""
    print("🔥 HARRY ON: Saving all projects to GitHub...")
    print("=" * 60)
    result = sync_now()

    if "error" in result:
        print(f"\n❌ Sync failed: {result['error']}")
        print("\n💡 Run setup first:")
        print("   python session_manager/github_setup.py")
        return False

    print(f"\n✅ All projects saved!")
    print(f"   Total synced: {result.get('total_synced', 0)} files")
    print(f"   Repo: https://github.com/harryansyah212-coder/harry-on-v1-mva")
    return True


def restore_all():
    """Restore all projects from GitHub."""
    print("🔥 HARRY ON: Restoring all projects from GitHub...")
    print("=" * 60)
    result = restore_now()

    if "error" in result:
        print(f"\n❌ Restore failed: {result['error']}")
        print("\n💡 Run setup first:")
        print("   python session_manager/github_setup.py")
        return False

    print(f"\n✅ All projects restored!")
    print(f"   Total downloaded: {result.get('total_downloaded', 0)} files")
    return True


def show_status():
    """Show current sync status."""
    print("🔥 HARRY ON: Sync Status")
    print("=" * 60)

    config_file = "/mnt/agents/output/harry_on_v1_mva/session_manager/.github_config.json"

    if not os.path.exists(config_file):
        print("❌ Not configured")
        print("   Run: python session_manager/github_setup.py")
        return

    import json
    with open(config_file, "r") as f:
        config = json.load(f)

    print(f"✅ Configured")
    print(f"   Repo: {config.get('repo', 'N/A')}")
    print(f"   Branch: {config.get('branch', 'N/A')}")
    print(f"   Token: {'*' * 20}{config.get('token', '')[-4:]}")

    # Check local files
    base = "/mnt/agents/output/harry_on_v1_mva/"
    if os.path.exists(base):
        total_files = sum(1 for _, _, files in os.walk(base) for f in files)
        print(f"\n   Local files: {total_files}")

    print(f"\n💡 Commands:")
    print(f"   Save:   python one_click_sync.py save")
    print(f"   Restore: python one_click_sync.py restore")


def main():
    if len(sys.argv) < 2:
        print("""
🔥 HARRY ON One-Click Sync v1.0.0

Usage:
  python one_click_sync.py save     → Save all to GitHub
  python one_click_sync.py restore  → Restore all from GitHub
  python one_click_sync.py status   → Check status
  python one_click_sync.py setup    → Configure GitHub

Examples:
  # Before ending chat:
  python one_click_sync.py save

  # In new chat:
  python one_click_sync.py restore
""")
        return

    command = sys.argv[1].lower()

    if command == "save":
        save_all()
    elif command == "restore":
        restore_all()
    elif command == "status":
        show_status()
    elif command == "setup":
        wizard = GitHubSetupWizard()
        wizard.run_wizard()
    else:
        print(f"❌ Unknown command: {command}")
        print("Use: save, restore, status, or setup")


if __name__ == "__main__":
    main()
