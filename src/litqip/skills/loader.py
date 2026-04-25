from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("litqip.skills")

def _default_skills_dir() -> Path:
    return Path.cwd() / "skills"


class Skill:
    name: str
    description: str
    body: str
    meta: dict[str, str]

    def __init__(self, name: str, description: str, body: str, meta: dict[str, str]) -> None:
        self.name = name
        self.description = description
        self.body = body
        self.meta = meta


class SkillLoader:
    def __init__(self, skills_dir: Path | None = None) -> None:
        self.skills_dir = skills_dir or _default_skills_dir()
        self._skills: dict[str, Skill] = {}
        self._load_all()

    def _load_all(self) -> None:
        if not self.skills_dir.exists():
            logger.info("skills dir not found: %s", self.skills_dir)
            return
        for f in sorted(self.skills_dir.rglob("SKILL.md")):
            self._load_file(f)
        logger.info("loaded %d skills", len(self._skills))

    def _load_file(self, path: Path) -> None:
        try:
            text = path.read_text()
            match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
            meta: dict[str, str] = {}
            body = text
            if match:
                for line in match.group(1).strip().splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip()] = v.strip()
                body = match.group(2).strip()
            name = meta.get("name", path.parent.name)
            desc = meta.get("description", "-")
            self._skills[name] = Skill(name=name, description=desc, body=body, meta=meta)
            logger.debug("loaded skill: %s", name)
        except Exception as e:
            logger.warning("failed to load skill %s: %s", path, e)

    def descriptions(self) -> str:
        if not self._skills:
            return "(no skills)"
        return "\n".join(f"  - {n}: {s.description}" for n, s in self._skills.items())

    def load(self, name: str) -> str:
        skill = self._skills.get(name)
        if not skill:
            available = ", ".join(self._skills.keys())
            return f"Error: Unknown skill '{name}'. Available: {available}"
        return f'<skill name="{name}">\n{skill.body}\n</skill>'

    def list_names(self) -> list[str]:
        return list(self._skills.keys())


# Global instance
skills = SkillLoader()
