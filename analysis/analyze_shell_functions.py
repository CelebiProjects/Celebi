#!/usr/bin/env python3
"""
Shell Function Documentation Analysis Script

This script analyzes shell functions in the Celebi codebase to generate
a detailed breakdown of documentation completeness and categorization.

Outputs a CSV file with function-by-function analysis including:
- Function name
- Line number
- Category
- Documentation sections present
- Quality rating
"""

import ast
import csv
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional


# Category mapping from design document
CATEGORY_MAPPING = {
    # Navigation Functions
    "cd_project": "navigation",
    "shell_cd_project": "navigation",
    "cd": "navigation",
    "navigate": "navigation",

    # File Operations
    "mv": "file_operations",
    "cp": "file_operations",
    "ls": "file_operations",
    "short_ls": "file_operations",
    "successors": "file_operations",
    "rm": "file_operations",
    "rm_file": "file_operations",
    "mv_file": "file_operations",
    "import_file": "file_operations",

    # Object Creation
    "mkalgorithm": "object_creation",
    "mktask": "object_creation",
    "mkdata": "object_creation",
    "mkdir": "object_creation",

    # Task Configuration
    "add_source": "task_configuration",
    "jobs": "task_configuration",
    "status": "task_configuration",
    "add_input": "task_configuration",
    "add_algorithm": "task_configuration",
    "add_parameter": "task_configuration",
    "add_parameter_subtask": "task_configuration",
    "set_environment": "task_configuration",
    "set_memory_limit": "task_configuration",
    "rm_parameter": "task_configuration",
    "remove_input": "task_configuration",

    # Execution Management
    "jobs": "execution_management",
    "status": "execution_management",
    "submit": "execution_management",
    "collect": "execution_management",
    "collect_outputs": "execution_management",
    "collect_logs": "execution_management",
    "purge": "execution_management",
    "purge_old_impressions": "execution_management",

    # Communication
    "add_host": "communication",
    "hosts": "communication",
    "dite": "communication",
    "set_dite": "communication",
    "runners": "communication",
    "register_runner": "communication",
    "remove_runner": "communication",
    "request_runner": "communication",
    "search_impression": "communication",
    "send": "communication",

    # Visualization
    "view": "visualization",
    "viewurl": "visualization",
    "impress": "visualization",
    "trace": "visualization",

    # Utilities
    "get_script_path": "utilities",
    "config": "utilities",
    "danger_call": "utilities",
    "workaround_preshell": "utilities",
    "workaround_postshell": "utilities",
    "history": "utilities",
    "watermark": "utilities",
    "changes": "utilities",
    "doctor": "utilities",
    "bookkeep": "utilities",
    "bookkeep_url": "utilities",
    "tree": "utilities",
    "error_log": "utilities",
}


class FunctionAnalyzer(ast.NodeVisitor):
    """AST visitor to extract function definitions and their docstrings."""

    def __init__(self):
        self.functions = []
        self.current_file = ""

    def visit_FunctionDef(self, node):
        """Extract function information including docstring."""
        func_info = {
            'name': node.name,
            'line': node.lineno,
            'file': self.current_file,
            'docstring': ast.get_docstring(node),
            'args': self._extract_args(node),
            'has_args_section': False,
            'has_returns_section': False,
            'has_examples_section': False,
            'has_note_section': False,
        }

        # Analyze docstring sections
        if func_info['docstring']:
            func_info.update(self._analyze_docstring(func_info['docstring']))

        # Determine category
        func_info['category'] = CATEGORY_MAPPING.get(node.name, "uncategorized")

        # Determine quality rating
        func_info['quality_rating'] = self._determine_quality(func_info)

        self.functions.append(func_info)

        # Continue visiting child nodes
        self.generic_visit(node)

    def _extract_args(self, node) -> List[str]:
        """Extract argument names from function definition."""
        args = []
        # Positional arguments
        for arg in node.args.args:
            args.append(arg.arg)
        # *args
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        # **kwargs
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")
        return args

    def _analyze_docstring(self, docstring: str) -> Dict:
        """Analyze docstring for sections."""
        result = {
            'has_args_section': False,
            'has_returns_section': False,
            'has_examples_section': False,
            'has_note_section': False,
        }

        # Check for sections (case-insensitive)
        doc_lower = docstring.lower()

        # Args section
        if 'args:' in doc_lower or 'arguments:' in doc_lower:
            result['has_args_section'] = True

        # Returns section
        if 'returns:' in doc_lower or 'return:' in doc_lower:
            result['has_returns_section'] = True

        # Examples section
        if 'examples:' in doc_lower or 'example:' in doc_lower:
            result['has_examples_section'] = True

        # Note section
        if 'note:' in doc_lower or 'notes:' in doc_lower:
            result['has_note_section'] = True

        return result

    def _determine_quality(self, func_info: Dict) -> str:
        """Determine documentation quality rating."""
        if not func_info.get('docstring'):
            return "None"

        sections = [
            func_info.get('has_args_section', False),
            func_info.get('has_returns_section', False),
            func_info.get('has_examples_section', False),
            func_info.get('has_note_section', False),
        ]

        # Count how many sections are present
        section_count = sum(sections)

        if section_count >= 3:
            return "Good"
        elif section_count >= 1:
            return "Partial"
        else:
            return "Basic"  # Has docstring but no formal sections


def analyze_file(filepath: str) -> List[Dict]:
    """Analyze a single Python file for function definitions."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        analyzer = FunctionAnalyzer()
        analyzer.current_file = filepath
        analyzer.visit(tree)

        return analyzer.functions
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {filepath}: {e}")
        return []


def find_shell_files(base_dir: str) -> List[str]:
    """Find Python files containing shell functions."""
    shell_files = []

    # Look for shell-related files
    patterns = [
        "**/shell.py",
        "**/chern_shell_*.py",
        "**/commands_*.py",
        "**/interface/*.py",
    ]

    for pattern in patterns:
        for filepath in Path(base_dir).glob(pattern):
            if filepath.is_file() and filepath.suffix == '.py':
                shell_files.append(str(filepath))

    return sorted(set(shell_files))


def generate_csv_report(functions: List[Dict], output_path: str):
    """Generate CSV report from function analysis."""
    if not functions:
        print("No functions found to analyze.")
        return

    # Prepare CSV data
    csv_data = []
    for func in functions:
        csv_data.append({
            'Function Name': func['name'],
            'Line Number': func['line'],
            'File': os.path.relpath(func['file'], os.path.dirname(output_path)),
            'Category': func['category'],
            'Has Docstring': 'Y' if func['docstring'] else 'N',
            'Has Args Section': 'Y' if func['has_args_section'] else 'N',
            'Has Returns Section': 'Y' if func['has_returns_section'] else 'N',
            'Has Examples Section': 'Y' if func['has_examples_section'] else 'N',
            'Has Note Section': 'Y' if func['has_note_section'] else 'N',
            'Documentation Quality': func['quality_rating'],
            'Number of Arguments': len(func['args']),
            'Arguments': ', '.join(func['args']) if func['args'] else 'None',
        })

    # Write CSV file
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Function Name', 'Line Number', 'File', 'Category',
            'Has Docstring', 'Has Args Section', 'Has Returns Section',
            'Has Examples Section', 'Has Note Section', 'Documentation Quality',
            'Number of Arguments', 'Arguments'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(csv_data)

    print(f"CSV report generated: {output_path}")
    print(f"Total functions analyzed: {len(functions)}")


def generate_summary_report(functions: List[Dict]):
    """Generate summary statistics."""
    if not functions:
        print("No functions to summarize.")
        return

    total = len(functions)

    # Count by category
    categories = {}
    for func in functions:
        cat = func['category']
        categories[cat] = categories.get(cat, 0) + 1

    # Count by quality
    qualities = {'Good': 0, 'Partial': 0, 'Basic': 0, 'None': 0}
    for func in functions:
        qualities[func['quality_rating']] += 1

    # Count documentation sections
    sections = {
        'has_docstring': sum(1 for f in functions if f['docstring']),
        'has_args': sum(1 for f in functions if f['has_args_section']),
        'has_returns': sum(1 for f in functions if f['has_returns_section']),
        'has_examples': sum(1 for f in functions if f['has_examples_section']),
        'has_note': sum(1 for f in functions if f['has_note_section']),
    }

    print("\n" + "="*60)
    print("SUMMARY REPORT")
    print("="*60)
    print(f"Total functions analyzed: {total}")

    print("\nBy Category:")
    print("-"*40)
    for cat, count in sorted(categories.items()):
        percentage = (count / total) * 100
        print(f"  {cat:25} {count:3} ({percentage:5.1f}%)")

    print("\nBy Documentation Quality:")
    print("-"*40)
    for quality, count in qualities.items():
        percentage = (count / total) * 100
        print(f"  {quality:25} {count:3} ({percentage:5.1f}%)")

    print("\nDocumentation Sections:")
    print("-"*40)
    for section, count in sections.items():
        percentage = (count / total) * 100
        print(f"  {section:25} {count:3} ({percentage:5.1f}%)")

    # List undocumented functions
    undocumented = [f for f in functions if not f['docstring']]
    if undocumented:
        print(f"\nUndocumented Functions ({len(undocumented)}):")
        print("-"*40)
        for func in undocumented:
            print(f"  {func['name']:30} (line {func['line']} in {os.path.basename(func['file'])})")

    # List uncategorized functions
    uncategorized = [f for f in functions if f['category'] == 'uncategorized']
    if uncategorized:
        print(f"\nUncategorized Functions ({len(uncategorized)}):")
        print("-"*40)
        for func in uncategorized:
            print(f"  {func['name']:30} (line {func['line']} in {os.path.basename(func['file'])})")


def main():
    """Main analysis function."""
    base_dir = "/Users/zhaomr/workdir/Chern/Celebi"
    output_csv = "/Users/zhaomr/workdir/Chern/Celebi/analysis/shell_documentation_analysis.csv"

    print("Analyzing shell functions in Celebi codebase...")
    print(f"Base directory: {base_dir}")

    # Find shell files
    shell_files = find_shell_files(base_dir)
    print(f"\nFound {len(shell_files)} shell-related files:")
    for file in shell_files:
        print(f"  {os.path.relpath(file, base_dir)}")

    # Analyze all files
    all_functions = []
    for filepath in shell_files:
        functions = analyze_file(filepath)
        all_functions.extend(functions)

    # Filter for functions in our category mapping (shell functions)
    shell_functions = [f for f in all_functions if f['name'] in CATEGORY_MAPPING]

    print(f"\nFound {len(shell_functions)} shell functions (from category mapping)")

    # Generate reports
    generate_csv_report(shell_functions, output_csv)
    generate_summary_report(shell_functions)

    # Also show all functions found for comparison
    print(f"\nTotal functions found in files: {len(all_functions)}")
    if len(all_functions) > len(shell_functions):
        other_functions = [f for f in all_functions if f['name'] not in CATEGORY_MAPPING]
        print(f"Other functions (not in shell mapping): {len(other_functions)}")

        # Show top 20 other functions
        print("\nTop 20 other functions found:")
        for i, func in enumerate(other_functions[:20]):
            print(f"  {i+1:2}. {func['name']:30} (line {func['line']} in {os.path.basename(func['file'])})")
        if len(other_functions) > 20:
            print(f"  ... and {len(other_functions) - 20} more")


if __name__ == "__main__":
    main()