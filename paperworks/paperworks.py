#!/usr/bin/env python3
"""paperworks - WG21 paper management dashboard.

Orchestrates scrivener (markdown -> PDF) and docketeer (isocpp.org
client) into a unified web UI for managing paper inventory, rendering,
uploading, and status transitions.

Usage:
    python paperworks.py serve                    # start web UI
    python paperworks.py serve --port 8080        # custom port
"""

import argparse
import sys
from pathlib import Path


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "serve":
        serve_parser = argparse.ArgumentParser(prog="paperworks serve")
        serve_parser.add_argument("--port", type=int, default=None)
        serve_args = serve_parser.parse_args(sys.argv[2:])

        from lib.server import run_server
        from lib.server_config import load_config, save_config

        cfg = load_config()
        if serve_args.port is not None:
            cfg["port"] = serve_args.port
            save_config(cfg)
        run_server(cfg)
        return

    parser = argparse.ArgumentParser(
        prog="paperworks",
        description="WG21 paper management dashboard.",
        epilog="Run 'paperworks serve' to start the web UI.")

    parser.add_argument(
        "command", nargs="?", choices=["serve"],
        help="Command to run (currently only 'serve')")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
