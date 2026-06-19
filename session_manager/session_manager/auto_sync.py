#!/usr/bin/env python3
"""
HARRY ON Auto-Sync Engine v1.0.0
Automatically syncs all project files to GitHub after creation/editing.
Run this after completing any project to ensure files survive sessions.
"""

import os
import json
import base64
import datetime
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Set


class AutoSyncEngine:
    """
    Automatic file sync to GitHub.

    Usage:
        from auto_sync import AutoSyncEngine
        sync = AutoSyncEngine()
        sync.sync_all_projects()  # Sync everything
        sync.sync_project("modules/storycraft/")  # Sync specific project
    """

    def __init__(self):
        self.config_file = "/mnt/agents/output/harry_on_v1_mva/session_manager/.github_config.json"
        self.config = self._load_config()
        self.token = self.config.get("token", "")
        self.repo = self.config.get("repo", "harryansyah212-coder/harry-on-v1-mva")
        self.branch = self.config.get("branch", "main")
        self.base_path = Path("/mnt/agents/output/harry_on_v1_mva/")

        # Track synced files to avoid duplicates
        self.sync_index_file = self.base_path / "session_manager" / ".sync_index.json"
        self.sync_index = self._load_sync_index()

    def _load_config(self) -> dict:
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _load_sync_index(self) -> dict:
        if self.sync_index_file.exists():
            with open(self.sync_index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"synced_files": {}, "last_sync": None}

    def _save_sync_index(self):
        with open(self.sync_index_file, "w", encoding="utf-8") as f:
            json.dump(self.sync_index, f, indent=2, ensure_ascii=False)

    def _api_request(self, endpoint: str, method: str = "GET", 
                     data: bytes = None) -> Dict:
        """Make GitHub API request."""
        url = f"https://api.github.com/repos/{self.repo}/{endpoint}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HARRY-ON-AutoSync/1.0"
        }
        if data:
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, method=method, headers=headers)

        try:
            with urllib.request.urlopen(req, data=data, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if hasattr(e, 'read') else ""
            return {"error": str(e), "code": e.code, "body": error_body}
        except Exception as e:
            return {"error": str(e)}

    def _get_file_sha(self, path: str) -> Optional[str]:
        """Get SHA of existing file for updates."""
        result = self._api_request(f"contents/{path}?ref={self.branch}")
        if "sha" in result:
            return result["sha"]
        return None

    def upload_file(self, local_path: Path, repo_path: str, 
                    message: str = None) -> bool:
        """
        Upload a single file to GitHub.

        Args:
            local_path: Path to local file
            repo_path: Target path in repo (e.g., "modules/storycraft/hook_engine.py")
            message: Commit message
        """
        if not self.token:
            print(f"⚠️ No token configured. Skipping: {repo_path}")
            return False

        if not local_path.exists():
            print(f"❌ Local file not found: {local_path}")
            return False

        # Read and encode file
        try:
            content = local_path.read_bytes()
            content_b64 = base64.b64encode(content).decode("utf-8")
        except Exception as e:
            print(f"❌ Failed to read file: {e}")
            return False

        # Get existing SHA (for updates)
        sha = self._get_file_sha(repo_path)

        # Prepare commit data
        commit_msg = message or f"Sync {repo_path} via HARRY ON Auto-Sync"
        data = {
            "message": commit_msg,
            "content": content_b64,
            "branch": self.branch
        }
        if sha:
            data["sha"] = sha

        # Upload
        result = self._api_request(
            f"contents/{repo_path}",
            method="PUT",
            data=json.dumps(data).encode("utf-8")
        )

        if "error" in result:
            print(f"❌ Failed to upload {repo_path}: {result['error']}")
            return False

        # Update sync index
        self.sync_index["synced_files"][str(repo_path)] = {
            "local_path": str(local_path),
            "last_sync": datetime.datetime.now().isoformat(),
            "commit": result.get("commit", {}).get("sha", "unknown")[:8]
        }

        print(f"✅ Uploaded: {repo_path}")
        return True

    def sync_project(self, project_path: str, 
                     repo_prefix: str = "",
                     exclude_patterns: List[str] = None) -> Dict:
        """
        Sync an entire project directory to GitHub.

        Args:
            project_path: Local project directory (relative to base_path or absolute)
            repo_prefix: Prefix in repo (e.g., "modules/storycraft/")
            exclude_patterns: File patterns to exclude (e.g., ["*.pyc", "__pycache__"])

        Returns:
            Sync report
        """
        exclude = exclude_patterns or ["*.pyc", "__pycache__", ".git", ".env", 
                                         ".tmp", ".sync_index.json", ".github_config.json"]

        # Resolve path
        project_dir = Path(project_path)
        if not project_dir.is_absolute():
            project_dir = self.base_path / project_path

        if not project_dir.exists():
            return {"error": f"Directory not found: {project_dir}"}

        report = {
            "project": project_dir.name,
            "files_synced": 0,
            "files_failed": 0,
            "files_skipped": 0,
            "errors": []
        }

        for file_path in project_dir.rglob("*"):
            if not file_path.is_file():
                continue

            # Check exclusions
            skip = False
            for pattern in exclude:
                if pattern in str(file_path):
                    skip = True
                    break
            if skip:
                report["files_skipped"] += 1
                continue

            # Calculate relative path
            try:
                relative = file_path.relative_to(self.base_path)
            except ValueError:
                relative = file_path.relative_to(project_dir)

            repo_target = f"{repo_prefix}{relative}".replace(chr(92), "/")

            # Upload
            success = self.upload_file(
                file_path,
                repo_target,
                f"Auto-sync: {relative}"
            )

            if success:
                report["files_synced"] += 1
            else:
                report["files_failed"] += 1
                report["errors"].append(str(relative))

        self.sync_index["last_sync"] = datetime.datetime.now().isoformat()
        self._save_sync_index()

        return report

    def sync_all_projects(self) -> Dict:
        """Sync ALL projects in /mnt/agents/output/harry_on_v1_mva/."""
        print("🔥 HARRY ON Auto-Sync: Syncing ALL projects")
        print("=" * 60)

        if not self.token:
            print("❌ No GitHub token configured!")
            print("   Run: python github_setup.py")
            return {"error": "No token"}

        total_report = {
            "projects": [],
            "total_synced": 0,
            "total_failed": 0,
            "timestamp": datetime.datetime.now().isoformat()
        }

        # Sync session_manager first
        print("\n📦 Syncing: session_manager/")
        sm_report = self.sync_project("session_manager/", "session_manager/")
        total_report["projects"].append({"name": "session_manager", **sm_report})
        total_report["total_synced"] += sm_report.get("files_synced", 0)
        total_report["total_failed"] += sm_report.get("files_failed", 0)

        # Find all other project directories
        for item in sorted(self.base_path.iterdir()):
            if item.is_dir() and item.name not in ["session_manager"]:
                print(f"\n📦 Syncing: {item.name}/")
                report = self.sync_project(str(item), f"{item.name}/")
                total_report["projects"].append({"name": item.name, **report})
                total_report["total_synced"] += report.get("files_synced", 0)
                total_report["total_failed"] += report.get("files_failed", 0)

        print()
        print("=" * 60)
        print(f"✅ SYNC COMPLETE")
        print(f"   Total synced: {total_report['total_synced']} files")
        print(f"   Total failed: {total_report['total_failed']} files")
        print(f"   Timestamp: {total_report['timestamp']}")
        print("=" * 60)

        return total_report

    def generate_sync_script(self) -> str:
        """Generate a standalone bash script for manual sync."""
        script = f"""#!/bin/bash
# HARRY ON GitHub Sync Script
# Generated: {datetime.datetime.now().isoformat()}
# Repo: {self.repo}
# Branch: {self.branch}

set -e

echo "🔥 HARRY ON GitHub Sync"
echo "======================="

# Check git
if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Install git first."
    exit 1
fi

# Check token
if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️ GITHUB_TOKEN not set"
    echo "   export GITHUB_TOKEN='your_token_here'"
    exit 1
fi

REPO_DIR="harry-on-sync-temp"
REPO_URL="https://$GITHUB_TOKEN@github.com/{self.repo}.git"

# Clone or update
if [ -d "$REPO_DIR" ]; then
    echo "📥 Pulling latest changes..."
    cd "$REPO_DIR"
    git pull origin {self.branch}
    cd ..
else
    echo "📥 Cloning repository..."
    git clone "$REPO_URL" "$REPO_DIR"
fi

# Copy all projects
echo "📦 Copying projects..."
SOURCE_DIR="/mnt/agents/output/harry_on_v1_mva/"

# Sync session_manager
if [ -d "$SOURCE_DIR/session_manager" ]; then
    echo "  → session_manager/"
    mkdir -p "$REPO_DIR/session_manager"
    cp -r "$SOURCE_DIR/session_manager/"* "$REPO_DIR/session_manager/" 2>/dev/null || true
fi

# Sync all other projects
for dir in "$SOURCE_DIR"/*/; do
    dirname=$(basename "$dir")
    if [ "$dirname" != "session_manager" ]; then
        echo "  → $dirname/"
        mkdir -p "$REPO_DIR/$dirname"
        cp -r "$dir"* "$REPO_DIR/$dirname/" 2>/dev/null || true
    fi
done

# Commit and push
cd "$REPO_DIR"
git add -A
git commit -m "HARRY ON auto-sync: $(date '+%Y-%m-%d %H:%M:%S')" || echo "Nothing to commit"
git push origin {self.branch}

echo ""
echo "✅ Sync complete!"
echo "   Repo: https://github.com/{self.repo}"
"""

        script_path = self.base_path / "session_manager" / "sync_to_github.sh"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)

        # Make executable
        os.chmod(script_path, 0o755)

        print(f"✅ Sync script generated: {script_path}")
        return str(script_path)


# Convenience function for one-line sync
def sync_now():
    """Quick sync all projects."""
    engine = AutoSyncEngine()
    return engine.sync_all_projects()


if __name__ == "__main__":
    print("HARRY ON Auto-Sync Engine v1.0.0")
    print("=" * 50)

    engine = AutoSyncEngine()
    if not engine.token:
        print("❌ Not configured. Run github_setup.py first.")
    else:
        engine.sync_all_projects()
