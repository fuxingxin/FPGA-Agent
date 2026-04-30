from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class SimIssue:
    severity: str
    line: int
    text: str


@dataclass
class SimLog:
    source: str
    issues: list[SimIssue] = field(default_factory=list)
    has_finish: bool = False
    has_fatal: bool = False


_PATTERNS = [
    ("error", re.compile(r"\b(error|failed|mismatch|assertion failed)\b", re.I)),
    ("fatal", re.compile(r"\b(fatal|segmentation fault|crash)\b", re.I)),
    ("warning", re.compile(r"\b(warning|x-propagation|unknown|metastability)\b", re.I)),
]


def parse_sim_log(path: Path) -> SimLog:
    log = SimLog(source=str(path))
    for idx, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        if "$finish" in line or "Simulation finished" in line or "finish" in line.lower():
            log.has_finish = True
        for severity, pattern in _PATTERNS:
            if pattern.search(line):
                if severity == "fatal":
                    log.has_fatal = True
                log.issues.append(SimIssue(severity=severity, line=idx, text=line.strip()))
                break
    return log
