#!/usr/bin/env python3
"""
HARRY ON GitHub Sync Module v1.0.0
Syncs all project files to GitHub for permanent cross-session storage
Repository: github.com/harryansyah212-coder/harry-on-v1-mva
"""

import os
import json
import base64
import datetime
from pathlib import Path
from typing import Dict, List, Optional
import urllib.request
import urllib.error


class GitHubSync:
    """
    Syncs HARRY ON projects to GitHub repository.
    This ensures files survive even if /mnt/agents/output/ is cleared.
    """

    DEFAULT_REPO = "harryansyah212-coder/harry-on-v1-mva"
    DEFAULT_BRANCH = "main"

    def __init__(self, repo: str = None, token: str = None, 
                 branch: str = "main"):
        self.repo = repo or self.DEFAULT_REPO
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.branch = branch
        self.base_url = f"https://api.github.com/repos/{self.repo}"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HARRY-ON-Session-Manager/1.0"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def _api_request(self, endpoint: str, method: str = "GET", 
                     data: bytes = None) -> Dict:
        """Make GitHub API request."""
        url = f"{self.base_url}/{endpoint}"
        req = urllib.request.Request(url, method=method, headers=self.headers)
        if data:
            req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, data=data, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"error": str(e), "code": e.code}
        except Exception as e:
            return {"error": str(e)}

    def test_connection(self) -> bool:
        """Test if GitHub API is accessible."""
        if not self.token:
            print("⚠️ No GitHub token configured")
            return False

        result = self._api_request("")
        if "error" in result:
            print(f"❌ GitHub API error: {result['error']}")
            return False

        print(f"✅ Connected to GitHub repo: {result.get('full_name', self.repo)}")
        print(f"   Default branch: {result.get('default_branch', 'unknown')}")
        print(f"   Private: {result.get('private', 'unknown')}")
        return True

    def get_file(self, path: str) -> Optional[str]:
        """Get file content from GitHub."""
        endpoint = f"contents/{path}?ref={self.branch}"
        result = self._api_request(endpoint)

        if "error" in result:
            return None

        if "content" in result:
            return base64.b64decode(result["content"]).decode("utf-8")
        return None

    def upload_file(self, local_path: str, repo_path: str, 
                    message: str = None) -> bool:
        """
        Upload a file to GitHub repository.

        Args:
            local_path: Path to local file
            repo_path: Target path in repo (e.g., "modules/storycraft/hook_engine.py")
            message: Commit message
        """
        if not self.token:
            print("❌ No GitHub token. Set GITHUB_TOKEN environment variable.")
            return False

        local_file = Path(local_path)
        if not local_file.exists():
            print(f"❌ Local file not found: {local_path}")
            return False

        content = local_file.read_text(encoding="utf-8")
        content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        # Check if file already exists
        endpoint = f"contents/{repo_path}"
        existing = self._api_request(f"{endpoint}?ref={self.branch}")

        sha = None
        if "sha" in existing:
            sha = existing["sha"]

        # Prepare commit data
        commit_msg = message or f"Update {repo_path} via HARRY ON Session Manager"
        data = {
            "message": commit_msg,
            "content": content_b64,
            "branch": self.branch
        }
        if sha:
            data["sha"] = sha

        # Upload
        result = self._api_request(endpoint, method="PUT", 
                                   data=json.dumps(data).encode("utf-8"))

        if "error" in result:
            print(f"❌ Upload failed: {result['error']}")
            return False

        print(f"✅ Uploaded: {repo_path}")
        return True

    def sync_project(self, project_path: str, repo_prefix: str = "") -> Dict:
        """
        Sync an entire project directory to GitHub.

        Args:
            project_path: Local project directory
            repo_prefix: Prefix in repo (e.g., "modules/storycraft/")

        Returns:
            Sync report
        """
        project_dir = Path(project_path)
        if not project_dir.exists():
            return {"error": f"Directory not found: {project_path}"}

        report = {
            "project": project_dir.name,
            "files_synced": 0,
            "files_failed": 0,
            "errors": []
        }

        for file_path in project_dir.rglob("*"):
            if file_path.is_file():
                relative = file_path.relative_to(project_dir)
                repo_target = f"{repo_prefix}{relative}".replace(chr(92), "/")

                success = self.upload_file(
                    str(file_path), 
                    repo_target,
                    f"Sync {relative} from HARRY ON"
                )

                if success:
                    report["files_synced"] += 1
                else:
                    report["files_failed"] += 1
                    report["errors"].append(str(relative))

        return report

    def download_project(self, repo_path: str, local_path: str) -> bool:
        """
        Download a project from GitHub to local workspace.
        Used when resuming work in a new session.

        Args:
            repo_path: Path in GitHub repo (e.g., "modules/storycraft/")
            local_path: Local destination
        """
        # Get directory listing
        endpoint = f"contents/{repo_path}?ref={self.branch}"
        result = self._api_request(endpoint)

        if "error" in result:
            print(f"❌ Failed to list repo contents: {result['error']}")
            return False

        local_dir = Path(local_path)
        local_dir.mkdir(parents=True, exist_ok=True)

        for item in result:
            if item["type"] == "file":
                content = self.get_file(item["path"])
                if content:
                    local_file = local_dir / item["name"]
                    local_file.write_text(content, encoding="utf-8")
                    print(f"✅ Downloaded: {item['path']}")
            elif item["type"] == "dir":
                sub_local = local_dir / item["name"]
                self.download_project(item["path"], str(sub_local))

        return True

    def generate_sync_script(self, project_paths: List[str]) -> str:
        """
        Generate a standalone sync script for manual GitHub push.
        Useful when API token is not available.
        """
        script = f"""#!/bin/bash
# HARRY ON GitHub Sync Script
# Generated: {datetime.datetime.now().isoformat()}
# Repo: {self.repo}
# Branch: {self.branch}

echo "🔥 HARRY ON GitHub Sync"
echo "========================"

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install git."
    exit 1
fi

# Clone or pull repo
REPO_DIR="harry-on-v1-mva-temp"
if [ -d "$REPO_DIR" ]; then
    cd "$REPO_DIR"
    git pull origin {self.branch}
else
    git clone https://github.com/{self.repo}.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Copy project files
"""

        for path in project_paths:
            project_name = Path(path).name
            script += f"""
echo "📦 Syncing: {project_name}"
mkdir -p "{project_name}"
cp -r "{path}"/* "{project_name}/" 2>/dev/null || echo "⚠️ No files in {path}"
"""

        script += f"""
# Commit and push
git add .
git commit -m "HARRY ON auto-sync: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
git push origin {self.branch}

echo "✅ Sync complete!"
"""

        return script


def setup_github_token():
    """Interactive setup for GitHub token."""
    print("🔑 GitHub Token Setup")
    print("=" * 50)
    print("""
To enable permanent cross-session storage:

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: repo (full control)
4. Generate and copy the token
5. Set as environment variable:
   export GITHUB_TOKEN="your_token_here"

Or provide it when initializing GitHubSync:
   sync = GitHubSync(token="your_token")
""")


if __name__ == "__main__":
    print("HARRY ON GitHub Sync Module v1.0.0")
    print("=" * 50)

    sync = GitHubSync()
    if sync.test_connection():
        print("\n✅ GitHub sync is ready!")
    else:
        setup_github_token()
