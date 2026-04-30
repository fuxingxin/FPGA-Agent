from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class XdcCommand:
    command: str
    args: str
    file: str
    line: int


@dataclass
class XdcFile:
    source: str
    commands: list[XdcCommand] = field(default_factory=list)
    clocks: list[XdcCommand] = field(default_factory=list)
    generated_clocks: list[XdcCommand] = field(default_factory=list)
    input_delays: list[XdcCommand] = field(default_factory=list)
    output_delays: list[XdcCommand] = field(default_factory=list)
    clock_groups: list[XdcCommand] = field(default_factory=list)
    false_paths: list[XdcCommand] = field(default_factory=list)
    multicycle_paths: list[XdcCommand] = field(default_factory=list)


def parse_xdc_file(path: Path) -> XdcFile:
    result = XdcFile(source=str(path))
    raw_lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    logical_lines: list[tuple[int, str]] = []
    buf = ""
    start_line = 1
    for idx, line in enumerate(raw_lines, start=1):
        clean = re.sub(r"#.*$", "", line).strip()
        if not clean:
            continue
        if not buf:
            start_line = idx
        if clean.endswith("\\"):
            buf += clean[:-1] + " "
        else:
            buf += clean
            logical_lines.append((start_line, buf.strip()))
            buf = ""
    if buf:
        logical_lines.append((start_line, buf.strip()))

    for line_no, line in logical_lines:
        match = re.match(r"(\w+)\b\s*(.*)", line)
        if not match:
            continue
        cmd = XdcCommand(command=match.group(1), args=match.group(2), file=str(path), line=line_no)
        result.commands.append(cmd)
        if cmd.command == "create_clock":
            result.clocks.append(cmd)
        elif cmd.command == "create_generated_clock":
            result.generated_clocks.append(cmd)
        elif cmd.command == "set_input_delay":
            result.input_delays.append(cmd)
        elif cmd.command == "set_output_delay":
            result.output_delays.append(cmd)
        elif cmd.command == "set_clock_groups":
            result.clock_groups.append(cmd)
        elif cmd.command == "set_false_path":
            result.false_paths.append(cmd)
        elif cmd.command == "set_multicycle_path":
            result.multicycle_paths.append(cmd)
    return result


def parse_xdc_files(paths: list[Path]) -> list[XdcFile]:
    return [parse_xdc_file(path) for path in paths]
