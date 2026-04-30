from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable
import json


@dataclass
class ProjectFiles:
    root: Path
    rtl_files: list[Path] = field(default_factory=list)
    xdc_files: list[Path] = field(default_factory=list)
    timing_reports: list[Path] = field(default_factory=list)
    sim_logs: list[Path] = field(default_factory=list)
    tcl_files: list[Path] = field(default_factory=list)

    @staticmethod
    def discover(root: str | Path) -> "ProjectFiles":
        root_path = Path(root).resolve()
        if not root_path.exists():
            raise FileNotFoundError(f"Project root does not exist: {root_path}")

        rtl_ext = {".v", ".sv", ".vh", ".svh"}
        rpt_ext = {".rpt", ".txt"}
        sim_names = {"sim.log", "simulation.log", "xsim.log", "questa.log", "modelsim.log"}

        rtl_files: list[Path] = []
        xdc_files: list[Path] = []
        timing_reports: list[Path] = []
        sim_logs: list[Path] = []
        tcl_files: list[Path] = []

        ignored_dirs = {".git", ".venv", "venv", "runs", "build", "dist", "__pycache__"}
        for path in root_path.rglob("*"):
            if any(part in ignored_dirs for part in path.parts):
                continue
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            name = path.name.lower()
            if suffix in rtl_ext:
                rtl_files.append(path)
            elif suffix == ".xdc":
                xdc_files.append(path)
            elif suffix == ".tcl":
                tcl_files.append(path)
            elif suffix in rpt_ext and ("timing" in name or "slack" in name):
                timing_reports.append(path)
            elif name in sim_names or (suffix == ".log" and "sim" in name):
                sim_logs.append(path)

        return ProjectFiles(
            root=root_path,
            rtl_files=sorted(rtl_files),
            xdc_files=sorted(xdc_files),
            timing_reports=sorted(timing_reports),
            sim_logs=sorted(sim_logs),
            tcl_files=sorted(tcl_files),
        )

    def to_jsonable(self) -> dict[str, Any]:
        data = asdict(self)
        for key, value in list(data.items()):
            if isinstance(value, Path):
                data[key] = str(value)
            elif isinstance(value, list):
                data[key] = [str(v) for v in value]
        return data


@dataclass
class Finding:
    agent: str
    severity: str
    title: str
    detail: str
    file: str | None = None
    line: int | None = None
    evidence: list[str] = field(default_factory=list)
    recommendation: str | None = None

    def to_markdown(self) -> str:
        loc = ""
        if self.file:
            loc = f"\n- Location: `{self.file}`"
            if self.line:
                loc += f":{self.line}"
        evidence = "" if not self.evidence else "\n" + "\n".join(f"  - {item}" for item in self.evidence)
        rec = "" if not self.recommendation else f"\n- Recommendation: {self.recommendation}"
        return (
            f"### [{self.severity.upper()}] {self.title}\n"
            f"- Agent: `{self.agent}`{loc}\n"
            f"- Detail: {self.detail}{evidence}{rec}\n"
        )


@dataclass
class AgentResult:
    name: str
    summary: str
    findings: list[Finding] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunContext:
    files: ProjectFiles
    out_dir: Path
    top: str | None = None
    dry_run: bool = True
    max_source_chars: int = 120_000
    shared: dict[str, Any] = field(default_factory=dict)
    results: list[AgentResult] = field(default_factory=list)

    def add_result(self, result: AgentResult) -> None:
        self.results.append(result)
        self.shared[result.name] = result.data

    def all_findings(self) -> Iterable[Finding]:
        for result in self.results:
            yield from result.findings

    def write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
