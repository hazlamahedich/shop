#!/usr/bin/env python3
"""
Dashboard Visual & Interaction Testing Script

Checks for common issues:
1. Missing or incorrect ARIA labels
2. Broken hover states
3. Missing tooltips
4. Color contrast issues
5. Empty data states
6. Loading states
7. Click handlers
8. Overflow issues
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

FRONTEND_DIR = Path("/Users/sherwingorechomante/shop/frontend/src")

# Patterns to check
PATTERNS = {
    'missing_aria_label': (
        r'<(svg|div|button)(?!.*aria-label)',
        "Element without aria-label"
    ),
    'missing_role': (
        r'role=["\'](?:img|graphics-document|button)["\']',
        "Good: Has role attribute"
    ),
    'has_tooltip': (
        r'showTooltip\s*=\s*{true}',
        "Tooltip enabled"
    ),
    'click_handler': (
        r'onClick\s*=',
        "Click handler present"
    ),
    'hover_state': (
        r'hover:',
        "Hover state defined"
    ),
    'empty_state': (
        r'\.length\s*===\s*0|isEmpty|!isLoading.*!data',
        "Empty state handling"
    ),
    'loading_state': (
        r'isLoading.*\?\.',
        "Loading state handling"
    ),
}

ISSUES_FOUND = []

def check_file(filepath: Path) -> List[Tuple[str, str]]:
    """Check a file for potential issues"""
    issues = []
    content = filepath.read_text()

    # Check for missing aria-label on interactive elements
    if 'dashboard' in str(filepath) or 'charts' in str(filepath):
        # Look for interactive elements without aria-label
        buttons = re.findall(r'<button[^>]*>(.*?)</button>', content, re.DOTALL)
        for btn in buttons:
            if 'aria-label' not in btn and len(btn.strip()) < 20:
                issues.append((filepath.name, f"Button without aria-label: {btn[:50]}..."))

        # Check for chart components
        if filepath.name.startswith(('Area', 'Bar', 'Bubble', 'Donut', 'Radar', 'Treemap')):
            if 'ariaLabel' not in content:
                issues.append((filepath.name, "Chart missing ariaLabel prop"))

            if 'showTooltip' not in content and 'Tooltip' not in content:
                issues.append((filepath.name, "Chart has no tooltip"))

    return issues

def check_widget_completeness(filepath: Path) -> List[str]:
    """Check if widget has all necessary states"""
    missing = []
    content = filepath.read_text()

    if 'isLoading' not in content and 'loading' not in content.lower():
        missing.append("loading")

    if 'error' not in content.lower() and 'isError' not in content:
        missing.append("error")

    # Check for empty data handling
    has_empty_check = (
        'length === 0' in content or
        '?.length === 0' in content or
        'data?.length === 0' in content or
        '=== 0' in content
    )

    if not has_empty_check and 'Widget' in filepath.name:
        missing.append("empty data check")

    return missing

def main():
    print("🔍 Testing Dashboard Visuals & Interactions\n")
    print("=" * 60)

    # Check all dashboard widgets and charts
    dashboard_files = list((FRONTEND_DIR / "components/dashboard").glob("*.tsx"))
    chart_files = list((FRONTEND_DIR / "components/charts").glob("*.tsx"))

    all_files = dashboard_files + chart_files

    print(f"\n📊 Checking {len(all_files)} files...\n")

    issues_count = 0
    warnings_count = 0

    for filepath in all_files:
        # Check for issues
        file_issues = check_file(filepath)

        # Check widget completeness
        if 'Widget' in filepath.name:
            missing_states = check_widget_completeness(filepath)
            if missing_states:
                warnings_count += 1
                print(f"⚠️  {filepath.name}: Missing states: {', '.join(missing_states)}")

        for filename, issue in file_issues:
            issues_count += 1
            print(f"❌ {filename}: {issue}")

    print("\n" + "=" * 60)
    print(f"\n✅ Analysis complete!")
    print(f"   Issues found: {issues_count}")
    print(f"   Warnings: {warnings_count}")

    # Check for specific visual issues
    print("\n🎨 Visual Quality Checks:\n")

    # Check for text-shadow on colored backgrounds
    for filepath in chart_files:
        content = filepath.read_text()

        # Check for text-shadow in bubble/treemap charts
        if 'Bubble' in filepath.name or 'Treemap' in filepath.name:
            if 'text-shadow' not in content and 'textShadow' not in content:
                print(f"⚠️  {filepath.name}: May need text-shadow for contrast")
                warnings_count += 1

        # Check for hover animations
        if 'transition' not in content:
            print(f"⚠️  {filepath.name}: Missing hover transitions")
            warnings_count += 1

    print("\n" + "=" * 60)

    if issues_count == 0 and warnings_count == 0:
        print("\n✨ All checks passed! Dashboard looks great.")
        return 0
    elif issues_count == 0:
        print(f"\n⚠️  {warnings_count} warnings found. Consider reviewing.")
        return 0
    else:
        print(f"\n❌ {issues_count} issues need attention!")
        return 1

if __name__ == '__main__':
    sys.exit(main())
