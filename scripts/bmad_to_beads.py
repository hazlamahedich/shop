#!/usr/bin/env python3
"""
BMad to Beads Converter

Converts BMad Method sprint-status.yaml into Beads tasks.
This bridges the gap between BMad planning and Beads execution.

Usage:
    python scripts/bmad_to_beads.py              # Show what would be created
    python scripts/bmad_to_beads.py --dry-run    # Same as above (explicit)
    python scripts/bmad_to_beads.py --create     # Actually create Beads tasks
    python scripts/bmad_to_beads.py --sync       # Sync status changes from BMad to Beads
    python scripts/bmad_to_beads.py --epic 1     # Only process specific epic
    python scripts/bmad_to_beads.py --status backlog  # Only stories with specific status
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

# ANSI colors for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# BMad status to Beads status mapping
BMAD_TO_BEADS_STATUS = {
    'backlog': 'todo',
    'ready-for-dev': 'todo',
    'in-progress': 'in_progress',
    'review': 'in_progress',
    'done': 'done',
    'optional': 'todo'
}

# Priority mapping based on story patterns
PRIORITY_PATTERNS = {
    'critical': ['prerequisite', 'critical', 'security', 'auth'],
    'high': ['deployment', 'connection', 'core', 'essential'],
    'medium': ['feature', 'integration', 'configuration'],
    'low': ['optional', 'enhancement', 'nice-to-have']
}


class BMadParser:
    """Parse BMad sprint-status.yaml and story files"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.bmad_output = project_root / "_bmad-output"
        self.implementation_artifacts = self.bmad_output / "implementation-artifacts"
        self.sprint_status_file = self.implementation_artifacts / "sprint-status.yaml"

    def parse_sprint_status(self) -> Dict:
        """Parse the sprint-status.yaml file"""
        if not self.sprint_status_file.exists():
            print(f"{Colors.FAIL}Error: sprint-status.yaml not found at {self.sprint_status_file}{Colors.ENDC}")
            sys.exit(1)

        with open(self.sprint_status_file, 'r') as f:
            content = f.read()

        return self._parse_yaml_content(content)

    def _parse_yaml_content(self, content: str) -> Dict:
        """Simple YAML parser for sprint-status format"""
        result = {
            'epics': {},
            'stories': {},
            'metadata': {}
        }

        current_section = None
        epic_name = None

        for line in content.split('\n'):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                if 'generated:' in line:
                    result['metadata']['generated'] = line.split(':')[1].strip()
                if 'project:' in line and 'project_key' not in line:
                    result['metadata']['project'] = line.split(':')[1].strip()
                continue

            # Parse development_status section
            if 'development_status:' in line:
                current_section = 'development'
                continue

            if current_section != 'development':
                continue

            # Parse epic line - handle inline comments
            # Format: epic-1: in-progress # Description here
            if 'epic-' in line or 'sprint-' in line:
                # Split on # to separate content from comment
                line_parts = line.split('#', 1)
                content_part = line_parts[0].strip()
                description = line_parts[1].strip() if len(line_parts) > 1 else ''

                epic_match = re.match(r'(epic-\d+|sprint-\d+):\s*([\w-]+)', content_part)
                if epic_match:
                    epic_name = epic_match.group(1)
                    epic_status = epic_match.group(2)
                    result['epics'][epic_name] = {
                        'status': epic_status,
                        'description': description,
                        'stories': []
                    }
                    continue

            # Parse story line - handle inline comments
            # Format: 1-1-prerequisite-checklist: done # Description here
            story_match = re.match(r'([\d\w-]+):\s*([\w-]+)', line)
            if story_match:
                # Split on # to separate content from comment
                line_parts = line.split('#', 1)
                content_part = line_parts[0].strip()
                description = line_parts[1].strip() if len(line_parts) > 1 else ''

                story_id = story_match.group(1)
                story_status = story_match.group(2)

                result['stories'][story_id] = {
                    'status': story_status,
                    'description': description,
                    'epic': epic_name
                }

                if epic_name and epic_name in result['epics']:
                    result['epics'][epic_name]['stories'].append(story_id)

        return result

    def get_story_details(self, story_id: str) -> Dict:
        """Get detailed story information from story markdown file"""
        story_file = self.implementation_artifacts / f"story-{story_id}.md"

        if not story_file.exists():
            return {}

        with open(story_file, 'r') as f:
            content = f.read()

        details = {
            'title': '',
            'acceptance_criteria': [],
            'tasks': []
        }

        # Extract title (usually first heading)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            details['title'] = title_match.group(1).strip()

        # Extract acceptance criteria
        ac_section = re.search(r'##?\s*Acceptance Criteria\s*(.*?)(?=##|\Z)', content, re.DOTALL)
        if ac_section:
            ac_lines = [line.strip('- ').strip() for line in ac_section.group(1).split('\n')
                       if line.strip() and line.strip('- ')]
            details['acceptance_criteria'] = ac_lines

        return details


class BeadsManager:
    """Manage Beads tasks via CLI"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.task_id_map = {}  # Maps BMad IDs to Beads IDs

    def create_task(self, title: str, priority: int = 1, description: str = "") -> Optional[str]:
        """Create a Beads task and return its ID"""
        cmd = ['bd', 'create', title, '-p', str(priority)]

        if description:
            # Add description via note (bd will prompt or we can use stdin)
            # For now, we'll include it in the title as a suffix
            cmd[2] = f"{title}: {description[:50]}..."

        if self.dry_run:
            print(f"{Colors.OKCYAN}Would create: {Colors.ENDC}{Colors.BOLD}bd create '{title}' -p {priority}{Colors.ENDC}")
            return f"would-be-created-{title[:10].replace(' ', '-')}"

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            # Extract task ID from output (format: "Created issue bd-xxxx")
            output = result.stdout
            id_match = re.search(r'(bd-[a-f0-9]+)', output)
            if id_match:
                return id_match.group(1)
            return None
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}Error creating task: {e.stderr}{Colors.ENDC}")
            return None

    def update_status(self, task_id: str, status: str) -> bool:
        """Update a Beads task status"""
        cmd = ['bd', 'update', task_id, '--status', status]

        if self.dry_run:
            print(f"{Colors.OKCYAN}Would update: {Colors.ENDC}{Colors.BOLD}bd update {task_id} --status {status}{Colors.ENDC}")
            return True

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}Error updating task {task_id}: {e.stderr}{Colors.ENDC}")
            return False

    def add_dependency(self, child_id: str, parent_id: str) -> bool:
        """Add a dependency between two tasks"""
        cmd = ['bd', 'dep', 'add', child_id, parent_id]

        if self.dry_run:
            print(f"{Colors.OKCYAN}Would link: {Colors.ENDC}{Colors.BOLD}bd dep add {child_id} {parent_id}{Colors.ENDC}")
            return True

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"{Colors.FAIL}Error adding dependency: {e.stderr}{Colors.ENDC}")
            return False

    def get_existing_tasks(self) -> Dict[str, Dict]:
        """Get all existing Beads tasks"""
        cmd = ['bd', 'list', '--json']

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Parse output - this is simplified, actual format may vary
            return {}
        except:
            return {}


def determine_priority(description: str, status: str) -> int:
    """Determine Beads priority (0-3) from description and status"""
    desc_lower = description.lower()

    # Check critical patterns
    for pattern in PRIORITY_PATTERNS['critical']:
        if pattern in desc_lower:
            return 0

    # Check high priority patterns
    for pattern in PRIORITY_PATTERNS['high']:
        if pattern in desc_lower:
            return 1

    # Check medium priority patterns
    for pattern in PRIORITY_PATTERNS['medium']:
        if pattern in desc_lower:
            return 2

    # Default to low priority
    return 3


def format_description(story_id: str, details: Dict, bmad_description: str) -> str:
    """Format a nice description for the Beads task"""
    desc = f"[{story_id}]"

    if details.get('title'):
        desc += f" {details['title']}"
    elif bmad_description and bmad_description != story_id:
        desc += f" {bmad_description}"

    return desc


def print_summary(parsed_data: Dict, epic_filter: Optional[str] = None, status_filter: Optional[str] = None):
    """Print a summary of what would be converted"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== BMad to Beads Conversion Summary ==={Colors.ENDC}\n")

    epics = parsed_data['epics']
    stories = parsed_data['stories']

    total_stories = 0
    filtered_stories = 0

    for epic_id, epic_data in sorted(epics.items()):
        if epic_filter and epic_id != epic_filter:
            continue

        epic_status = epic_data['status']
        epic_desc = epic_data.get('description', '')

        print(f"{Colors.OKBLUE}Epic: {epic_id}{Colors.ENDC} ({epic_status})")
        if epic_desc:
            print(f"  {Colors.WARNING}{epic_desc}{Colors.ENDC}")
        print()

        for story_id in epic_data['stories']:
            if story_id not in stories:
                continue

            total_stories += 1
            story = stories[story_id]

            if status_filter and story['status'] != status_filter:
                continue

            filtered_stories += 1
            priority = determine_priority(story['description'], story['status'])
            beads_status = BMAD_TO_BEADS_STATUS.get(story['status'], 'todo')

            print(f"  {Colors.OKCYAN}→{Colors.ENDC} {story_id}: {story['description'][:60]}")
            print(f"     Status: {story['status']} → {beads_status} | Priority: P{priority}")

    print(f"\n{Colors.BOLD}Total Stories: {total_stories}{Colors.ENDC}")
    if status_filter or epic_filter:
        print(f"{Colors.BOLD}Filtered Stories: {filtered_stories}{Colors.ENDC}")


def convert_to_beads(parsed_data: Dict, beads_mgr: BeadsManager, epic_filter: Optional[str] = None,
                     status_filter: Optional[str] = None, parser: Optional[BMadParser] = None):
    """Convert BMad data to Beads tasks"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== Converting to Beads Tasks ==={Colors.ENDC}\n")

    epics = parsed_data['epics']
    stories = parsed_data['stories']

    epic_task_ids = {}

    for epic_id, epic_data in sorted(epics.items()):
        if epic_filter and epic_id != epic_filter:
            continue

        # Create epic task
        epic_title = f"Epic: {epic_id}"
        if epic_data.get('description'):
            epic_title += f" - {epic_data['description'][:50]}"

        epic_task_id = beads_mgr.create_task(
            title=epic_title,
            priority=1,  # Epics default to P1
            description=epic_data.get('description', '')
        )

        if epic_task_id:
            epic_task_ids[epic_id] = epic_task_id
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} Created epic: {epic_id} → {epic_task_id}")

        # Create story tasks
        for story_id in epic_data['stories']:
            if story_id not in stories:
                continue

            story = stories[story_id]

            if status_filter and story['status'] != status_filter:
                continue

            # Get story details
            details = {}
            if parser:
                details = parser.get_story_details(story_id)

            # Create task
            description = format_description(story_id, details, story['description'])
            priority = determine_priority(story['description'], story['status'])
            beads_status = BMAD_TO_BEADS_STATUS.get(story['status'], 'todo')

            story_task_id = beads_mgr.create_task(
                title=description,
                priority=priority,
                description=story.get('description', '')
            )

            if story_task_id:
                beads_mgr.task_id_map[story_id] = story_task_id
                print(f"{Colors.OKGREEN}✓{Colors.ENDC} Created story: {story_id} → {story_task_id}")

                # Link story to epic
                if epic_task_id:
                    beads_mgr.add_dependency(story_task_id, epic_task_id)

                # Set initial status if not todo
                if beads_status != 'todo':
                    beads_mgr.update_status(story_task_id, beads_status)


def main():
    parser = argparse.ArgumentParser(
        description='Convert BMad Method sprint status to Beads tasks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --dry-run                    # Preview what would be created
  %(prog)s --create                     # Actually create Beads tasks
  %(prog)s --create --epic epic-1       # Only process specific epic
  %(prog)s --create --status backlog    # Only process backlog stories
  %(prog)s --sync                       # Sync status changes
        """
    )

    parser.add_argument('--dry-run', action='store_true', help='Show what would be done (default)')
    parser.add_argument('--create', action='store_true', help='Actually create Beads tasks')
    parser.add_argument('--sync', action='store_true', help='Sync status changes from BMad to Beads')
    parser.add_argument('--epic', type=str, help='Only process specific epic (e.g., epic-1)')
    parser.add_argument('--status', type=str, choices=['backlog', 'ready-for-dev', 'in-progress', 'review', 'done'],
                       help='Only process stories with specific status')

    args = parser.parse_args()

    # Default to dry-run
    dry_run = not args.create and not args.sync

    # Get project root
    project_root = Path.cwd()
    if not (project_root / "_bmad-output").exists():
        print(f"{Colors.FAIL}Error: BMad output directory not found. Are you in the project root?{Colors.ENDC}")
        sys.exit(1)

    # Parse BMad data
    bmad_parser = BMadParser(project_root)
    parsed_data = bmad_parser.parse_sprint_status()

    # Print summary
    print_summary(parsed_data, args.epic, args.status)

    if dry_run:
        print(f"\n{Colors.WARNING}Running in dry-run mode. Use --create to actually create tasks.{Colors.ENDC}")
        return

    # Convert to Beads
    beads_mgr = BeadsManager(dry_run=False)
    convert_to_beads(parsed_data, beads_mgr, args.epic, args.status, bmad_parser)

    print(f"\n{Colors.OKGREEN}{Colors.BOLD}=== Conversion Complete ==={Colors.ENDC}\n")


if __name__ == '__main__':
    main()
