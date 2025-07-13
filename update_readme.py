import os
import subprocess
import yaml
import re
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


def parse_frontmatter_and_heading(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    metadata = {}
    content_start = 0

    # Parse YAML frontmatter
    if lines and lines[0].strip() == "---":
        try:
            end_idx = lines[1:].index("---\n") + 1
            yaml_block = "".join(lines[1:end_idx])
            metadata = yaml.safe_load(yaml_block) or {}
            content_start = end_idx + 1
        except (ValueError, yaml.YAMLError):
            pass

    # Find first heading after frontmatter
    heading = None
    for line in lines[content_start:]:
        if line.strip().startswith("#"):
            heading = line.strip().lstrip("#").strip()
            break

    return metadata, heading


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s]+", "-", text)


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
    lines.append("# Blog\n")
    lines.append("_Just some thoughts._\n")

    # Emoji mapping for categories (customize as needed)
    category_emojis = {
        "dev": "💻",
        "music": "🎵",
    }

    for category, files in sorted(categories.items()):
        emoji = category_emojis.get(category.lower(), "📂")
        lines.append(f"## {emoji} {category.capitalize()}")

        # Sort files by date from frontmatter
        files_with_dates = []
        files_without_dates = []

        for file in files:
            metadata, heading = parse_frontmatter_and_heading(file)
            date_str = metadata.get("date")

            if date_str:
                try:
                    # Try to parse the date
                    if isinstance(date_str, str):
                        # Handle various date formats
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    else:
                        # If it's already a datetime object
                        date_obj = date_str
                    files_with_dates.append((date_obj, file))
                except (ValueError, TypeError):
                    # If date parsing fails, treat as no date
                    files_without_dates.append(file)
            else:
                files_without_dates.append(file)

        # Sort files with dates by date (newest first)
        files_with_dates.sort(key=lambda x: x[0], reverse=True)

        # Combine sorted files with dates and files without dates (alphabetically sorted)
        sorted_files = [file for date, file in files_with_dates] + sorted(
            files_without_dates
        )

        for file in sorted_files:
            rel_path = Path(file)
            metadata, heading = parse_frontmatter_and_heading(file)

            title = (
                metadata.get("title")
                or rel_path.stem.replace("-", " ").replace("_", " ").capitalize()
            )
            description = metadata.get("description", "")
            anchor = f"#{slugify(heading)}" if heading else ""
            link = f"{rel_path.as_posix()}{anchor}"
            updated = get_git_last_modified(file)

            # Bold for title, italics for description
            lines.append(f"- [**{title}**]({link})")
            if description:
                lines.append(f"  _{description}_  ")
            lines.append(f"  <sub>Last updated: {updated}</sub>")
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
