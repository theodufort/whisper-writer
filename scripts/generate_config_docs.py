"""Generate docs/configuration.md from src/config_schema.yaml (the single source of truth).

Usage:  uv run python scripts/generate_config_docs.py

Re-run it whenever a setting is added or changed in the schema.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "src" / "config_schema.yaml"
OUTPUT = ROOT / "docs" / "configuration.md"

INTRO = """\
# Configuration reference

> This file is generated from [`src/config_schema.yaml`](../src/config_schema.yaml) by
> `scripts/generate_config_docs.py`. Do not edit it by hand.

All settings can be changed in the app (**Settings** window) and are stored in `config.yaml`:

* running from source: `src/config.yaml`
* the packaged app: `config.yaml` next to `whisper-writer.exe`

`config.yaml` is created the first time you save settings. Any setting missing from it uses the
default listed below, so the file may contain only the values you changed. It is ignored by git.
"""

SECTION_NOTES = {
    "model_options": "Which speech-to-text engine to use and how it behaves.",
    "post_processing": "What happens to the text after it has been transcribed.",
    "recording_options": "How recording is started and stopped.",
    "misc": "Everything else.",
}


def fmt_default(value) -> str:
    if value is None:
        return "*(empty)*"
    if isinstance(value, bool):
        return "`true`" if value else "`false`"
    return f"`{value}`"


def walk(node: dict, path: tuple[str, ...]):
    """Yield (path, meta) for every setting; a setting is a mapping that has a 'value' key."""
    for key, child in node.items():
        if isinstance(child, dict) and "value" in child:
            yield path + (key,), child
        elif isinstance(child, dict):
            yield from walk(child, path + (key,))


def main() -> None:
    schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    out = [INTRO]
    for section, body in schema.items():
        out.append(f"\n## `{section}`\n")
        if section in SECTION_NOTES:
            out.append(f"{SECTION_NOTES[section]}\n")
        out.append(f"Setting names are paths inside the `{section}:` section of `config.yaml`.\n")
        out.append("| Setting | Default | Description |")
        out.append("|---|---|---|")
        for path, meta in walk(body, ()):
            name = ".".join(path)
            desc = str(meta.get("description", "")).replace("|", "\\|")
            options = meta.get("options")
            if options:
                desc += " Options: " + ", ".join(f"`{o}`" for o in options) + "."
            out.append(f"| `{name}` | {fmt_default(meta['value'])} | {desc} |")
        out.append("")
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
