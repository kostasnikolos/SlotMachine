"""Turn a prompt manifest into a copy-paste pack for the Gemini app (free route, no API billing).

Each job becomes one ready-to-paste prompt. Save every result into
generated/inbox/<manifest-name>/ named <job-id>_<n>.png (or .jpg/.webp), then run designer_pass.py on that folder.

Usage:
    python scripts/ai/prompt_pack.py scripts/ai/prompts/p1_backdrop_frame.json
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    path = Path(sys.argv[1])
    m = json.loads(path.read_text(encoding="utf-8"))
    name = path.stem
    inbox = REPO / "generated" / "inbox" / name
    inbox.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Prompt pack — {name}",
        "",
        "Free route: paste each prompt into the Gemini app (gemini.google.com) with image generation.",
        f"Save results to `generated/inbox/{name}/` as `<job-id>_<n>.png`. Make 2–4 per job.",
        "",
        "**Consistency:** once one image looks right, attach it to the following prompts and add",
        "\"Match the painting style, palette and lighting of the attached image.\"",
        "",
    ]
    for job in m["jobs"]:
        aspect = job.get("aspect", "1:1")
        prompt = "\n\n".join(p for p in (m.get("style", ""), job["prompt"], m.get("negative", "")) if p)
        lines += [f"## {job['id']}  ({aspect})", "", "```text", f"Aspect ratio {aspect}. {prompt}", "```", ""]

    out = REPO / "docs" / "prompt_packs" / f"{name}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{out.relative_to(REPO)}  ({len(m['jobs'])} prompts) -> save images to {inbox.relative_to(REPO)}")


if __name__ == "__main__":
    main()
