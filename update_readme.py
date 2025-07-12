import os
import subprocess
from datetime import datetime
from pathlib import Path

ARTICLES_DIR = "articles"
README_PATH = "README.md"


def get_markdown_files():
    md_files = []
    for root, dirs, files in os.walk(ARTICLES_DIR):
        for file in files:
            if file.endswith(".md") and not file.startswith("_"):
                full_path = os.path.join(root, file)
                md_files.append(full_path)
    return md_files


def get_git_last_modified(filepath):
    try:
        output = subprocess.check_output(
            ["git", "log", "-1", "--format=%ad", "--date=short", filepath],
            stderr=subprocess.DEVNULL,
        )
        return output.decode().strip()
    except subprocess.CalledProcessError:
        return "Unknown"


def group_by_category(files):
    categories = {}
    for file in files:
        rel_path = Path(file)
        parts = rel_path.parts
        if len(parts) < 2:
            continue
        category = parts[1]
        categories.setdefault(category, []).append(file)
    return categories


def build_readme(categories):
    lines = []
    lines.append("# NotaBlog\n")
    lines.append("_Auto-generated on merge to main._\n")

    for category, files in sorted(categories.items()):
        lines.append(f"## {category.capitalize()}")
        for file in sorted(files):
            rel_path = Path(file)
            name = rel_path.stem.replace("-", " ").replace("_", " ").capitalize()
            link = rel_path.as_posix()
            last_updated = get_git_last_modified(file)
            lines.append(f"- [{name}]({link}) - _Last updated: {last_updated}_")
        lines.append("")  # newline between categories

    return "\n".join(lines)


def main():
    md_files = get_markdown_files()
    grouped = group_by_category(md_files)
    readme_content = build_readme(grouped)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"✅ {README_PATH} updated with {len(md_files)} articles.")


if __name__ == "__main__":
    main()
