#!/usr/bin/env python3
"""Install the self-contained provenote Codex skill into one project."""

import argparse
import filecmp
import os
import shutil
import sys
import tempfile
from pathlib import Path


def reject_symlink_parents(path):
    current = path
    while True:
        if current.is_symlink():
            raise ValueError(f"refusing symlink path: {current}")
        if current.parent == current:
            return
        current = current.parent


def resolve_macos_var_alias(path):
    """Resolve only macOS's system /var alias, not arbitrary user symlinks."""
    alias = Path("/var")
    target = Path("/private/var")
    if sys.platform != "darwin" or not alias.is_symlink() or alias.resolve() != target:
        return path
    try:
        return target / path.relative_to(alias)
    except ValueError:
        return path


def same_tree(left, right):
    left_entries = sorted(
        p.relative_to(left) for p in left.rglob("*") if not p.is_dir()
    )
    right_entries = sorted(
        p.relative_to(right) for p in right.rglob("*") if not p.is_dir()
    )
    return left_entries == right_entries and all(
        filecmp.cmp(left / item, right / item, shallow=False) for item in left_entries
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project",
        required=True,
        help="project directory receiving .agents/skills/provenote",
    )
    args = parser.parse_args()
    supplied_project = resolve_macos_var_alias(Path(args.project).absolute())
    try:
        reject_symlink_parents(supplied_project)
    except ValueError as error:
        parser.error(str(error))
    project = supplied_project.resolve()
    if not project.is_dir():
        parser.error(f"project is not a directory: {project}")
    destination = project / ".agents" / "skills" / "provenote"
    for path in (project, project / ".agents", project / ".agents/skills", destination):
        try:
            reject_symlink_parents(path)
        except ValueError as error:
            print(f"install-codex: {error}", file=sys.stderr)
            return 2
        if path.is_symlink():
            print(
                f"install-codex: refusing symlink destination: {path}", file=sys.stderr
            )
            return 2
    root = Path(__file__).resolve().parent.parent
    kit = root / "plugins/provenote"
    with tempfile.TemporaryDirectory(dir=project) as temp:
        staged = Path(temp) / "provenote"
        staged.mkdir()
        shutil.copy2(root / "docs/codex/SKILL.md", staged / "SKILL.md")
        for name in ("bin", "templates", "agents"):
            shutil.copytree(
                kit / name, staged / name, ignore=shutil.ignore_patterns("__pycache__")
            )
        shutil.copytree(kit / "skills", staged / "workflows")
        if destination.exists():
            if destination.is_dir() and same_tree(staged, destination):
                print(f"install-codex: already installed: {destination}")
                return 0
            print(
                f"install-codex: refusing differing destination: {destination}",
                file=sys.stderr,
            )
            return 2
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(staged, destination)
    print(f"install-codex: installed: {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
