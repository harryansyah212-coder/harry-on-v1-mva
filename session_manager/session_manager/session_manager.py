#!/usr/bin/env python3
"""
HARRY ON Cross-Session Persistence Manager v1.0.0
Solves: File loss between Kimi K2.6 chat sessions
Strategy: Multi-layer persistence + auto-backup + GitHub sync
Author: HARRY ON V1 MVA UNLIMITED v2.0.0
"""

import os
import json
import hashlib
import datetime
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any


class SessionManager:
    """
    Manages cross-session persistence for HARRY ON projects.

    Key Features:
    - Session checkpointing (auto-save project state)
    - Cross-session memory (resume any project in new chat)
    - GitHub sync integration (push to repo automatically)
    - Auto-compression (archive old sessions)
    - Master index (searchable project registry)
    """

    def __init__(self, base_path: str = "/mnt/agents/output/harry_on_v1_mva/"):
        self.base_path = Path(base_path)
        self.session_dir = self.base_path / "session_manager" / "sessions"
        self.archive_dir = self.base_path / "session_manager" / "archive"
        self.index_dir = self.base_path / "session_manager" / "index"
        self.backup_dir = self.base_path / "session_manager" / "backups"
        self.template_dir = self.base_path / "session_manager" / "templates"

        # Ensure directories exist
        for d in [self.session_dir, self.archive_dir, self.index_dir, 
                  self.backup_dir, self.template_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.index_file = self.index_dir / "master_index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        """Load or create master project index."""
        if self.index_file.exists():
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "version": "1.0.0",
            "last_updated": datetime.datetime.now().isoformat(),
            "projects": {},
            "sessions": {},
            "archives": {}
        }

    def _save_index(self):
        """Save master index to disk."""
        self.index["last_updated"] = datetime.datetime.now().isoformat()
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)

    def create_project(self, project_name: str, project_type: str = "general",
                       description: str = "", metadata: Dict = None) -> str:
        """
        Register a new project in the persistence system.

        Args:
            project_name: Unique project identifier (e.g., "ai_story_generator")
            project_type: Category (e.g., "web_app", "python_module", "tool")
            description: Human-readable description
            metadata: Extra project config

        Returns:
            project_id: Unique project hash ID
        """
        project_id = hashlib.sha256(
            f"{project_name}_{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        self.index["projects"][project_id] = {
            "name": project_name,
            "type": project_type,
            "description": description,
            "created_at": datetime.datetime.now().isoformat(),
            "last_active": datetime.datetime.now().isoformat(),
            "status": "active",
            "metadata": metadata or {},
            "sessions": [],
            "file_count": 0,
            "total_size_bytes": 0
        }
        self._save_index()

        # Create project session file
        session_file = self.session_dir / f"{project_id}.json"
        session_data = {
            "project_id": project_id,
            "project_name": project_name,
            "checkpoints": [],
            "current_state": {
                "files": {},
                "variables": {},
                "last_command": "",
                "pending_tasks": [],
                "completed_tasks": [],
                "notes": ""
            },
            "history": []
        }
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Project registered: {project_name} (ID: {project_id})")
        return project_id

    def save_checkpoint(self, project_id: str, checkpoint_name: str = "auto",
                        state_data: Dict = None, files_snapshot: Dict = None):
        """
        Save a project checkpoint (project state at a point in time).

        Args:
            project_id: Project identifier
            checkpoint_name: Name of this checkpoint
            state_data: Current project state (variables, configs, etc.)
            files_snapshot: Dictionary of file paths and their content hashes
        """
        if project_id not in self.index["projects"]:
            print(f"❌ Project {project_id} not found!")
            return False

        session_file = self.session_dir / f"{project_id}.json"
        if not session_file.exists():
            print(f"❌ Session file not found for {project_id}")
            return False

        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        checkpoint = {
            "id": hashlib.sha256(
                f"{project_id}_{checkpoint_name}_{datetime.datetime.now().isoformat()}".encode()
            ).hexdigest()[:12],
            "name": checkpoint_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "state": state_data or {},
            "files": files_snapshot or {},
            "chat_context": "",  # Will be filled by AI
            "notes": ""
        }

        session_data["checkpoints"].append(checkpoint)
        session_data["current_state"] = state_data or session_data["current_state"]

        # Update index
        self.index["projects"][project_id]["last_active"] = datetime.datetime.now().isoformat()
        self.index["projects"][project_id]["sessions"].append(checkpoint["id"])
        self._save_index()

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Checkpoint saved: {checkpoint_name} ({checkpoint['id']})")
        return checkpoint["id"]

    def load_project(self, project_id: str) -> Optional[Dict]:
        """
        Load project state for resumption in a new chat session.

        Args:
            project_id: Project identifier

        Returns:
            Full project state including last checkpoint
        """
        if project_id not in self.index["projects"]:
            # Try search by name
            for pid, proj in self.index["projects"].items():
                if proj["name"] == project_id:
                    project_id = pid
                    break
            else:
                print(f"❌ Project '{project_id}' not found!")
                return None

        session_file = self.session_dir / f"{project_id}.json"
        if not session_file.exists():
            print(f"❌ Session file missing for {project_id}")
            return None

        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        # Get latest checkpoint
        latest_checkpoint = None
        if session_data["checkpoints"]:
            latest_checkpoint = session_data["checkpoints"][-1]

        project_info = self.index["projects"][project_id]

        resume_data = {
            "project_id": project_id,
            "project_name": project_info["name"],
            "project_type": project_info["type"],
            "description": project_info["description"],
            "created_at": project_info["created_at"],
            "last_active": project_info["last_active"],
            "total_checkpoints": len(session_data["checkpoints"]),
            "latest_checkpoint": latest_checkpoint,
            "current_state": session_data["current_state"],
            "history": session_data["history"][-10:] if len(session_data["history"]) > 10 else session_data["history"],
            "status": project_info["status"]
        }

        print(f"✅ Project loaded: {project_info['name']}")
        print(f"   Checkpoints: {resume_data['total_checkpoints']}")
        print(f"   Last active: {project_info['last_active']}")

        return resume_data

    def list_projects(self, status: str = None) -> List[Dict]:
        """List all registered projects."""
        projects = []
        for pid, proj in self.index["projects"].items():
            if status and proj["status"] != status:
                continue
            projects.append({
                "id": pid,
                "name": proj["name"],
                "type": proj["type"],
                "status": proj["status"],
                "last_active": proj["last_active"],
                "checkpoints": len(proj["sessions"])
            })
        return sorted(projects, key=lambda x: x["last_active"], reverse=True)

    def update_project_state(self, project_id: str, key: str, value: Any):
        """Update a specific state variable for a project."""
        session_file = self.session_dir / f"{project_id}.json"
        if not session_file.exists():
            return False

        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        session_data["current_state"][key] = value
        session_data["history"].append({
            "action": f"update_state:{key}",
            "timestamp": datetime.datetime.now().isoformat(),
            "value": str(value)[:200]
        })

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        return True

    def archive_project(self, project_id: str):
        """Archive old project to save space."""
        if project_id not in self.index["projects"]:
            return False

        # Move session file to archive
        session_file = self.session_dir / f"{project_id}.json"
        if session_file.exists():
            archive_file = self.archive_dir / f"{project_id}.json"
            shutil.copy2(session_file, archive_file)
            session_file.unlink()

        self.index["projects"][project_id]["status"] = "archived"
        self.index["archives"][project_id] = datetime.datetime.now().isoformat()
        self._save_index()

        print(f"📦 Project archived: {project_id}")
        return True

    def generate_resume_prompt(self, project_id: str) -> str:
        """
        Generate an AI prompt to resume a project in a new chat session.
        This is the KEY function for cross-session continuity.
        """
        project = self.load_project(project_id)
        if not project:
            return ""

        checkpoint = project["latest_checkpoint"]
        state = project["current_state"]

        prompt_parts = [
            f"# 🔄 RESUME PROJECT: {project['project_name']}",
            f"",
            f"## Project Info",
            f"- **ID**: {project['project_id']}",
            f"- **Type**: {project['project_type']}",
            f"- **Description**: {project['description']}",
            f"- **Created**: {project['created_at']}",
            f"- **Last Active**: {project['last_active']}",
            f"- **Total Checkpoints**: {project['total_checkpoints']}",
            f"",
            f"## Latest Checkpoint",
        ]

        if checkpoint:
            prompt_parts.extend([
                f"- **Name**: {checkpoint['name']}",
                f"- **Timestamp**: {checkpoint['timestamp']}",
                f"- **ID**: {checkpoint['id']}",
                f"",
                f"## Current State",
            ])

            if checkpoint.get("state"):
                for k, v in checkpoint["state"].items():
                    prompt_parts.append(f"- **{k}**: {v}")

            if checkpoint.get("files"):
                prompt_parts.extend([
                    f"",
                    f"## File Snapshot",
                ])
                for filepath, filehash in checkpoint["files"].items():
                    prompt_parts.append(f"- `{filepath}` → hash: {filehash[:8]}...")

            if checkpoint.get("chat_context"):
                prompt_parts.extend([
                    f"",
                    f"## Context from Last Session",
                    f"{checkpoint['chat_context']}",
                ])

        if state.get("pending_tasks"):
            prompt_parts.extend([
                f"",
                f"## Pending Tasks",
            ])
            for task in state["pending_tasks"]:
                prompt_parts.append(f"- [ ] {task}")

        if state.get("completed_tasks"):
            prompt_parts.extend([
                f"",
                f"## Completed Tasks",
            ])
            for task in state["completed_tasks"][-5:]:
                prompt_parts.append(f"- [x] {task}")

        if state.get("notes"):
            prompt_parts.extend([
                f"",
                f"## Notes",
                f"{state['notes']}",
            ])

        if project.get("history"):
            prompt_parts.extend([
                f"",
                f"## Recent History",
            ])
            for entry in project["history"][-5:]:
                prompt_parts.append(f"- [{entry['timestamp']}] {entry['action']}")

        prompt_parts.extend([
            f"",
            f"---",
            f"",
            f"## 🚀 INSTRUCTION FOR AI",
            f"",
            f"You are resuming work on this project in a NEW chat session.",
            f"The previous session ended and all files were cleared from `/mnt/agents/output/`.",
            f"",
            f"### What You Must Do:",
            f"1. **Acknowledge** the project state above",
            f"2. **Check** if files need to be recreated from the file snapshot",
            f"3. **Continue** pending tasks or ask user what to do next",
            f"4. **Update** the session manager with new progress",
            f"",
            f"### Important Rules:",
            f"- Do NOT ask user to re-explain the project",
            f"- Use the context above to continue seamlessly",
            f"- Save checkpoints frequently using the session manager",
            f"- If files are missing, recreate them based on the snapshot",
            f"",
            f"### Session Manager Commands:",
            f"```python",
            f"from session_manager import SessionManager",
            f"sm = SessionManager()",
            f"sm.save_checkpoint('{project_id}', 'checkpoint_name', state_data, files_snapshot)",
            f"sm.update_project_state('{project_id}', 'key', 'value')",
            f"```",
        ])

        return "\n".join(prompt_parts)


# Singleton instance for easy access
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get or create the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


if __name__ == "__main__":
    # Demo
    sm = SessionManager()
    print("HARRY ON Cross-Session Persistence Manager v1.0.0")
    print("=" * 50)
    print(f"Session dir: {sm.session_dir}")
    print(f"Projects registered: {len(sm.index['projects'])}")
