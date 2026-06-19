#!/usr/bin/env python3
"""
HARRY ON Project Restore v1.0.0
Downloads all project files from GitHub to local workspace.
Use this when starting a NEW chat session to restore all projects.

Usage:
    python download_all.py

Or in chat:
    HARRY ON restore
"""

import os
import json
import base64
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional


class ProjectRestore:
    """
    Restores all HARRY ON projects from GitHub to local workspace.
    Run this at the start of every new chat session.
    """

    def __init__(self):
        self.config_file = "/mnt/agents/output/harry_on_v1_mva/session_manager/.github_config.json"
        self.config = self._load_config()
        self.token = self.config.get("token", "")
        self.repo = self.config.get("repo", "harryansyah212-coder/harry-on-v1-mva")
        self.branch = self.config.get("branch", "main")
        self.base_path = Path("/mnt/agents/output/harry_on_v1_mva/")

    def _load_config(self) -> dict:
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _api_request(self, endpoint: str) -> Dict:
        """Make GitHub API request."""
        url = f"https://api.github.com/repos/{self.repo}/{endpoint}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HARRY-ON-Restore/1.0"
        }

        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"error": str(e), "code": e.code}
        except Exception as e:
            return {"error": str(e)}

    def list_repo_contents(self, path: str = "") -> List[Dict]:
        """List contents of a directory in the repo."""
        endpoint = f"contents/{path}?ref={self.branch}" if path else f"contents?ref={self.branch}"
        result = self._api_request(endpoint)

        if "error" in result:
            print(f"❌ Failed to list {path}: {result['error']}")
            return []

        if isinstance(result, list):
            return result
        return [result]

    def download_file(self, repo_path: str, local_path: Path) -> bool:
        """Download a single file from GitHub."""
        result = self._api_request(f"contents/{repo_path}?ref={self.branch}")

        if "error" in result:
            print(f"❌ Failed to get {repo_path}: {result['error']}")
            return False

        if "content" not in result:
            print(f"⚠️ No content for {repo_path}")
            return False

        try:
            content = base64.b64decode(result["content"])
            local_path.parent.mkdir(parents=True, exist_ok=True)
            local_path.write_bytes(content)
            print(f"✅ Downloaded: {repo_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to write {local_path}: {e}")
            return False

    def download_directory(self, repo_path: str, local_path: Path) -> Dict:
        """
        Recursively download a directory from GitHub.

        Args:
            repo_path: Path in repo (e.g., "modules/storycraft/")
            local_path: Local destination

        Returns:
            Download report
        """
        report = {
            "downloaded": 0,
            "failed": 0,
            "skipped": 0
        }

        items = self.list_repo_contents(repo_path)

        for item in items:
            if item.get("type") == "file":
                target = local_path / item["name"]
                if self.download_file(item["path"], target):
                    report["downloaded"] += 1
                else:
                    report["failed"] += 1

            elif item.get("type") == "dir":
                sub_local = local_path / item["name"]
                sub_report = self.download_directory(item["path"], sub_local)
                report["downloaded"] += sub_report["downloaded"]
                report["failed"] += sub_report["failed"]

        return report

    def restore_all(self) -> Dict:
        """
        Restore ALL projects from GitHub to local workspace.
        This is the main function to call at the start of a new session.
        """
        print("=" * 70)
        print("🔥 HARRY ON Project Restore v1.0.0")
        print("=" * 70)
        print()

        if not self.token:
            print("❌ No GitHub token configured!")
            print("   Run: python github_setup.py")
            return {"error": "No token"}

        print(f"📥 Restoring from: github.com/{self.repo}")
        print(f"   Branch: {self.branch}")
        print()

        # Create base directory
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Get root contents
        root_items = self.list_repo_contents("")

        total_report = {
            "projects": [],
            "total_downloaded": 0,
            "total_failed": 0
        }

        for item in root_items:
            if item.get("type") == "dir":
                project_name = item["name"]
                print(f"\n📦 Restoring: {project_name}/")

                local_dir = self.base_path / project_name
                report = self.download_directory(item["path"], local_dir)

                total_report["projects"].append({
                    "name": project_name,
                    **report
                })
                total_report["total_downloaded"] += report["downloaded"]
                total_report["total_failed"] += report["failed"]

                print(f"   Downloaded: {report['downloaded']} | Failed: {report['failed']}")

        print()
        print("=" * 70)
        print("✅ RESTORE COMPLETE")
        print("=" * 70)
        print(f"   Total files downloaded: {total_report['total_downloaded']}")
        print(f"   Total failed: {total_report['total_failed']}")
        print()
        print("💡 Next steps:")
        print("   1. Run: python session_manager/resume_engine.py")
        print("   2. Or: HARRY ON resume [project_name]")
        print("   3. Or: HARRY ON list")

        return total_report

    def restore_project(self, project_name: str) -> Dict:
        """
        Restore a specific project.

        Args:
            project_name: Name of project directory in repo (e.g., "modules", "ai_story_generator")
        """
        print(f"📥 Restoring project: {project_name}")

        local_dir = self.base_path / project_name
        report = self.download_directory(project_name, local_dir)

        print(f"✅ Done: {report['downloaded']} files downloaded")
        return report

    def generate_restore_script(self) -> str:
        """Generate a standalone restore script for manual use."""
        script = f"""#!/bin/bash
# HARRY ON Project Restore Script
# Generated: {__import__('datetime').datetime.now().isoformat()}
# Repo: {self.repo}
# Branch: {self.branch}

set -e

echo "🔥 HARRY ON Project Restore"
echo "============================"

# Check token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN not set"
    echo "   export GITHUB_TOKEN='your_token_here'"
    exit 1
fi

REPO="{self.repo}"
BRANCH="{self.branch}"
DEST="/mnt/agents/output/harry_on_v1_mva/"

echo "📥 Downloading from: $REPO"
echo "   Branch: $BRANCH"
echo ""

# Create destination
mkdir -p "$DEST"

# Use GitHub API to list and download files
# This requires jq: apt-get install jq

echo "💡 For full restore, use Python script instead:"
echo "   python session_manager/download_all.py"
echo ""
echo "Or clone with git:"
echo "   git clone https://$GITHUB_TOKEN@github.com/$REPO.git $DEST"
"""

        script_path = self.base_path / "session_manager" / "restore_from_github.sh"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)

        os.chmod(script_path, 0o755)
        return str(script_path)


# Quick restore function
def restore_now():
    """Quick restore all projects."""
    restorer = ProjectRestore()
    return restorer.restore_all()


if __name__ == "__main__":
    print("HARRY ON Project Restore v1.0.0")
    print("=" * 50)

    restorer = ProjectRestore()
    if not restorer.token:
        print("❌ Not configured. Run github_setup.py first.")
    else:
        restorer.restore_all()
