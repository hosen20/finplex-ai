from pathlib import Path
from typing import Any

import yaml

from app.config import settings

DEFAULT_POLICIES: dict[str, Any] = {
    "policy_version": "guardrails_policy_v0.1.0",
    "prohibited_phrases": [
        "we will sue you",
        "you will be arrested",
        "final warning",
        "pay immediately or else",
        "legal action has already started",
        "we will contact your employer",
        "we will shame you",
    ],
    "prohibited_regex": [
        r"\barrest(ed)?\b",
        r"\bjail\b",
        r"\bcriminal\b",
        r"\bpolice\b",
        r"\bpublicly report\b",
    ],
    "aggressive_terms": [
        "threat",
        "shame",
        "refuse",
        "blacklist",
        "harass",
        "punish",
    ],
    "required_evidence_minimum": 1,
    "max_exclamation_marks": 1,
    "max_uppercase_ratio": 0.35,
}


class PolicyLoader:
    """Loads machine-readable guardrail policies from regulations/."""

    def __init__(self, regulations_dir: Path | None = None) -> None:
        self.regulations_dir = regulations_dir or settings.regulations_dir

    def load(self) -> dict[str, Any]:
        policies = DEFAULT_POLICIES.copy()
        machine_dir = self.regulations_dir / "machine_readable"

        for file_name in [
            "guardrail_thresholds.yaml",
            "prohibited_language.yaml",
            "required_evidence.yaml",
            "communication_rules.yaml",
            "audit_requirements.yaml",
        ]:
            policies.update(self._read_yaml(machine_dir / file_name))

        return policies

    def _read_yaml(self, path: Path) -> dict[str, Any]:
        if not path.exists() or path.stat().st_size == 0:
            return {}

        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else {}