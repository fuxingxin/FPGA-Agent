from __future__ import annotations

import argparse
from pathlib import Path
import sys

from fpga_debug_agent.config import Settings
from fpga_debug_agent.graph import DebugGraph


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fpga-debug-agent",
        description="Multi-agent FPGA RTL, timing, XDC and simulation debug assistant",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="Run the multi-agent debug workflow")
    analyze.add_argument("--project", required=True, help="Project root containing RTL/XDC/reports/logs")
    analyze.add_argument("--out", default="runs/latest", help="Output directory")
    analyze.add_argument("--top", default=None, help="Top module name used by generated Vivado Tcl")
    analyze.add_argument("--part", default="xc7k325tffg900-2", help="FPGA part used by generated Vivado Tcl")
    analyze.add_argument("--execute", action="store_true", help="Run Vivado instead of dry-run script generation")

    demo = sub.add_parser("demo", help="Run bundled demo project")
    demo.add_argument("--out", default="runs/demo", help="Output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env()

    if args.command == "analyze":
        graph = DebugGraph(settings=settings, part=args.part)
        ctx = graph.run(
            project_root=args.project,
            out_dir=args.out,
            top=args.top,
            dry_run=not args.execute,
        )
        print(f"Report written to: {Path(ctx.out_dir / 'debug_report.md')}")
        return 0

    if args.command == "demo":
        repo_root = Path(__file__).resolve().parents[2]
        demo_root = repo_root / "examples" / "demo_project"
        graph = DebugGraph(settings=settings)
        ctx = graph.run(project_root=demo_root, out_dir=args.out, top="top_lvds_rx", dry_run=True)
        print(f"Demo report written to: {Path(ctx.out_dir / 'debug_report.md')}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
