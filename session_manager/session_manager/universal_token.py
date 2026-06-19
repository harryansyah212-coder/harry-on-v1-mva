#!/usr/bin/env python3
"""
HARRY ON Universal Token Manager v1.0.0
Manages GitHub token across ALL sessions - old, new, and future.

Strategy:
1. Store token in multiple locations for redundancy
2. Auto-detect token from any source
3. Encrypt token for security
"""

import os
import json
import base64
import datetime
from pathlib import Path
from typing import Optional, Dict


class UniversalTokenManager:
    """
    Manages GitHub token with multiple fallback sources.
    Ensures token is available in ANY session.
    """

    # Multiple storage locations for redundancy
    STORAGE_PATHS = [
        "/mnt/agents/output/harry_on_v1_mva/session_manager/.github_config.json",
        "/mnt/agents/output/harry_on_v1_mva/session_manager/.token_backup",
        "/mnt/agents/.store/harry_on_token.json",
        "/mnt/agents/.tmp/harry_on_token.txt",
    ]

    def __init__(self):
        self.token = None
        self.repo = "harryansyah212-coder/harry-on-v1-mva"
        self.branch = "main"
        self._load_token()

    def _encode(self, text: str) -> str:
        """Simple encoding (not encryption, just obfuscation)."""
        return base64.b64encode(text.encode()).decode()

    def _decode(self, text: str) -> str:
        """Decode token."""
        return base64.b64decode(text.encode()).decode()

    def _load_token(self):
        """Try to load token from any available source."""
        for path in self.STORAGE_PATHS:
            if os.path.exists(path):
                try:
                    # Try JSON format
                    if path.endswith(".json"):
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if "token" in data:
                                self.token = data["token"]
                                self.repo = data.get("repo", self.repo)
                                self.branch = data.get("branch", self.branch)
                                return
                            elif "encoded_token" in data:
                                self.token = self._decode(data["encoded_token"])
                                self.repo = data.get("repo", self.repo)
                                self.branch = data.get("branch", self.branch)
                                return

                    # Try plain text
                    else:
                        with open(path, "r", encoding="utf-8") as f:
                            content = f.read().strip()
                            if content.startswith("ghp_") or content.startswith("github_pat_"):
                                self.token = content
                                return
                            # Try encoded
                            try:
                                self.token = self._decode(content)
                                return
                            except:
                                pass
                except:
                    continue

    def save_token(self, token: str, repo: str = None, branch: str = None) -> bool:
        """
        Save token to ALL storage locations for maximum redundancy.

        Args:
            token: GitHub personal access token
            repo: Repository name (default: harryansyah212-coder/harry-on-v1-mva)
            branch: Branch name (default: main)

        Returns:
            True if saved to at least one location
        """
        self.token = token
        if repo:
            self.repo = repo
        if branch:
            self.branch = branch

        saved_count = 0

        # Save to all locations
        for path in self.STORAGE_PATHS:
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)

                if path.endswith(".json"):
                    data = {
                        "token": token,
                        "repo": self.repo,
                        "branch": self.branch,
                        "updated_at": datetime.datetime.now().isoformat(),
                        "encoded_token": self._encode(token)
                    }
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)

                else:
                    # Save encoded version
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(self._encode(token))

                saved_count += 1
            except Exception as e:
                print(f"⚠️ Could not save to {path}: {e}")

        # Also save to session manager config
        config_path = "/mnt/agents/output/harry_on_v1_mva/session_manager/.github_config.json"
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            config = {
                "token": token,
                "repo": self.repo,
                "branch": self.branch,
                "set_at": datetime.datetime.now().isoformat()
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            saved_count += 1
        except:
            pass

        if saved_count > 0:
            print(f"✅ Token saved to {saved_count} locations")
            return True
        return False

    def get_token(self) -> Optional[str]:
        """Get token from any available source."""
        if self.token:
            return self.token
        self._load_token()
        return self.token

    def is_configured(self) -> bool:
        """Check if token is available."""
        return self.get_token() is not None

    def get_config(self) -> Dict:
        """Get full config."""
        return {
            "token": self.get_token(),
            "repo": self.repo,
            "branch": self.branch,
            "configured": self.is_configured()
        }

    def clear_token(self):
        """Clear all stored tokens."""
        self.token = None
        for path in self.STORAGE_PATHS:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        print("✅ All stored tokens cleared")

    def test_connection(self) -> bool:
        """Test if token works with GitHub API."""
        token = self.get_token()
        if not token:
            return False

        import urllib.request
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HARRY-ON-TokenManager/1.0"
        }

        try:
            req = urllib.request.Request(
                "https://api.github.com/user",
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                print(f"✅ Token valid! Connected as: {data.get('login', 'unknown')}")
                return True
        except Exception as e:
            print(f"❌ Token test failed: {e}")
            return False


# Global instance
_token_manager = None

def get_token_manager() -> UniversalTokenManager:
    """Get global token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = UniversalTokenManager()
    return _token_manager


def set_universal_token(token: str) -> bool:
    """
    Set token that works across ALL sessions.
    Call this once and token persists everywhere.
    """
    manager = get_token_manager()
    return manager.save_token(token)


def get_universal_token() -> Optional[str]:
    """Get token from any available source."""
    manager = get_token_manager()
    return manager.get_token()


if __name__ == "__main__":
    manager = UniversalTokenManager()
    print("HARRY ON Universal Token Manager v1.0.0")
    print("=" * 50)
    print(f"Token configured: {manager.is_configured()}")
    print(f"Storage locations: {len(manager.STORAGE_PATHS)}")

    if manager.is_configured():
        print(f"Repo: {manager.repo}")
        print(f"Branch: {manager.branch}")
        manager.test_connection()
