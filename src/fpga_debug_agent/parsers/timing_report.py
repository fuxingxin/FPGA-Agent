from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class TimingPath:
    slack: float
    path_type: str = "unknown"
    startpoint: str | None = None
    endpoint: str | None = None
    clock_group: str | None = None
    logic_levels: int | None = None
    requirement: float | None = None
    source_file: str | None = None
    evidence: list[str] = field(default_factory=list)


@dataclass
class TimingReport:
    source: str
    wns: float | None = None
    tns: float | None = None
    whs: float | None = None
    ths: float | None = None
    failing_paths: list[TimingPath] = field(default_factory=list)


_FLOAT = r"[-+]?\d+(?:\.\d+)?"


def _find_float(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text, re.I | re.M)
    return float(match.group(1)) if match else None


def parse_timing_report(path: Path) -> TimingReport:
    text = path.read_text(encoding="utf-8", errors="ignore")
    report = TimingReport(source=str(path))
    report.wns = _find_float(r"\bWNS\b\s*[:=]?\s*(%s)" % _FLOAT, text)
    report.tns = _find_float(r"\bTNS\b\s*[:=]?\s*(%s)" % _FLOAT, text)
    report.whs = _find_float(r"\bWHS\b\s*[:=]?\s*(%s)" % _FLOAT, text)
    report.ths = _find_float(r"\bTHS\b\s*[:=]?\s*(%s)" % _FLOAT, text)

    chunks = re.split(r"(?=\n\s*(?:Slack|SLACK)\b)", text)
    for chunk in chunks:
        slack_match = re.search(r"\bSlack\b\s*\(?[^\n]*?\)?\s*[:=]?\s*(%s)" % _FLOAT, chunk, re.I)
        if not slack_match:
            continue
        slack = float(slack_match.group(1))
        if slack >= 0:
            continue
        start = re.search(r"Startpoint:\s*([^\n]+)", chunk, re.I)
        end = re.search(r"Endpoint:\s*([^\n]+)", chunk, re.I)
        group = re.search(r"Path Group:\s*([^\n]+)", chunk, re.I)
        requirement = _find_float(r"Requirement:\s*(%s)" % _FLOAT, chunk)
        levels = re.search(r"Logic Levels:\s*(\d+)", chunk, re.I)
        ptype = "hold" if re.search(r"\bhold\b", chunk, re.I) else "setup"
        report.failing_paths.append(
            TimingPath(
                slack=slack,
                path_type=ptype,
                startpoint=start.group(1).strip() if start else None,
                endpoint=end.group(1).strip() if end else None,
                clock_group=group.group(1).strip() if group else None,
                logic_levels=int(levels.group(1)) if levels else None,
                requirement=requirement,
                source_file=str(path),
                evidence=[line.strip() for line in chunk.splitlines()[:20] if line.strip()],
            )
        )

    # Compact Vivado summary table fallback: find negative slack lines around 'VIOLATED'.
    if not report.failing_paths:
        for line in text.splitlines():
            if "VIOLATED" in line.upper():
                floats = re.findall(_FLOAT, line)
                if floats:
                    slack = float(floats[0])
                    if slack < 0:
                        report.failing_paths.append(
                            TimingPath(slack=slack, evidence=[line.strip()], source_file=str(path))
                        )
    return report
