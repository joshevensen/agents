#!/usr/bin/env python3
"""Structural lint for the orc plugin — catches the class of bug that only
shows up at runtime in prose-driven skills: a renamed agent no skill was
updated to match, a template path that doesn't exist, a version bump that
was forgotten. Exits non-zero on any failure.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ORC_ROOT = REPO_ROOT / "plugins" / "orc"
VALID_MODELS = {"haiku", "sonnet", "opus"}

errors = []
warnings = []


def fail(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def parse_frontmatter(path):
    text = path.read_text()
    if not text.startswith("---\n"):
        fail(f"{path}: missing frontmatter (must start with '---')")
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        fail(f"{path}: frontmatter never closes with '---'")
        return {}
    block = text[4:end]
    fields = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            fail(f"{path}: malformed frontmatter line: {line!r}")
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def check_frontmatter_files(paths, kind):
    for path in paths:
        fields = parse_frontmatter(path)
        for required in ("name", "description", "model"):
            if not fields.get(required):
                fail(f"{path}: missing or empty '{required}' in frontmatter")
        model = fields.get("model")
        if model and model not in VALID_MODELS:
            fail(f"{path}: model '{model}' is not one of {sorted(VALID_MODELS)}")
        expected_name = path.stem if kind == "agent" else path.parent.name
        if fields.get("name") and fields["name"] != expected_name:
            fail(
                f"{path}: frontmatter name '{fields['name']}' doesn't match "
                f"{'filename' if kind == 'agent' else 'directory'} '{expected_name}'"
            )


def check_plugin_root_paths(paths):
    pattern = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s`)\"']+)")
    for path in paths:
        text = path.read_text()
        for match in pattern.finditer(text):
            rel = match.group(1)
            target = ORC_ROOT / rel
            if not target.exists():
                fail(f"{path}: references nonexistent path ${{CLAUDE_PLUGIN_ROOT}}/{rel}")


def check_agent_references(skill_paths, agent_paths):
    defined = {parse_frontmatter(p).get("name") for p in agent_paths}
    defined.discard(None)

    invoke_pattern = re.compile(r"[Ii]nvoke(?:\s+the)?\s+`([a-z][a-z0-9-]*)`")
    bullet_pattern = re.compile(r"^-\s+`([a-z][a-z0-9-]*)`\s+[—-]", re.MULTILINE)

    referenced = set()
    for path in skill_paths:
        text = path.read_text()
        for pattern in (invoke_pattern, bullet_pattern):
            for match in pattern.finditer(text):
                name = match.group(1)
                referenced.add(name)
                if name not in defined:
                    fail(f"{path}: references undefined agent `{name}`")

    for name in sorted(defined - referenced):
        warn(f"agent '{name}' is defined but never referenced by any skill")


def check_version_changelog_sync():
    plugin_json = ORC_ROOT / ".claude-plugin" / "plugin.json"
    changelog = ORC_ROOT / "CHANGELOG.md"

    version_match = re.search(r'"version"\s*:\s*"([^"]+)"', plugin_json.read_text())
    if not version_match:
        fail(f"{plugin_json}: no 'version' field found")
        return
    version = version_match.group(1)

    changelog_text = changelog.read_text()
    if f"## [{version}]" not in changelog_text:
        fail(
            f"{plugin_json}: version '{version}' has no matching "
            f"'## [{version}]' heading in {changelog}"
        )

    base_ref = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--verify", "origin/main"],
        capture_output=True, text=True,
    )
    if base_ref.returncode != 0:
        warn("no origin/main ref available — skipping version-bump-on-change check")
        return

    diff = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--name-only", "origin/main...HEAD", "--", "plugins/orc"],
        capture_output=True, text=True,
    )
    changed_files = [f for f in diff.stdout.splitlines() if f]
    if not changed_files:
        return

    plugin_json_rel = str(plugin_json.relative_to(REPO_ROOT))
    if plugin_json_rel not in changed_files:
        fail(
            "plugins/orc/** changed in this branch but "
            f"{plugin_json_rel}'s version wasn't bumped — installed copies "
            "won't receive this change. Bump 'version' and add a matching "
            "CHANGELOG.md entry."
        )


def main():
    skill_paths = sorted((ORC_ROOT / "skills").glob("*/SKILL.md"))
    agent_paths = sorted((ORC_ROOT / "agents").glob("*.md"))

    if not skill_paths:
        fail(f"no SKILL.md files found under {ORC_ROOT / 'skills'}")
    if not agent_paths:
        fail(f"no agent files found under {ORC_ROOT / 'agents'}")

    check_frontmatter_files(skill_paths, "skill")
    check_frontmatter_files(agent_paths, "agent")
    check_plugin_root_paths(skill_paths + agent_paths)
    check_agent_references(skill_paths, agent_paths)
    check_version_changelog_sync()

    for w in warnings:
        print(f"::warning::{w}")
    for e in errors:
        print(f"::error::{e}")

    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
