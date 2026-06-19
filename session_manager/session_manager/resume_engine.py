#!/usr/bin/env python3
"""
HARRY ON Resume Engine v1.0.0
The HEART of cross-session persistence.

This engine allows baginda to:
1. Save project state before chat ends
2. Resume ANY project in a new chat session
3. Never lose progress again

Usage:
    from resume_engine import ResumeEngine
    engine = ResumeEngine()

    # Before ending chat:
    engine.save_session("my_project", context="Current progress...")

    # In new chat:
    engine.resume_project("my_project")
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from session_manager import SessionManager, get_session_manager
from session_manager.project_registry import ProjectRegistry
from session_manager.auto_backup import AutoBackup


class ResumeEngine:
    """
    Main engine for cross-session project resumption.

    This is the PRIMARY interface baginda should use.
    """

    def __init__(self):
        self.sm = get_session_manager()
        self.registry = ProjectRegistry()
        self.backup = AutoBackup()
        self.base_path = Path("/mnt/agents/output/harry_on_v1_mva/")

        # Session state file (quick access)
        self.state_file = self.base_path / "session_manager" / "current_state.json"

    def save_session(self, project_name: str, context: str = "",
                     files_snapshot: Dict = None, 
                     pending_tasks: List[str] = None,
                     notes: str = "") -> str:
        """
        Save current session state BEFORE ending the chat.

        Args:
            project_name: Name of project (e.g., "AI Story Generator v2.0")
            context: Summary of what was accomplished in this session
            files_snapshot: Dict of file paths and content summaries
            pending_tasks: List of tasks not yet completed
            notes: Any additional notes

        Returns:
            checkpoint_id
        """
        # Find project
        project_id = self.registry.find_project_by_name(project_name)

        if not project_id:
            print(f"⚠️ Project '{project_name}' not found. Creating new...")
            project_id = self.sm.create_project(
                project_name=project_name,
                project_type="general",
                description=context[:200]
            )

        # Build state
        state = {
            "last_session_date": datetime.datetime.now().isoformat(),
            "chat_context": context,
            "pending_tasks": pending_tasks or [],
            "notes": notes,
            "metadata": self.sm.index["projects"].get(project_id, {}).get("metadata", {})
        }

        # Save checkpoint
        checkpoint_id = self.sm.save_checkpoint(
            project_id=project_id,
            checkpoint_name=f"session_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}",
            state_data=state,
            files_snapshot=files_snapshot or {}
        )

        # Also save to quick-access state file
        quick_state = {
            "last_project": project_name,
            "last_project_id": project_id,
            "last_checkpoint": checkpoint_id,
            "last_saved": datetime.datetime.now().isoformat(),
            "context": context,
            "pending": pending_tasks or []
        }

        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(quick_state, f, indent=2, ensure_ascii=False)

        # Auto-backup
        self.backup.auto_backup_all()

        print(f"\n✅ SESSION SAVED SUCCESSFULLY")
        print(f"   Project: {project_name}")
        print(f"   Checkpoint: {checkpoint_id}")
        print(f"   Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n💡 To resume in new chat, say:")
        print(f"   'HARRY ON resume {project_name}'")

        return checkpoint_id

    def resume_project(self, project_name: str) -> str:
        """
        Resume a project in a NEW chat session.

        Args:
            project_name: Name or ID of project to resume

        Returns:
            AI prompt string with full context for resumption
        """
        # Try to find project
        project_id = self.registry.find_project_by_name(project_name)

        if not project_id:
            # Try quick state file
            if self.state_file.exists():
                with open(self.state_file, "r", encoding="utf-8") as f:
                    quick_state = json.load(f)
                if quick_state.get("last_project") == project_name or                    quick_state.get("last_project_id") == project_name:
                    project_id = quick_state["last_project_id"]

        if not project_id:
            print(f"❌ Project '{project_name}' not found!")
            print(f"\n📋 Available projects:")
            for proj in self.registry.list_all_projects():
                print(f"   • {proj['name']}")
            return ""

        # Generate resume prompt
        resume_prompt = self.sm.generate_resume_prompt(project_id)

        # Also restore files if backup exists
        latest_backup = self.backup.get_latest_backup()
        if latest_backup:
            resume_prompt += f"""

## 📦 Latest Backup Available
- **Backup ID**: {latest_backup['id']}
- **Created**: {latest_backup['timestamp']}
- **Size**: {latest_backup['size_mb']} MB
- **Changes**: {latest_backup['changes']['new']} new, {latest_backup['changes']['modified']} modified

### To Restore Files:
```python
from session_manager.auto_backup import AutoBackup
backup = AutoBackup()
backup.restore_backup("{latest_backup['id']}")
```
"""

        print(f"\n✅ RESUME DATA READY")
        print(f"   Project: {self.sm.index['projects'][project_id]['name']}")
        print(f"   Checkpoints: {len(self.sm.index['projects'][project_id]['sessions'])}")

        return resume_prompt

    def quick_resume(self) -> str:
        """
        Quick resume last active project.
        Use this when baginda just says 'lanjutkan' without specifying project.
        """
        if not self.state_file.exists():
            print("❌ No previous session found!")
            return ""

        with open(self.state_file, "r", encoding="utf-8") as f:
            state = json.load(f)

        project_name = state.get("last_project", "")
        if not project_name:
            print("❌ No last project recorded!")
            return ""

        print(f"🔄 Quick resuming last project: {project_name}")
        return self.resume_project(project_name)

    def list_all_sessions(self) -> List[Dict]:
        """List all saved sessions with status."""
        sessions = []

        for pid, proj in self.sm.index["projects"].items():
            session_file = self.sm.session_dir / f"{pid}.json"
            if session_file.exists():
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                sessions.append({
                    "project_id": pid,
                    "name": proj["name"],
                    "type": proj["type"],
                    "checkpoints": len(data["checkpoints"]),
                    "last_active": proj["last_active"],
                    "status": proj["status"]
                })

        return sorted(sessions, key=lambda x: x["last_active"], reverse=True)

    def generate_session_summary(self, project_id: str) -> str:
        """Generate human-readable summary of a project's session history."""
        project = self.sm.load_project(project_id)
        if not project:
            return "Project not found!"

        summary = f"""
# 📊 SESSION SUMMARY: {project['project_name']}

## Overview
- **Status**: {project['status']}
- **Created**: {project['created_at'][:10]}
- **Last Active**: {project['last_active'][:10]}
- **Total Checkpoints**: {project['total_checkpoints']}

## Session History
"""

        session_file = self.sm.session_dir / f"{project_id}.json"
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            for i, cp in enumerate(data["checkpoints"][-5:], 1):
                summary += f"\n### Checkpoint {i}: {cp['name']}\n"
                summary += f"- **Time**: {cp['timestamp']}\n"
                if cp.get("chat_context"):
                    summary += f"- **Context**: {cp['chat_context'][:200]}...\n"

        summary += f"""
## Current State
"""

        state = project["current_state"]
        if state.get("pending_tasks"):
            summary += "\n### Pending Tasks\n"
            for task in state["pending_tasks"]:
                summary += f"- [ ] {task}\n"

        if state.get("notes"):
            summary += f"\n### Notes\n{state['notes']}\n"

        return summary

    def export_session_data(self, project_id: str, format: str = "json") -> str:
        """
        Export session data for external storage.

        Args:
            project_id: Project to export
            format: "json", "markdown", or "txt"

        Returns:
            File path of exported data
        """
        project = self.sm.load_project(project_id)
        if not project:
            return ""

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = self.base_path / "session_manager" / "exports"
        export_dir.mkdir(exist_ok=True)

        if format == "json":
            export_file = export_dir / f"{project['project_name']}_{timestamp}.json"
            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(project, f, indent=2, ensure_ascii=False)

        elif format == "markdown":
            export_file = export_dir / f"{project['project_name']}_{timestamp}.md"
            with open(export_file, "w", encoding="utf-8") as f:
                f.write(self.generate_session_summary(project_id))

        else:
            export_file = export_dir / f"{project['project_name']}_{timestamp}.txt"
            with open(export_file, "w", encoding="utf-8") as f:
                f.write(f"HARRY ON Session Export\n")
                f.write(f"Project: {project['project_name']}\n")
                f.write(f"Date: {datetime.datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n\n")
                f.write(json.dumps(project, indent=2, ensure_ascii=False))

        print(f"✅ Exported to: {export_file}")
        return str(export_file)


# === COMMAND HANDLERS ===

def handle_harry_on_command(command: str, *args) -> str:
    """
    Handle HARRY ON commands for session management.

    Commands:
    - HARRY ON save [project] [context]  → Save current session
    - HARRY ON resume [project]          → Resume project in new chat
    - HARRY ON list                      → List all saved sessions
    - HARRY ON status [project]          → Show project status
    - HARRY ON backup                    → Force backup now
    - HARRY ON export [project]          → Export session data
    """
    engine = ResumeEngine()

    if command == "save":
        project = args[0] if args else "default"
        context = " ".join(args[1:]) if len(args) > 1 else "Session saved"
        engine.save_session(project, context=context)
        return f"✅ Session saved: {project}"

    elif command == "resume":
        project = args[0] if args else ""
        if not project:
            return engine.quick_resume()
        return engine.resume_project(project)

    elif command == "list":
        sessions = engine.list_all_sessions()
        result = "📋 SAVED SESSIONS:\n"
        for s in sessions:
            result += f"  • {s['name']} ({s['type']}) - {s['checkpoints']} checkpoints\n"
        return result

    elif command == "status":
        project = args[0] if args else ""
        if not project:
            return "Usage: HARRY ON status [project_name]"
        return engine.generate_session_summary(
            engine.registry.find_project_by_name(project)
        )

    elif command == "backup":
        backup_id = engine.backup.auto_backup_all()
        return f"✅ Backup created: {backup_id}"

    elif command == "export":
        project = args[0] if args else ""
        if not project:
            return "Usage: HARRY ON export [project_name]"
        project_id = engine.registry.find_project_by_name(project)
        filepath = engine.export_session_data(project_id, "markdown")
        return f"✅ Exported: {filepath}"

    else:
        return f"❌ Unknown command: {command}\nAvailable: save, resume, list, status, backup, export"


if __name__ == "__main__":
    engine = ResumeEngine()
    print("🔥 HARRY ON Resume Engine v1.0.0")
    print("=" * 60)
    print("\nCross-Session Persistence is ACTIVE")
    print("\nCommands:")
    print("  engine.save_session('project_name', 'context')")
    print("  engine.resume_project('project_name')")
    print("  engine.quick_resume()")
    print("  engine.list_all_sessions()")
    print("\nOr use: handle_harry_on_command('command', 'args...')")
