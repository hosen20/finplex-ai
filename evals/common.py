"""Shared helpers for Finplex AI golden evaluation scripts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
THRESHOLDS_PATH = ROOT_DIR / "evals" / "eval_thresholds.yaml"
REPORTS_DIR = ROOT_DIR / "reports" / "evals"


@dataclass(frozen=True)
class EvalResult:
    """Result object returned by an evaluation script."""

    name: str
    metrics: dict[str, float]
    passed: bool
    failures: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result for console and report output."""
        return {
            "name": self.name,
            "passed": self.passed,
            "metrics": self.metrics,
            "failures": self.failures,
        }


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file with a helpful error message."""
    if not path.exists():
        raise FileNotFoundError(f"Missing golden file: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_thresholds(path: Path = THRESHOLDS_PATH) -> dict[str, float]:
    """Load flat numeric thresholds from a small YAML-style file.

    The project does not need a YAML dependency just for CI thresholds. This
    parser intentionally supports the simple format used by eval_thresholds.yaml:
    one ``key: number`` pair per line, with comments allowed.
    """
    thresholds: dict[str, float] = {}
    if not path.exists():
        return thresholds

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue

        key, value = line.split(":", 1)
        value = value.strip().split("#", 1)[0].strip()
        if not value:
            continue

        try:
            thresholds[key.strip()] = float(value)
        except ValueError as exc:
            raise ValueError(f"Threshold {key.strip()} must be numeric") from exc

    return thresholds


def normalize_text(text: str) -> str:
    """Normalize text for deterministic lexical scoring."""
    return re.sub(r"\s+", " ", text.casefold()).strip()


def tokenize(text: str) -> set[str]:
    """Return simple alphanumeric tokens for retrieval-style scoring."""
    return set(re.findall(r"[a-z0-9]+", normalize_text(text)))


def safe_divide(numerator: float, denominator: float) -> float:
    """Return zero instead of raising when a denominator is zero."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def write_report(result: EvalResult) -> Path:
    """Write a JSON report under reports/evals and return its path."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{result.name}.json"
    report_path.write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report_path


def print_result(result: EvalResult) -> None:
    """Print a compact evaluation result for local and CI logs."""
    status = "PASS" if result.passed else "FAIL"
    print(f"[{status}] {result.name}")
    for metric, value in sorted(result.metrics.items()):
        print(f"  - {metric}: {value:.3f}")
    for failure in result.failures:
        print(f"  - failure: {failure}")


def exit_for_result(result: EvalResult) -> None:
    """Print, write, and exit non-zero if an eval fails."""
    print_result(result)
    report_path = write_report(result)
    print(f"  - report: {report_path}")
    if not result.passed:
        raise SystemExit(1)
