#!/usr/bin/env python3
"""scrivener - Markdown to PDF converter.

Uses ReportLab, mistune v3, and variable fonts to produce
beautifully formatted PDFs from Markdown files with YAML front
matter. Styling is fully externalized into style YAML files.

Usage:
    python scrivener.py doc.md                  # -> .out/doc.pdf
    python scrivener.py doc.md -o out.pdf       # explicit output
    python scrivener.py *.md                    # batch mode -> .out/
    python scrivener.py doc.md --style wg21     # named style
    python scrivener.py --list-styles           # JSON style catalog
    python scrivener.py doc.md --options '{"toc": true}'
"""

import argparse
import glob as globmod
import json
import sys
from pathlib import Path

from lib.builder import build_pdf
from lib.catalog import list_styles
from lib.config import (
    PROJECT_ROOT,
    apply_options,
    load_style,
    resolve_style_path,
)


def main():
    parser = argparse.ArgumentParser(
        prog="scrivener",
        description="Convert Markdown files to beautifully formatted PDFs.",
        epilog="For the web UI, run 'python paperworks.py serve' from the paperworks directory.")

    parser.add_argument(
        "input", nargs="*",
        help="Markdown file(s) or glob patterns to convert")
    parser.add_argument(
        "-o", "--output",
        help="Output PDF path (single-file mode only)")
    parser.add_argument(
        "--outdir",
        help="Output directory for batch mode (default: .out/)")
    parser.add_argument(
        "--style",
        help="Style name (from styles/) or path to a style directory")
    parser.add_argument(
        "--logo",
        help="Override the logo image path")
    toc_group = parser.add_mutually_exclusive_group()
    toc_group.add_argument(
        "--toc", action="store_true", default=None,
        help="Force table of contents on")
    toc_group.add_argument(
        "--no-toc", action="store_true", default=None,
        help="Force table of contents off")
    parser.add_argument(
        "--options",
        help="JSON string or path to JSON file with option overrides")
    parser.add_argument(
        "--list-styles", action="store_true",
        help="List available styles as JSON and exit")

    args = parser.parse_args()

    if args.list_styles:
        styles = list_styles()
        print(json.dumps(styles, indent=2))
        sys.exit(0)

    if not args.input:
        parser.print_help()
        sys.exit(0)

    style_path = resolve_style_path(args.style)
    style = load_style(style_path)

    if args.options:
        opt_path = Path(args.options)
        if opt_path.is_file():
            with open(opt_path, encoding="utf-8") as f:
                options_dict = json.load(f)
        else:
            options_dict = json.loads(args.options)
        apply_options(style, options_dict)

    md_files = []
    for pattern in args.input:
        expanded = globmod.glob(pattern, recursive=True)
        if expanded:
            md_files.extend(expanded)
        else:
            md_files.append(pattern)
    md_files = [Path(f) for f in md_files]

    if args.output and len(md_files) > 1:
        parser.error("-o/--output cannot be used with multiple input files")

    default_outdir = PROJECT_ROOT / ".out"

    if len(md_files) == 1 and args.output:
        outputs = [Path(args.output)]
    elif args.outdir:
        outdir = Path(args.outdir)
        outputs = [outdir / f.with_suffix(".pdf").name for f in md_files]
    else:
        outputs = [default_outdir / f.with_suffix(".pdf").name
                    for f in md_files]

    cli_cfg = {}
    if args.logo:
        cli_cfg["logo"] = args.logo
    if args.toc:
        cli_cfg["toc"] = True
    if args.no_toc:
        cli_cfg["no_toc"] = True

    successes = []
    failures = []

    for md_file, out_file in zip(md_files, outputs):
        try:
            result = build_pdf(md_file, out_file, cli_cfg, style)
            print(f"  ok: {md_file} -> {result}")
            successes.append(md_file)
        except Exception as e:
            import traceback
            print(f"FAIL: {md_file} -- {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            failures.append((md_file, e))

    if len(md_files) > 1:
        print(f"\n{len(successes)} succeeded, {len(failures)} failed")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
