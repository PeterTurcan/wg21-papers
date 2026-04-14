#!/usr/bin/env python3
"""tomd - Convert PDF files to Markdown.

Hybrid converter using dual extraction (MuPDF + spatial rules),
multi-signal confidence scoring, and companion prompt files for
ambiguous regions.

Usage:
    python tomd/main.py input.pdf                  # -> input.md + input.prompts.md
    python tomd/main.py input.pdf -o output.md     # -> output.md + output.prompts.md
    python tomd/main.py *.pdf --outdir converted/  # batch mode
"""

import argparse
import glob as globmod
import sys
from pathlib import Path

from lib.pdf import convert_pdf


def main():
    parser = argparse.ArgumentParser(
        prog="tomd",
        description="Convert PDF files to Markdown with confidence scoring.",
    )
    parser.add_argument(
        "input", nargs="*",
        help="PDF file(s) or glob patterns to convert")
    parser.add_argument(
        "-o", "--output",
        help="Output Markdown path (single-file mode only)")
    parser.add_argument(
        "--outdir",
        help="Output directory for batch mode")
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug logging")

    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG,
                            format="%(name)s: %(message)s")

    if not args.input:
        parser.print_help()
        sys.exit(0)

    pdf_files = []
    for pattern in args.input:
        expanded = globmod.glob(pattern, recursive=True)
        if expanded:
            pdf_files.extend(expanded)
        else:
            pdf_files.append(pattern)
    pdf_files = [Path(f) for f in pdf_files]

    if args.output and len(pdf_files) > 1:
        parser.error("-o/--output cannot be used with multiple input files")

    successes = []
    failures = []

    for pdf_file in pdf_files:
        if not pdf_file.exists():
            print(f"SKIP: {pdf_file} not found", file=sys.stderr)
            failures.append(pdf_file)
            continue

        if args.output and len(pdf_files) == 1:
            md_path = Path(args.output)
        elif args.outdir:
            md_path = Path(args.outdir) / pdf_file.with_suffix(".md").name
        else:
            md_path = pdf_file.with_suffix(".md")

        prompts_path = md_path.with_suffix(".prompts.md")

        try:
            md_text, prompts_text = convert_pdf(pdf_file)

            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(md_text, encoding="utf-8")

            if prompts_text:
                prompts_path.write_text(prompts_text, encoding="utf-8")
                print(f"  ok: {pdf_file} -> {md_path} + {prompts_path}")
            else:
                print(f"  ok: {pdf_file} -> {md_path}")

            successes.append(pdf_file)
        except Exception as e:
            print(f"FAIL: {pdf_file} -- {e}", file=sys.stderr)
            failures.append(pdf_file)

    if len(pdf_files) > 1:
        print(f"\n{len(successes)} succeeded, {len(failures)} failed")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
