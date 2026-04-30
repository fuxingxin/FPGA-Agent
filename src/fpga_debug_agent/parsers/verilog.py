from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class AlwaysBlock:
    sensitivity: str
    line: int
    text: str
    kind: str
    clocks: list[str] = field(default_factory=list)
    resets: list[str] = field(default_factory=list)
    nonblocking_count: int = 0
    blocking_count: int = 0


@dataclass
class VerilogModule:
    name: str
    file: str
    line: int
    ports: list[str] = field(default_factory=list)
    regs: list[str] = field(default_factory=list)
    wires: list[str] = field(default_factory=list)
    always_blocks: list[AlwaysBlock] = field(default_factory=list)
    instantiations: list[str] = field(default_factory=list)
    parameters: list[str] = field(default_factory=list)


@dataclass
class VerilogDesign:
    modules: list[VerilogModule]
    clocks: set[str] = field(default_factory=set)
    resets: set[str] = field(default_factory=set)
    potential_cdc_signals: list[str] = field(default_factory=list)


_COMMENT_RE = re.compile(r"//.*?$|/\*.*?\*/", re.S | re.M)
_MODULE_RE = re.compile(r"\bmodule\s+(\w+)\s*(?:#\s*\((.*?)\))?\s*\((.*?)\)\s*;", re.S)
_ENDMODULE_RE = re.compile(r"\bendmodule\b")
_ALWAYS_RE = re.compile(r"\balways(?:_ff|_comb|_latch)?\s*@\s*\((.*?)\)\s*begin(.*?)(?=\n\s*end\b)", re.S)
_DECL_RE = re.compile(r"\b(input|output|inout|reg|wire|logic)\b\s*(?:signed\s*)?(?:\[[^\]]+\]\s*)?([^;\n]+)[;\n]")
_PARAM_RE = re.compile(r"\bparameter\s+(?:\w+\s+)?(\w+)")
_INSTANCE_RE = re.compile(r"^\s*(\w+)\s*(?:#\s*\()?[\w\s,.'()\[\]:+-]*\s+(\w+)\s*\(", re.M)


def strip_comments(text: str) -> str:
    return re.sub(_COMMENT_RE, "", text)


def _line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _split_names(blob: str) -> list[str]:
    names: list[str] = []
    for part in blob.split(","):
        part = re.sub(r"=.*", "", part).strip()
        part = re.sub(r"\[[^\]]+\]", "", part).strip()
        if not part:
            continue
        token = re.findall(r"[A-Za-z_]\w*", part)
        if token:
            names.append(token[-1])
    return names


def parse_verilog_file(path: Path) -> list[VerilogModule]:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    text = strip_comments(raw)
    modules: list[VerilogModule] = []

    for match in _MODULE_RE.finditer(text):
        name = match.group(1)
        body_start = match.end()
        end_match = _ENDMODULE_RE.search(text, body_start)
        if not end_match:
            end_idx = len(text)
        else:
            end_idx = end_match.start()
        body = text[body_start:end_idx]
        header = match.group(0)
        module = VerilogModule(name=name, file=str(path), line=_line_number(text, match.start()))
        module.ports = sorted(set(_split_names(match.group(3))))
        module.parameters = sorted(set(_PARAM_RE.findall(match.group(2) or "") + _PARAM_RE.findall(body)))

        for decl in _DECL_RE.finditer(header + "\n" + body):
            kind, blob = decl.group(1), decl.group(2)
            names = _split_names(blob)
            if kind in {"input", "output", "inout"}:
                module.ports = sorted(set(module.ports + names))
            elif kind in {"reg", "logic"}:
                module.regs = sorted(set(module.regs + names))
            elif kind == "wire":
                module.wires = sorted(set(module.wires + names))

        for always in _ALWAYS_RE.finditer(body):
            sensitivity = " ".join(always.group(1).split())
            block_text = always.group(0)
            kind = "seq" if "posedge" in sensitivity or "negedge" in sensitivity else "comb"
            clocks = re.findall(r"(?:posedge|negedge)\s+(\w+)", sensitivity)
            resets = [sig for sig in clocks if re.search(r"rst|reset|areset", sig, re.I)]
            clocks = [sig for sig in clocks if sig not in resets]
            module.always_blocks.append(
                AlwaysBlock(
                    sensitivity=sensitivity,
                    line=module.line + _line_number(body, always.start()) - 1,
                    text=block_text[:3000],
                    kind=kind,
                    clocks=clocks,
                    resets=resets,
                    nonblocking_count=len(re.findall(r"<=", block_text)),
                    blocking_count=len(re.findall(r"(?<![<>=!])=(?!=)", block_text)),
                )
            )

        for inst in _INSTANCE_RE.finditer(body):
            cell_type, inst_name = inst.group(1), inst.group(2)
            if cell_type not in {"if", "for", "while", "case", "assign", "always"}:
                module.instantiations.append(f"{cell_type} {inst_name}")
        modules.append(module)
    return modules


def parse_design(paths: list[Path]) -> VerilogDesign:
    modules: list[VerilogModule] = []
    for path in paths:
        modules.extend(parse_verilog_file(path))

    clocks: set[str] = set()
    resets: set[str] = set()
    for module in modules:
        for block in module.always_blocks:
            clocks.update(block.clocks)
            resets.update(block.resets)

    potential_cdc: list[str] = []
    clock_to_blocks: dict[str, int] = {}
    for module in modules:
        for block in module.always_blocks:
            for clk in block.clocks:
                clock_to_blocks[clk] = clock_to_blocks.get(clk, 0) + 1
        if len({clk for blk in module.always_blocks for clk in blk.clocks}) > 1:
            potential_cdc.append(module.name)

    return VerilogDesign(modules=modules, clocks=clocks, resets=resets, potential_cdc_signals=potential_cdc)
