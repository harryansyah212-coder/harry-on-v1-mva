#!/usr/bin/env python3
"""
HARRY ON GitHub Setup Wizard v1.0.0
Interactive setup for permanent cross-session storage
Repository: github.com/harryansyah212-coder/harry-on-v1-mva
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path


class GitHubSetupWizard:
    """
    Step-by-step wizard to configure GitHub sync for HARRY ON.
    Run once, use forever.
    """

    CONFIG_FILE = "/mnt/agents/output/harry_on_v1_mva/session_manager/.github_config.json"

    def __init__(self):
        self.config = self._load_config()
        self.token = self.config.get("token", "")
        self.repo = self.config.get("repo", "harryansyah212-coder/harry-on-v1-mva")
        self.branch = self.config.get("branch", "main")

    def _load_config(self) -> dict:
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_config(self):
        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def run_wizard(self):
        """Run the full setup wizard."""
        print("=" * 70)
        print("🔥 HARRY ON GitHub Sync Setup Wizard v1.0.0")
        print("=" * 70)
        print()
        print("This wizard will configure permanent storage for all HARRY ON projects.")
        print("Your files will survive even if Kimi clears the workspace.")
        print()

        # Step 1: Check existing config
        if self.config.get("token"):
            print("✅ Existing config found!")
            print(f"   Repo: {self.repo}")
            print(f"   Branch: {self.branch}")
            test = input("Test connection? (y/n): ").lower()
            if test == "y":
                if self.test_connection():
                    print("\n🎉 GitHub sync is already configured and working!")
                    return True

        # Step 2: Get GitHub token
        print()
        print("STEP 1: GitHub Personal Access Token")
        print("-" * 50)
        print("""
1. Go to: https://github.com/settings/tokens
2. Click: "Generate new token (classic)"
3. Note: "HARRY ON Sync"
4. Expiration: "No expiration" (or choose duration)
5. Scopes: CHECK these boxes:
   ✅ repo (Full control of private repositories)
   ✅ read:org (if using organizations)
6. Click: "Generate token"
7. COPY the token immediately (you can't see it again!)
""")

        token = input("Paste your GitHub token here: ").strip()
        if not token:
            print("❌ No token provided. Setup cancelled.")
            return False

        self.token = token
        self.config["token"] = token

        # Step 3: Verify token
        print()
        print("STEP 2: Verifying token...")
        if not self.test_connection():
            print("❌ Token verification failed!")
            return False

        # Step 4: Repository setup
        print()
        print("STEP 3: Repository Configuration")
        print("-" * 50)

        repo_input = input(f"Repository name [{self.repo}]: ").strip()
        if repo_input:
            self.repo = repo_input
            self.config["repo"] = repo_input

        branch_input = input(f"Branch name [{self.branch}]: ").strip()
        if branch_input:
            self.branch = branch_input
            self.config["branch"] = branch_input

        # Step 5: Create repo if not exists
        print()
        print("STEP 4: Checking repository...")
        if not self.check_repo_exists():
            create = input("Repository not found. Create it? (y/n): ").lower()
            if create == "y":
                if not self.create_repo():
                    print("❌ Failed to create repository!")
                    return False
            else:
                print("❌ Setup cancelled.")
                return False

        # Step 6: Save config
        self._save_config()

        print()
        print("=" * 70)
        print("🎉 SETUP COMPLETE!")
        print("=" * 70)
        print(f"""
Configuration saved to: {self.CONFIG_FILE}

Your settings:
  Token: {'*' * 20}{self.token[-4:]}
  Repo: {self.repo}
  Branch: {self.branch}

All HARRY ON projects will now auto-sync to GitHub!
""")
        return True

    def test_connection(self) -> bool:
        """Test GitHub API connection."""
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HARRY-ON-Sync/1.0"
        }

        req = urllib.request.Request(
            "https://api.github.com/user",
            headers=headers
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                print(f"✅ Connected as: {data.get('login', 'unknown')}")
                print(f"   Rate limit remaining: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
                return True
        except urllib.error.HTTPError as e:
            print(f"❌ API Error: {e.code} - {e.reason}")
            return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def check_repo_exists(self) -> bool:
        """Check if repository exists."""
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        req = urllib.request.Request(
            f"https://api.github.com/repos/{self.repo}",
            headers=headers
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                print(f"✅ Repository found: {data.get('full_name')}")
                print(f"   Private: {data.get('private')}")
                print(f"   Default branch: {data.get('default_branch')}")
                return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"⚠️ Repository not found: {self.repo}")
                return False
            print(f"❌ Error: {e.code}")
            return False

    def create_repo(self) -> bool:
        """Create a new repository."""
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }

        repo_name = self.repo.split("/")[-1]
        data = {
            "name": repo_name,
            "description": "HARRY ON V1 MVA UNLIMITED v2.0.0 - Cross-Session Persistence",
            "private": False,
            "auto_init": True,
            "gitignore_template": "Python"
        }

        req = urllib.request.Request(
            "https://api.github.com/user/repos",
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                print(f"✅ Repository created: {data.get('html_url')}")
                return True
        except Exception as e:
            print(f"❌ Failed to create repository: {e}")
            return False


def quick_setup(token: str, repo: str = "harryansyah212-coder/harry-on-v1-mva"):
    """Quick setup with provided token."""
    wizard = GitHubSetupWizard()
    wizard.token = token
    wizard.repo = repo
    wizard.config["token"] = token
    wizard.config["repo"] = repo

    if wizard.test_connection():
        wizard._save_config()
        print("✅ GitHub sync configured!")
        return True
    return False


if __name__ == "__main__":
    wizard = GitHubSetupWizard()
    wizard.run_wizard()
