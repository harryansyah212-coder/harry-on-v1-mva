#!/usr/bin/env python3
"""
HARRY ON Auto-Backup System v1.0.0
Automatically backs up all project files before session ends
Prevents data loss when chat session expires
"""

import os
import json
import shutil
import datetime
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import zipfile


class AutoBackup:
    """
    Automatic backup system for HARRY ON projects.

    Features:
    - Real-time file change detection
    - Scheduled backups every N minutes
    - Compression to save space
    - Restore from any backup point
    """

    def __init__(self, base_path: str = "/mnt/agents/output/harry_on_v1_mva/",
                 backup_interval_minutes: int = 10):
        self.base_path = Path(base_path)
        self.backup_dir = self.base_path / "session_manager" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.interval = backup_interval_minutes
        self.last_backup = None
        self.file_hashes = {}  # Track file changes

        # Load backup index
        self.index_file = self.backup_dir / "backup_index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        if self.index_file.exists():
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "version": "1.0.0",
            "backups": [],
            "last_full_backup": None,
            "total_size_mb": 0
        }

    def _save_index(self):
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)

    def _hash_file(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content."""
        hasher = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
        except:
            return ""
        return hasher.hexdigest()

    def scan_changes(self) -> Dict:
        """
        Scan all files and detect changes since last backup.
        Returns dict of changed files.
        """
        changes = {
            "new": [],
            "modified": [],
            "deleted": []
        }

        current_hashes = {}

        # Scan all files in base path (excluding backup dir)
        for root, dirs, files in os.walk(self.base_path):
            # Skip backup directory
            if "backups" in root:
                continue

            for file in files:
                file_path = Path(root) / file
                relative = str(file_path.relative_to(self.base_path))
                file_hash = self._hash_file(file_path)
                current_hashes[relative] = file_hash

                if relative not in self.file_hashes:
                    changes["new"].append(relative)
                elif self.file_hashes[relative] != file_hash:
                    changes["modified"].append(relative)

        # Check for deleted files
        for old_file in self.file_hashes:
            if old_file not in current_hashes:
                changes["deleted"].append(old_file)

        self.file_hashes = current_hashes
        return changes

    def create_backup(self, backup_name: str = None, 
                      project_filter: str = None) -> str:
        """
        Create a backup of current project state.

        Args:
            backup_name: Optional custom name
            project_filter: Only backup specific project path

        Returns:
            Backup ID
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = backup_name or f"backup_{timestamp}"
        backup_path = self.backup_dir / f"{backup_id}.zip"

        # Scan changes first
        changes = self.scan_changes()
        total_changes = len(changes["new"]) + len(changes["modified"])

        if total_changes == 0 and self.last_backup:
            print("ℹ️ No changes detected since last backup. Skipping.")
            return self.last_backup

        # Create zip backup
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(self.base_path):
                # Skip backup dir
                if "backups" in root:
                    continue

                # Apply project filter
                if project_filter:
                    rel_root = str(Path(root).relative_to(self.base_path))
                    if project_filter not in rel_root and rel_root != ".":
                        continue

                for file in files:
                    file_path = Path(root) / file
                    relative = str(file_path.relative_to(self.base_path))
                    zf.write(file_path, relative)

        # Record backup
        backup_info = {
            "id": backup_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "path": str(backup_path),
            "size_mb": round(backup_path.stat().st_size / (1024 * 1024), 2),
            "changes": {
                "new": len(changes["new"]),
                "modified": len(changes["modified"]),
                "deleted": len(changes["deleted"])
            },
            "project_filter": project_filter
        }

        self.index["backups"].append(backup_info)
        self.index["last_full_backup"] = datetime.datetime.now().isoformat()
        self._save_index()

        self.last_backup = backup_id

        print(f"✅ Backup created: {backup_id}")
        print(f"   Size: {backup_info['size_mb']} MB")
        print(f"   New: {backup_info['changes']['new']}")
        print(f"   Modified: {backup_info['changes']['modified']}")

        return backup_id

    def restore_backup(self, backup_id: str, target_path: str = None) -> bool:
        """
        Restore files from a backup.

        Args:
            backup_id: Backup identifier
            target_path: Where to restore (default: base_path)
        """
        backup_path = self.backup_dir / f"{backup_id}.zip"

        if not backup_path.exists():
            print(f"❌ Backup not found: {backup_id}")
            return False

        target = Path(target_path or self.base_path)
        target.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(backup_path, "r") as zf:
            zf.extractall(target)

        print(f"✅ Restored backup: {backup_id}")
        print(f"   To: {target}")
        return True

    def list_backups(self) -> List[Dict]:
        """List all available backups."""
        return sorted(self.index["backups"], 
                     key=lambda x: x["timestamp"], 
                     reverse=True)

    def get_latest_backup(self) -> Optional[Dict]:
        """Get the most recent backup info."""
        backups = self.list_backups()
        return backups[0] if backups else None

    def cleanup_old_backups(self, keep_count: int = 10):
        """Remove old backups, keeping only the most recent N."""
        backups = self.list_backups()

        if len(backups) <= keep_count:
            return

        to_delete = backups[keep_count:]
        for backup in to_delete:
            backup_path = Path(backup["path"])
            if backup_path.exists():
                backup_path.unlink()
                print(f"🗑️ Deleted old backup: {backup['id']}")

        self.index["backups"] = backups[:keep_count]
        self._save_index()

    def generate_restore_script(self, backup_id: str) -> str:
        """Generate a standalone restore script."""
        script = f"""#!/bin/bash
# HARRY ON Restore Script
# Backup: {backup_id}
# Generated: {datetime.datetime.now().isoformat()}

echo "🔄 Restoring HARRY ON from backup: {backup_id}"
echo "================================================"

BACKUP_FILE="{self.backup_dir}/{backup_id}.zip"
RESTORE_DIR="/mnt/agents/output/harry_on_v1_mva/"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Create restore directory
mkdir -p "$RESTORE_DIR"

# Extract backup
cd "$RESTORE_DIR"
unzip -o "$BACKUP_FILE"

echo "✅ Restore complete!"
echo "   Location: $RESTORE_DIR"
echo ""
echo "Next steps:"
echo "1. Run: python session_manager/session_manager.py"
echo "2. Resume your project with the session manager"
"""
        return script

    def auto_backup_all(self):
        """Run automatic backup for all active projects."""
        print("🔥 HARRY ON Auto-Backup")
        print("=" * 50)

        # Check for changes
        changes = self.scan_changes()
        total = len(changes["new"]) + len(changes["modified"])

        if total == 0:
            print("ℹ️ No changes to backup")
            return None

        # Create backup
        backup_id = self.create_backup()

        # Cleanup old backups
        self.cleanup_old_backups(keep_count=20)

        return backup_id


if __name__ == "__main__":
    backup = AutoBackup()
    print("HARRY ON Auto-Backup System v1.0.0")
    print("=" * 50)

    # Demo: create backup
    backup_id = backup.auto_backup_all()
    if backup_id:
        print(f"\n✅ Auto-backup complete: {backup_id}")

    print(f"\nTotal backups: {len(backup.list_backups())}")
