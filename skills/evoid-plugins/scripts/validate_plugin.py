#!/usr/bin/env python3
"""Validate an EVOID plugin implementation against contracts."""
import ast
import sys
from pathlib import Path


def check_file(path: Path) -> list[str]:
    errors = []
    source = path.read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        methods = {m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}

        # Check StorageEngine contract
        required_storage = {"write", "read", "delete", "health"}
        if required_storage.issubset(methods):
            missing = {"write", "read", "delete", "health"} - methods
            if missing:
                errors.append(f"{path}:{node.lineno} class {node.name} claims storage but missing: {missing}")

        # Check CacheEngine contract
        required_cache = {"get", "set", "delete", "exists", "health"}
        if required_cache.issubset(methods):
            missing = required_cache - methods
            if missing:
                errors.append(f"{path}:{node.lineno} class {node.name} claims cache but missing: {missing}")

        # Check LoggerEngine contract
        required_logger = {"info", "warning", "error", "debug"}
        if required_logger.issubset(methods):
            missing = required_logger - methods
            if missing:
                errors.append(f"{path}:{node.lineno} class {node.name} claims logger but missing: {missing}")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_plugin.py <path-to-plugin-dir-or-file>")
        sys.exit(1)

    target = Path(sys.argv[1])
    files = list(target.rglob("*.py")) if target.is_dir() else [target]

    all_errors = []
    for f in files:
        all_errors.extend(check_file(f))

    if all_errors:
        print("Issues found:")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("All contract checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
