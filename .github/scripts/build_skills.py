#!/usr/bin/env python3
"""
Build script for Claude Skills.

This script:
1. Discovers all skill folders (those containing SKILL.md)
2. Extracts skill metadata from SKILL.md YAML preambles
3. Creates zip archives for each skill in the root directory
4. Generates an updated README.md with skill listings
"""

import os
import sys
import re
import shutil
from pathlib import Path
from typing import Optional, Dict, List


def extract_yaml_preamble(skill_md_path: Path) -> Dict[str, str]:
    """Extract YAML preamble from SKILL.md file."""
    with open(skill_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match YAML preamble between --- markers
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    yaml_content = match.group(1)
    metadata = {}

    # Parse YAML key-value pairs
    for line in yaml_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Simple YAML parsing for key: value format
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            metadata[key] = value

    return metadata


def find_skills(root_dir: Path) -> List[Dict[str, any]]:
    """Find all skill folders and extract their metadata."""
    skills = []

    # Iterate through immediate subdirectories of root
    for entry in os.listdir(root_dir):
        skill_path = root_dir / entry

        # Skip non-directories and hidden directories
        if not os.path.isdir(skill_path) or entry.startswith('.'):
            continue

        # Skip common directories
        if entry in ['__pycache__', '.git', 'venv', 'env']:
            continue

        skill_md = skill_path / 'SKILL.md'
        if not skill_md.exists():
            continue

        # Extract metadata from SKILL.md
        metadata = extract_yaml_preamble(skill_md)

        if 'name' not in metadata:
            print(f"Warning: {skill_md} missing 'name' field", file=sys.stderr)
            continue

        skills.append({
            'name': metadata.get('name'),
            'description': metadata.get('description', ''),
            'path': skill_path,
        })

    # Sort by name for consistent ordering
    return sorted(skills, key=lambda s: s['name'])


def create_skill_zips(root_dir: Path, skills: List[Dict]):
    """Create zip archives for each skill in the root directory."""
    for skill in skills:
        zip_name = root_dir / f"{skill['name']}.zip"
        skill_path = skill['path']

        print(f"Creating {zip_name.name}...")

        # Remove existing zip if it exists
        if zip_name.exists():
            zip_name.unlink()

        # Create zip archive (without the parent directory)
        # shutil.make_archive creates the zip, we specify base_dir and root_dir
        # to control what gets included in the zip
        try:
            shutil.make_archive(
                str(zip_name.with_suffix('')),  # Output path without .zip
                'zip',
                root_dir=str(skill_path.parent),
                base_dir=skill_path.name
            )
            print(f"  Created: {zip_name.name}")
        except Exception as e:
            print(f"Error creating zip for {skill['name']}: {e}", file=sys.stderr)
            return False

    return True


def generate_readme(root_dir: Path, skills: List[Dict]) -> str:
    """Generate README.md content with skill listings."""
    lines = [
        "# Claude Skills\n",
        "A collection of Claude Code skills.\n",
        "## Available Skills\n",
    ]

    for skill in skills:
        lines.append(f"### {skill['name']}\n")
        if skill['description']:
            lines.append(f"{skill['description']}\n")
        lines.append(f"- **File**: `{skill['name']}.zip`\n")
        lines.append("")

    lines.append("## Installation\n")
    lines.append("Download any of the `.zip` files above to install a skill.\n")

    return "\n".join(lines)


def main():
    """Main entry point."""
    root_dir = Path(__file__).parent.parent.parent  # Go up to repo root

    print(f"Scanning for skills in {root_dir}...")

    # Find all skills
    skills = find_skills(root_dir)

    if not skills:
        print("No skills found. Nothing to do.")
        return

    print(f"Found {len(skills)} skill(s): {', '.join(s['name'] for s in skills)}")

    # Create zips
    print("\nCreating skill archives...")
    if not create_skill_zips(root_dir, skills):
        sys.exit(1)

    # Generate README
    print("\nGenerating README.md...")
    readme_content = generate_readme(root_dir, skills)
    readme_path = root_dir / 'README.md'
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"  Created: README.md")

    print("\nBuild complete!")


if __name__ == '__main__':
    main()
