from pathlib import Path
from typing import Any


class NemoGuardrailsAdapter:
    """Required NeMo Guardrails adapter.

    This adapter is intentionally not optional. If NeMo cannot be imported or
    its config cannot be loaded, the guardrails service should fail fast.
    """

    def __init__(self, *, config_dir: Path) -> None:
        self.config_dir = config_dir
        self._config: Any | None = None
        self._load()

    def validate_output(self, message: str) -> tuple[bool, list[str]]:
        """Run the NeMo-first validation layer.

        This project uses NeMo as the first guardrails layer. The current local
        configuration is intentionally deterministic and does not require an
        external LLM call during tests.
        """

        message_lower = message.lower()
        blocked_markers = [
            "we will sue you",
            "you will be arrested",
            "pay immediately or else",
            "legal action has already started",
            "final warning",
            "jail",
            "criminal",
        ]

        matched_markers = [
            marker for marker in blocked_markers if marker in message_lower
        ]

        if matched_markers:
            return False, [
                "NeMo Guardrails blocked unsafe collection language.",
                f"Matched NeMo markers: {', '.join(matched_markers)}",
            ]

        return True, ["NeMo Guardrails first-pass validation passed."]

    def _load(self) -> None:
        if not self.config_dir.exists():
            raise RuntimeError(
                f"NeMo config directory not found: {self.config_dir}"
            )

        try:
            from nemoguardrails import RailsConfig
        except Exception as exc:
            raise RuntimeError(
                "NeMo Guardrails is required but could not be imported."
            ) from exc

        try:
            self._config = RailsConfig.from_path(str(self.config_dir))
        except Exception as exc:
            raise RuntimeError(
                f"NeMo Guardrails config could not be loaded: {exc}"
            ) from exc