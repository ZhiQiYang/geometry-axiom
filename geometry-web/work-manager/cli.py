#!/usr/bin/env python3
"""Geometry work manager CLI. Commands print JSON and never write to GitHub."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys

from store import MAX_INPUT_BYTES, Store, ValidationError, atomic_write_json


def read_json(path):
    with open(path, "rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValidationError("input exceeds 8 MiB")
    return json.loads(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Geometry 工作管理：私有資料、證據與交付分離")
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent / ".local")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("import-snapshot", "record-assignment", "record-result", "export", "restore"):
        command = commands.add_parser(name)
        command.add_argument("file", type=Path)
    for name in ("reconcile", "list-alerts"):
        commands.add_parser(name)
    ready_parser = commands.add_parser("list-ready")
    ready_parser.add_argument("--mode", choices=["all", "read_only", "write"], default="all")
    inspect_parser = commands.add_parser("inspect")
    inspect_parser.add_argument("task_id", nargs="?")
    server_parser = commands.add_parser("serve")
    server_parser.add_argument("--port", type=int, default=8765)
    server_parser.add_argument("--host", choices=["127.0.0.1", "localhost"], default="127.0.0.1")
    args = parser.parse_args(argv)
    try:
        if args.command == "serve":
            from server import serve
            serve(args.data_dir, host=args.host, port=args.port)
            return 0
        store = Store(args.data_dir)
        if args.command == "import-snapshot":
            result = store.import_snapshot(read_json(args.file))
        elif args.command == "record-assignment":
            result = store.record_assignment(read_json(args.file))
        elif args.command == "record-result":
            result = store.record_result(read_json(args.file))
        elif args.command == "restore":
            result = store.restore(read_json(args.file))
        elif args.command == "export":
            exported = store.export_snapshot()
            atomic_write_json(args.file, exported)
            result = {"exported": True, "checksum": exported["checksum"],
                      "state_hash": store.reconcile()["state_hash"],
                      "snapshot_count": len(exported["snapshots"])}
        else:
            state = store.reconcile()
            if args.command == "list-ready":
                result = {key: state[key] for key in ("state_hash", "payload_hash", "last_synced_at",
                          "ready", "ready_read_only", "ready_write", "ready_counts")}
                result["mode"] = args.mode
                if args.mode != "all":
                    result["ready"] = state["ready_" + args.mode]
            elif args.command == "list-alerts":
                result = {key: state[key] for key in ("state_hash", "last_synced_at", "alerts")}
            elif args.command == "inspect" and args.task_id:
                task = next((task for task in state["tasks"] if task["id"] == args.task_id), None)
                if task is None:
                    raise ValidationError("task_id not found")
                result = {"state_hash": state["state_hash"], "task": task}
            else:
                result = state
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ValidationError, ValueError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
