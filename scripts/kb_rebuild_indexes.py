#!/usr/bin/env python3
"""
Knowledge Base Index Rebuilder

Scans all source files in knowledge-base/sources/, extracts structured
data, and regenerates JSON index files + updates README stats.

Usage:
    python scripts/kb_rebuild_indexes.py
    python scripts/kb_rebuild_indexes.py --dry-run    # Show what would change
"""

import json
import re
import sys
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

KB_ROOT = Path(__file__).parent.parent / "knowledge-base"
SOURCES_DIR = KB_ROOT / "sources"
INDEX_DIR = KB_ROOT / "indexes"
README_PATH = KB_ROOT / "README.md"


def extract_source_metadata(text: str, filename: str) -> dict:
    """Extract frontmatter-style metadata from source file header."""
    source_id_match = re.search(r"^# S(\d+):", text, re.MULTILINE)
    source_id = f"S{source_id_match.group(1)}" if source_id_match else filename[:3]

    title_match = re.search(r"^# S\d+:\s*(.+)", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Unknown"

    # Extract author
    author_match = re.search(r"\*\*(?:Source|Author)[:\s]*\*\*\s*(.+?)$", text, re.MULTILINE)
    author = author_match.group(1).strip() if author_match else "Unknown"

    # Extract date
    date_match = re.search(r"\*\*Date[:\s]*\*\*\s*(.+?)$", text, re.MULTILINE)
    date = date_match.group(1).strip() if date_match else "Unknown"

    # Extract type
    type_match = re.search(r"\*\*Type[:\s]*\*\*\s*(.+?)$", text, re.MULTILINE)
    source_type = type_match.group(1).strip() if type_match else "Unknown"

    # Extract credibility
    cred_match = re.search(
        r"\*\*(?:Credibility|Source Quality)[:\s]*\*\*\s*(\d+)",
        text,
        re.MULTILINE,
    )
    credibility = int(cred_match.group(1)) if cred_match else 0

    # Extract processed date
    proc_match = re.search(r"\*S\d+ processed:\s*(.+?)\*", text)
    processed = proc_match.group(1).strip() if proc_match else "Unknown"

    return {
        "id": source_id,
        "title": title,
        "author": author,
        "date": date,
        "type": source_type,
        "file": filename,
        "credibility": credibility,
        "processed": processed,
    }


def extract_items(text: str, source_id: str) -> list[dict]:
    """Extract items from markdown tables in source file."""
    items = []
    # Match table rows with item IDs like S1.01, S14.192, etc.
    pattern = re.compile(
        r"\|\s*(S\d+\.\d+)\s*\|"  # Item ID
        r"\s*\*\*(.+?)\*\*"  # Bold title
        r".*?\|"  # Rest until next pipe
        r"\s*(`[^|]+`)\s*\|"  # Tags in backticks
        r"\s*(\w+)\s*\|",  # Relevance
        re.DOTALL,
    )
    for match in pattern.finditer(text):
        item_id = match.group(1).strip()
        title = match.group(2).strip()
        tags_raw = match.group(3).strip()
        relevance = match.group(4).strip()

        tags = [t.strip().strip("`") for t in tags_raw.split("`") if t.strip()]

        items.append({
            "id": item_id,
            "summary": title[:120],
            "tags": tags,
            "relevance": relevance,
            "source_file": f"{source_id}",
        })

    # Fallback: count items by looking for the simpler pattern
    if not items:
        simple_pattern = re.compile(r"\|\s*(S\d+\.\d+)\s*\|")
        for match in simple_pattern.finditer(text):
            items.append({
                "id": match.group(1).strip(),
                "summary": "",
                "tags": [],
                "relevance": "UNKNOWN",
                "source_file": source_id,
            })

    return items


def extract_patterns(text: str) -> list[str]:
    """Extract pattern numbers referenced in source file."""
    pattern = re.compile(r"(?:Pattern |P)(\d+)")
    numbers = sorted(set(int(m.group(1)) for m in pattern.finditer(text)))
    return [f"P{n}" for n in numbers]


def extract_action_items(text: str, source_id: str) -> list[dict]:
    """Extract action items from source file."""
    actions = []
    # Look for action items in tables
    action_pattern = re.compile(
        r"\|\s*(\d+)\s*\|"  # Priority number
        r"\s*\*?\*?(.+?)\*?\*?\s*\|"  # Action description
        r"\s*(.+?)\s*\|",  # What to find out / status
        re.MULTILINE,
    )

    # Find the action items section
    action_section = re.search(
        r"(?:Action Items|Action Items for Investigation).*?(?=\n---|\n##|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if action_section:
        section_text = action_section.group(0)
        for match in action_pattern.finditer(section_text):
            actions.append({
                "source": source_id,
                "priority": match.group(1).strip(),
                "action": match.group(2).strip(),
                "detail": match.group(3).strip(),
            })

    return actions


def extract_tools(text: str) -> list[str]:
    """Extract tool/technology names mentioned in source file."""
    # Look for bold tool names in item descriptions
    tool_pattern = re.compile(r"\*\*([A-Z][a-zA-Z0-9/\-_.]+(?:\s[A-Z][a-zA-Z0-9]+)?)\*\*")
    tools = set()
    for match in tool_pattern.finditer(text):
        name = match.group(1).strip()
        # Filter out common non-tool matches
        if len(name) > 2 and name not in {
            "Source", "Type", "Date", "Key", "ATLAS", "Baby",
            "Pattern", "Theme", "Action", "Notes", "HIGH",
            "MEDIUM", "LOW", "NOISE", "Strengths", "Weaknesses",
            "Overall", "Credibility", "Translation", "WARNING",
        }:
            tools.add(name)
    return sorted(tools)


def build_category_index(all_data: list[dict]) -> dict:
    """Build index mapping category tags to items."""
    index = {"_meta": {"generated": datetime.now().isoformat(), "total_items": 0}}

    by_category = defaultdict(lambda: {"count": 0, "items": [], "patterns": set()})

    for source in all_data:
        for item in source.get("items", []):
            for tag in item.get("tags", []):
                tag_upper = tag.upper()
                by_category[tag_upper]["count"] += 1
                by_category[tag_upper]["items"].append({
                    "id": item["id"],
                    "summary": item["summary"],
                    "relevance": item["relevance"],
                    "source_file": item["source_file"],
                })
                index["_meta"]["total_items"] += 1

        for pattern in source.get("patterns", []):
            # Associate patterns with their source's primary tags
            for item in source.get("items", []):
                for tag in item.get("tags", []):
                    by_category[tag.upper()]["patterns"].add(pattern)

    # Convert sets to sorted lists for JSON
    for tag_data in by_category.values():
        tag_data["patterns"] = sorted(tag_data["patterns"])

    index.update(by_category)
    return index


def build_source_index(all_data: list[dict]) -> dict:
    """Build index mapping source IDs to metadata."""
    index = {
        "_meta": {
            "generated": datetime.now().isoformat(),
            "total_sources": len(all_data),
        }
    }

    for source in all_data:
        meta = source["metadata"]
        index[meta["id"]] = {
            "title": meta["title"],
            "author": meta["author"],
            "date": meta["date"],
            "type": meta["type"],
            "file": meta["file"],
            "item_count": len(source.get("items", [])),
            "patterns": source.get("patterns", []),
            "action_count": len(source.get("actions", [])),
            "credibility": meta["credibility"],
            "processed_date": meta["processed"],
        }

    return index


def build_tool_index(all_data: list[dict]) -> dict:
    """Build index mapping tool names to source references."""
    index = {"_meta": {"generated": datetime.now().isoformat()}}

    tool_sources = defaultdict(lambda: {"sources": set(), "items": []})

    for source in all_data:
        source_id = source["metadata"]["id"]
        for tool in source.get("tools", []):
            tool_sources[tool]["sources"].add(source_id)

    # Convert sets to sorted lists
    for tool, data in tool_sources.items():
        index[tool] = {
            "sources": sorted(data["sources"]),
            "item_count": len(data["sources"]),
        }

    return index


def update_readme_stats(all_data: list[dict], dry_run: bool = False) -> None:
    """Update the stats in README.md header."""
    if not README_PATH.exists():
        logger.warning("README.md not found, skipping stats update")
        return

    readme = README_PATH.read_text()

    total_sources = len(all_data)
    total_items = sum(len(s.get("items", [])) for s in all_data)
    total_patterns = len(
        set(p for s in all_data for p in s.get("patterns", []))
    )
    total_actions = sum(len(s.get("actions", [])) for s in all_data)
    today = datetime.now().strftime("%Y-%m-%d")

    # Update stats table values
    replacements = [
        (r"(\| Sources \|)\s*\d+.*?\|", f"| Sources | {total_sources} (S1-S{total_sources}) |"),
        (r"(\| Items \|)\s*\d+.*?\|", f"| Items | {total_items} |"),
        (r"(\| Last updated \|)\s*.*?\|", f"| Last updated | {today} |"),
    ]

    for pattern, replacement in replacements:
        readme = re.sub(pattern, replacement, readme)

    if dry_run:
        logger.info(
            f"Would update README: {total_sources} sources, "
            f"{total_items} items, {total_patterns} patterns"
        )
    else:
        README_PATH.write_text(readme)
        logger.info(f"Updated README stats: {total_sources} sources, {total_items} items")


def rebuild_all():
    """Main rebuild function."""
    source_files = sorted(SOURCES_DIR.glob("S*.md"))

    if not source_files:
        logger.error(f"No source files found in {SOURCES_DIR}")
        sys.exit(1)

    logger.info(f"Found {len(source_files)} source files")

    all_data = []
    for path in source_files:
        text = path.read_text()
        metadata = extract_source_metadata(text, path.name)
        items = extract_items(text, metadata["id"])
        patterns = extract_patterns(text)
        actions = extract_action_items(text, metadata["id"])
        tools = extract_tools(text)

        data = {
            "metadata": metadata,
            "items": items,
            "patterns": patterns,
            "actions": actions,
            "tools": tools,
        }
        all_data.append(data)
        logger.info(
            f"  {metadata['id']}: {len(items)} items, "
            f"{len(patterns)} patterns, {len(actions)} actions"
        )

    dry_run = "--dry-run" in sys.argv

    # Build indexes
    INDEX_DIR.mkdir(exist_ok=True)

    category_index = build_category_index(all_data)
    source_index = build_source_index(all_data)
    tool_index = build_tool_index(all_data)

    if not dry_run:
        (INDEX_DIR / "by_category.json").write_text(
            json.dumps(category_index, indent=2, default=str)
        )
        (INDEX_DIR / "by_source.json").write_text(
            json.dumps(source_index, indent=2, default=str)
        )
        (INDEX_DIR / "by_tool.json").write_text(
            json.dumps(tool_index, indent=2, default=str)
        )
        logger.info(f"Wrote 3 index files to {INDEX_DIR}")
    else:
        logger.info(
            f"[DRY RUN] Would write 3 index files. "
            f"Categories: {len(category_index) - 1}, "
            f"Sources: {len(source_index) - 1}, "
            f"Tools: {len(tool_index) - 1}"
        )

    # Update README stats
    update_readme_stats(all_data, dry_run=dry_run)

    # Summary
    total_items = sum(len(s.get("items", [])) for s in all_data)
    total_patterns = len(set(p for s in all_data for p in s.get("patterns", [])))
    total_actions = sum(len(s.get("actions", [])) for s in all_data)

    logger.info(
        f"\nRebuild complete: {len(all_data)} sources, "
        f"{total_items} items, {total_patterns} patterns, "
        f"{total_actions} actions"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    rebuild_all()
