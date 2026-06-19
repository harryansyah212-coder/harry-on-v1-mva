#!/usr/bin/env python3
"""
HARRY ON Project Registry v1.0.0
Manages all HARRY ON modules and standalone projects
Provides quick lookup, search, and resume capabilities
"""

import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional
from session_manager.session_manager import SessionManager, get_session_manager


class ProjectRegistry:
    """
    Central registry for all HARRY ON projects.
    Maps project names to IDs for easy lookup.
    """

    # Pre-defined HARRY ON modules (from memory records)
    HARRY_ON_MODULES = {
        "ai_hybrid": {
            "name": "AI Hybrid v4.0.0 Trinity",
            "type": "ai_orchestration",
            "description": "4-AI hybrid system: Claude Opus 4.8 (30%), GPT-5.5 Pro (50%), Kimi K2.6 (20%)",
            "path": "harry_ai_hybrid_v3/",
            "files": 12,
            "key_files": ["router.py", "aggregator.py", "evaluator.py", "fallback.py"]
        },
        "cybersecurity": {
            "name": "Cybersecurity Module",
            "type": "security",
            "description": "HARRY Firewall, threat detection, vulnerability assessment",
            "path": "modules/cybersecurity/",
            "files": 8,
            "key_files": ["firewall.py", "scanner.py", "detector.py", "reporter.py"]
        },
        "ddos_protection": {
            "name": "DDoS Protection",
            "type": "security",
            "description": "6-layer DDoS defense system",
            "path": "modules/ddos_protection/",
            "files": 8,
            "key_files": ["shield.py", "mitigator.py", "analyzer.py"]
        },
        "ddos_resilience": {
            "name": "DDoS Resilience",
            "type": "security",
            "description": "Resilience and recovery mechanisms",
            "path": "modules/ddos_resilience/",
            "files": 6,
            "key_files": ["resilience.py", "recovery.py"]
        },
        "web_scanner": {
            "name": "Web Vulnerability Scanner",
            "type": "security",
            "description": "OWASP Top 10, Port Scanner, Subdomain, Directory brute-force, SSL/TLS audit",
            "path": "modules/web_scanner/",
            "files": 10,
            "key_files": ["scanner.py", "owasp.py", "ssl_audit.py", "reporter.py"]
        },
        "storycraft": {
            "name": "StoryCraft AI",
            "type": "creative",
            "description": "8-module creative writing system: Hook, Pacing, Market, Emotional Arc, Conflict, Dialogue, Revision, Export",
            "path": "modules/storycraft/",
            "files": 18,
            "key_files": ["hook_engine.py", "pacing.py", "market_intel.py", "export.py"]
        },
        "creative_suite": {
            "name": "Creative Suite Preset Master",
            "type": "creative",
            "description": "680+ Adobe & CorelDRAW presets, Color Science Engine",
            "path": "modules/creative_suite_preset_master/",
            "files": 10,
            "key_files": ["preset_engine.py", "color_science.py", "workflows.py"]
        },
        "digital_product": {
            "name": "Digital Product Business Expert",
            "type": "business",
            "description": "6 Expert Engines: Niche Research, Product Creation, Platform, Marketing, Scaling, Analytics",
            "path": "modules/digital_product_expert/",
            "files": 11,
            "key_files": ["niche_engine.py", "product_creator.py", "marketing.py"]
        },
        "ebook": {
            "name": "Ebook Digital Product",
            "type": "business",
            "description": "Ebook HTML premium layout, PDF, cover PNG, sales page",
            "path": "modules/ebook_digital_product/",
            "files": 5,
            "key_files": ["ebook.html", "sales_page.html", "cover.png"]
        },
        "kimi_agent": {
            "name": "Kimi K2.6 Agent Module v2.0",
            "type": "ai_agent",
            "description": "24-file agent system for Kimi K2.6 optimization",
            "path": "modules/kimi_k2_agent/",
            "files": 24,
            "key_files": ["agent.py", "optimizer.py", "executor.py"]
        },
        "vibe_coding": {
            "name": "Vibe Coding 2.0",
            "type": "development",
            "description": "Multi-Agent Orchestration, Self-Healing, LLM Docs, Security Hardening",
            "path": "modules/vibe_coding_2/",
            "files": 16,
            "key_files": ["orchestrator.py", "healer.py", "boilerplate.py"]
        },
        "ai_writing": {
            "name": "AI Writing & Editing Evaluator",
            "type": "content",
            "description": "53 tasks, 12 categories, quality evaluation system",
            "path": "modules/ai_writing_evaluator/",
            "files": 18,
            "key_files": ["evaluator.py", "scorer.py", "reporter.py"]
        },
        "aider": {
            "name": "Aider Integration",
            "type": "development",
            "description": "Multi-AI auto-rotation, git integration, GitHub Codespaces support",
            "path": "modules/aider_integration/",
            "files": 10,
            "key_files": ["aider_bridge.py", "git_sync.py", "codespaces.py"]
        },
        "anti_interrupt": {
            "name": "Anti-Interruption Shield v5.0",
            "type": "system",
            "description": "30 features, 7 tiers, unlimited conversation potential",
            "path": "modules/anti_interruption_shield/",
            "files": 10,
            "key_files": ["shield.py", "protector.py", "enforcer.py"]
        },
        "learning_hub": {
            "name": "Learning Hub",
            "type": "education",
            "description": "AI-powered learning management system",
            "path": "modules/learning_hub/",
            "files": 9,
            "key_files": ["hub.py", "courses.py", "progress.py"]
        }
    }

    STANDALONE_PROJECTS = {
        "ai_story_generator": {
            "name": "AI Story Generator v2.0",
            "type": "web_app",
            "description": "Multi-chapter story generator, 7 genres, 40 chapters, export TXT/MD/JSON",
            "path": "ai_story_generator/",
            "files": 1,
            "key_files": ["ai_story_generator_v2_chapters.html"]
        },
        "phone_tracker": {
            "name": "Phone & WhatsApp Tracker",
            "type": "web_app",
            "description": "Next.js + Vercel, IP geolocation, WhatsApp link generator",
            "path": "phone_whatsapp_tracker/",
            "files": 15,
            "key_files": ["page.tsx", "layout.tsx", "api routes"]
        },
        "auto_clip": {
            "name": "Auto-Clip Video Tool",
            "type": "tool",
            "description": "Auto hook detection, viral scoring, smart clip generation, Whisper captions",
            "path": "auto_clip_tool/",
            "files": 25,
            "key_files": ["clipper.py", "scorer.py", "caption.py"]
        }
    }

    def __init__(self):
        self.sm = get_session_manager()
        self._register_all_modules()

    def _register_all_modules(self):
        """Auto-register all known HARRY ON modules."""
        all_projects = {**self.HARRY_ON_MODULES, **self.STANDALONE_PROJECTS}

        for module_key, module_info in all_projects.items():
            # Check if already registered
            existing = self.find_project_by_name(module_info["name"])
            if existing:
                continue

            # Register new project
            self.sm.create_project(
                project_name=module_info["name"],
                project_type=module_info["type"],
                description=module_info["description"],
                metadata={
                    "module_key": module_key,
                    "path": module_info["path"],
                    "expected_files": module_info["files"],
                    "key_files": module_info["key_files"],
                    "category": "harry_on_module" if module_key in self.HARRY_ON_MODULES else "standalone"
                }
            )

    def find_project_by_name(self, name: str) -> Optional[str]:
        """Find project ID by name (partial match supported)."""
        name_lower = name.lower()
        for pid, proj in self.sm.index["projects"].items():
            if name_lower in proj["name"].lower() or name_lower in pid.lower():
                return pid
        return None

    def get_project_summary(self, project_id: str) -> Dict:
        """Get quick summary of a project."""
        project = self.sm.load_project(project_id)
        if not project:
            return {}

        return {
            "id": project_id,
            "name": project["project_name"],
            "type": project["project_type"],
            "status": project["status"],
            "checkpoints": project["total_checkpoints"],
            "last_active": project["last_active"],
            "description": project["description"]
        }

    def list_all_projects(self) -> List[Dict]:
        """List all projects with summaries."""
        return [self.get_project_summary(pid) for pid in self.sm.index["projects"]]

    def search_projects(self, query: str) -> List[Dict]:
        """Search projects by keyword."""
        results = []
        query_lower = query.lower()

        for pid, proj in self.sm.index["projects"].items():
            search_text = f"{proj['name']} {proj['description']} {proj['type']}".lower()
            if query_lower in search_text:
                results.append(self.get_project_summary(pid))

        return results

    def generate_module_rebuild_plan(self, project_id: str) -> str:
        """Generate a plan to rebuild a module from scratch."""
        project = self.sm.load_project(project_id)
        if not project:
            return "Project not found!"

        meta = project.get("latest_checkpoint", {}).get("state", {}).get("metadata", {})
        if not meta:
            # Try from index
            meta = self.sm.index["projects"].get(project_id, {}).get("metadata", {})

        plan_parts = [
            f"# 🔧 REBUILD PLAN: {project['project_name']}",
            f"",
            f"## Module Info",
            f"- **Name**: {project['project_name']}",
            f"- **Type**: {project['project_type']}",
            f"- **Path**: `{meta.get('path', 'N/A')}`",
            f"- **Expected Files**: {meta.get('expected_files', 'N/A')}",
            f"",
            f"## Key Files to Rebuild",
        ]

        for file in meta.get("key_files", []):
            plan_parts.append(f"- [ ] `{file}`")

        plan_parts.extend([
            f"",
            f"## Rebuild Steps",
            f"1. Create directory structure: `{meta.get('path', 'modules/xxx/')}`",
            f"2. Generate core files based on module description",
            f"3. Add __init__.py and config files",
            f"4. Validate syntax (0 errors)",
            f"5. Run tests (100% pass)",
            f"6. Save checkpoint",
            f"",
            f"## Description",
            f"{project['description']}",
            f"",
            f"## Command to Resume",
            f"```",
            f"HARRY ON resume {project['project_name']}",
            f"```",
        ])

        return "\n".join(plan_parts)


if __name__ == "__main__":
    registry = ProjectRegistry()
    print("HARRY ON Project Registry v1.0.0")
    print("=" * 50)
    print(f"Total projects registered: {len(registry.sm.index['projects'])}")
    print("\nAll modules:")
    for proj in registry.list_all_projects():
        print(f"  • {proj['name']} ({proj['type']}) - {proj['status']}")
