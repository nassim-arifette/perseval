#!/usr/bin/env python3
"""
Generate a single text snapshot of the repository that contains the directory
tree and the content of every relevant file (i.e., anything not ignored by
.gitignore and common "useless" locations such as virtual environments).

Usage:
    python dump_project.py [--output path/to/output.txt]

The script writes the project tree at the top of the output followed by
sections for each file in the format:

    relative/path/to/file.ext
    <file content>
    ====
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

USELESS_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".ruff_cache",
    ".scannerwork",
}

USELESS_FILE_NAMES = {
    ".DS_Store",
    "Thumbs.db",
}

USELESS_FILE_GLOBS = {
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.swp",
    "*.swo",
    "*.tmp",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write a project snapshot (tree + file contents) to a text file."
    )
    parser.add_argument(
        "-o",
        "--output",
        default="project_dump.txt",
        help="Path to the output text file (default: project_dump.txt)",
    )
    return parser.parse_args()


def run_git_command(root: Path, args: List[str]) -> List[Path]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    data = completed.stdout.decode("utf-8", errors="replace")
    paths = [Path(p) for p in data.split("\0") if p]
    return paths


def gather_files(root: Path, output_relative: Optional[Path]) -> List[Path]:
    git_paths = set(run_git_command(root, ["ls-files", "-z"]))
    git_paths.update(run_git_command(root, ["ls-files", "--others", "--exclude-standard", "-z"]))

    if git_paths:
        candidates = [root / rel for rel in git_paths]
    else:
        # Fallback: manual walk respecting the known useless directories.
        candidates = []
        for dirpath, dirnames, filenames in os.walk(root):
            rel_dir = Path(dirpath).relative_to(root)
            dirnames[:] = [
                d for d in dirnames if not _should_skip_directory((rel_dir / d).parts)
            ]
            for filename in filenames:
                rel_file = (rel_dir / filename) if rel_dir.parts else Path(filename)
                candidates.append(root / rel_file)

    result = []
    for path in candidates:
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if _should_skip(relative, output_relative):
            continue
        result.append(path)

    result.sort(key=lambda p: p.relative_to(root).as_posix().lower())
    return result


def _should_skip(relative: Path, output_relative: Optional[Path]) -> bool:
    if output_relative and relative == output_relative:
        return True

    parts = relative.parts
    if len(parts) > 1 and _should_skip_directory(parts[:-1]):
        return True

    name = parts[-1] if parts else ""
    if name in USELESS_FILE_NAMES:
        return True
    if any(fnmatch.fnmatch(name, pattern) for pattern in USELESS_FILE_GLOBS):
        return True

    return False


def _should_skip_directory(parts: Iterable[str]) -> bool:
    return any(part in USELESS_DIR_NAMES for part in parts)


def build_tree_lines(root_name: str, files: List[Path]) -> List[str]:
    tree: Dict[str, Dict] = {}
    for rel in files:
        node = tree
        for idx, part in enumerate(rel.parts):
            is_file = idx == len(rel.parts) - 1
            if is_file:
                node.setdefault(part, None)
            else:
                node = node.setdefault(part, {})

    lines = [f"{root_name}/"]
    children = sorted(tree.items(), key=_tree_sort_key)
    for idx, (name, child) in enumerate(children):
        lines.extend(_render_tree_node(name, child, "", idx == len(children) - 1))
    return lines


def _tree_sort_key(item: Tuple[str, Optional[Dict]]) -> Tuple[int, str]:
    name, node = item
    is_dir = isinstance(node, dict)
    return (0 if is_dir else 1, name.lower())


def _render_tree_node(
    name: str,
    node: Optional[Dict],
    prefix: str,
    is_last: bool,
) -> List[str]:
    connector = "`-- " if is_last else "|-- "
    display_name = f"{name}/" if isinstance(node, dict) else name
    line = f"{prefix}{connector}{display_name}"
    lines = [line]

    if isinstance(node, dict):
        child_prefix = f"{prefix}{'    ' if is_last else '|   '}"
        children = sorted(node.items(), key=_tree_sort_key)
        for idx, (child_name, child_node) in enumerate(children):
            lines.extend(
                _render_tree_node(
                    child_name,
                    child_node,
                    child_prefix,
                    idx == len(children) - 1,
                )
            )
    return lines


def write_snapshot(root: Path, files: List[Path], output_path: Path) -> None:
    relative_files = [path.relative_to(root) for path in files]
    tree_lines = build_tree_lines(root.name, relative_files)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(tree_lines))
        handle.write("\n\n")

        for index, path in enumerate(files):
            relative = path.relative_to(root).as_posix()
            handle.write(f"{relative}\n")
            with path.open("r", encoding="utf-8", errors="replace") as source:
                contents = source.read()
            handle.write(contents)
            if contents and not contents.endswith("\n"):
                handle.write("\n")
            if index < len(files) - 1:
                handle.write("\n====\n\n")


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parent

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = root / output_path

    try:
        output_relative = output_path.relative_to(root)
    except ValueError:
        output_relative = None

    files = gather_files(root, output_relative)
    if not files:
        print("No files found to include in the snapshot.", file=sys.stderr)
        sys.exit(1)

    write_snapshot(root, files, output_path)
    print(f"Wrote {len(files)} files to {output_path}")


if __name__ == "__main__":
    main()
