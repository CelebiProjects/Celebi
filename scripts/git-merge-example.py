#!/usr/bin/env python3
"""
Example script demonstrating Celebi git merge functionality.

This script shows how to use the git merge system with a simulated
project structure and merge scenario.
"""
import os
import tempfile
import shutil
import json
import yaml
from pathlib import Path


def create_example_project(project_dir):
    """Create an example Celebi project structure."""
    print(f"Creating example project in {project_dir}")

    # Create basic project structure
    os.makedirs(os.path.join(project_dir, '.celebi'), exist_ok=True)
    os.makedirs(os.path.join(project_dir, 'tasks'), exist_ok=True)
    os.makedirs(os.path.join(project_dir, 'data'), exist_ok=True)
    os.makedirs(os.path.join(project_dir, 'algorithms'), exist_ok=True)

    # Create project config
    project_config = {
        'uuid': 'project-123',
        'name': 'example-project',
        'type': 'project',
        'created': '2024-01-01'
    }

    with open(os.path.join(project_dir, '.celebi', 'config.json'), 'w') as f:
        json.dump(project_config, f, indent=2)

    # Create a simple task
    task_config = {
        'uuid': 'task-001',
        'name': 'data-processing',
        'type': 'task',
        'algorithm': 'basic-processor',
        'parameters': {'threshold': 0.5},
        'dependencies': []
    }

    task_dir = os.path.join(project_dir, 'tasks', 'data-processing')
    os.makedirs(task_dir, exist_ok=True)

    with open(os.path.join(task_dir, 'config.json'), 'w') as f:
        json.dump(task_config, f, indent=2)

    # Create YAML version (human-readable)
    yaml_config = {
        'uuid': 'task-001',
        'name': 'data-processing',
        'description': 'Process input data with threshold',
        'algorithm': 'basic-processor',
        'parameters': {'threshold': 0.5},
        'dependencies': []
    }

    with open(os.path.join(task_dir, 'config.yaml'), 'w') as f:
        yaml.dump(yaml_config, f, default_flow_style=False)

    print("  Created example project with 1 task")
    return project_dir


def simulate_git_merge_scenario():
    """Simulate a git merge scenario with conflicts."""
    print("\n" + "="*80)
    print("SIMULATING GIT MERGE SCENARIO")
    print("="*80)

    # Create temporary directory for simulation
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, 'example-project')

        # Create base project
        create_example_project(project_dir)

        print("\nSimulating git operations:")
        print("1. Initialize git repository")
        print("2. Create initial commit")
        print("3. Create feature branch with modifications")
        print("4. Make conflicting changes in main branch")
        print("5. Attempt merge with Celebi validation")

        # Simulate DAG merge
        print("\nSimulating DAG merge conflict...")

        # Create simple DAGs for demonstration
        import networkx as nx

        # Base DAG: A -> B -> C
        base_dag = nx.DiGraph()
        base_dag.add_edges_from([('A', 'B'), ('B', 'C')])

        # Local DAG: A -> B -> C, added D -> E
        local_dag = nx.DiGraph()
        local_dag.add_edges_from([('A', 'B'), ('B', 'C'), ('D', 'E')])

        # Remote DAG: A -> B -> C, changed B -> X instead of B -> C
        remote_dag = nx.DiGraph()
        remote_dag.add_edges_from([('A', 'B'), ('B', 'X')])

        print(f"  Base DAG: {list(base_dag.edges())}")
        print(f"  Local DAG: {list(local_dag.edges())}")
        print(f"  Remote DAG: {list(remote_dag.edges())}")

        # Try to import and use DAGMerger
        try:
            from CelebiChrono.kernel.vobj_arc_merge import DAGMerger, MergeResolutionStrategy

            merger = DAGMerger(strategy=MergeResolutionStrategy.INTERACTIVE)
            merged_dag = merger.merge_dags(local_dag, remote_dag, base_dag)

            print(f"\nMerged DAG: {list(merged_dag.edges())}")
            print(f"Conflicts detected: {len(merger.get_conflicts())}")

            if merger.has_conflicts():
                print("Conflicts require resolution:")
                for conflict in merger.get_conflicts():
                    print(f"  - {conflict.description}")

        except ImportError as e:
            print(f"  Could not import DAGMerger: {e}")
            print("  (This is expected if Celebi is not installed)")

        # Simulate config merge
        print("\nSimulating config merge conflict...")

        base_config = {
            'uuid': 'config-123',
            'name': 'example',
            'dependencies': ['task1', 'task2']
        }

        local_config = {
            'uuid': 'config-123',
            'name': 'example',
            'dependencies': ['task1', 'task2', 'task3']  # Added task3
        }

        remote_config = {
            'uuid': 'config-123',
            'name': 'example',
            'dependencies': ['task1', 'task4']  # Removed task2, added task4
        }

        print(f"  Base config dependencies: {base_config['dependencies']}")
        print(f"  Local config dependencies: {local_config['dependencies']}")
        print(f"  Remote config dependencies: {remote_config['dependencies']}")

        # Try to import and use ConfigMerger
        try:
            from CelebiChrono.utils.config_merge import ConfigMerger

            config_merger = ConfigMerger(prefer_local=True)

            # Convert to YAML for merging
            base_yaml = yaml.dump(base_config, default_flow_style=False)
            local_yaml = yaml.dump(local_config, default_flow_style=False)
            remote_yaml = yaml.dump(remote_config, default_flow_style=False)

            merged_yaml, conflicts = config_merger.merge_yaml_files(
                local_yaml, remote_yaml, base_yaml
            )

            merged_config = yaml.safe_load(merged_yaml)
            print(f"  Merged dependencies: {merged_config['dependencies']}")
            print(f"  Config conflicts: {len(conflicts)}")

        except ImportError as e:
            print(f"  Could not import ConfigMerger: {e}")

        print("\n" + "="*80)
        print("SIMULATION COMPLETE")
        print("="*80)
        print("\nThis simulation demonstrated:")
        print("1. DAG merging with conflict detection")
        print("2. Config file merging with semantic understanding")
        print("3. How Celebi would handle git merge scenarios")

        return True


def show_cli_usage():
    """Show CLI usage examples."""
    print("\n" + "="*80)
    print("CLI USAGE EXAMPLES")
    print("="*80)

    print("\nBasic git integration commands:")
    print("  celebi git-status                    # Check git integration status")
    print("  celebi git-enable                    # Enable git integration")
    print("  celebi git-disable                   # Disable git integration")
    print("  celebi git-hooks                     # Install git hooks")
    print("  celebi git-hooks --uninstall         # Uninstall git hooks")

    print("\nMerge commands:")
    print("  celebi git-merge feature-branch      # Merge with interactive resolution")
    print("  celebi git-merge feature-branch --strategy=auto    # Auto-merge")
    print("  celebi git-merge feature-branch --strategy=local   # Prefer local")
    print("  celebi git-merge feature-branch --dry-run          # Simulate merge")

    print("\nValidation commands:")
    print("  celebi git-validate                  # Validate project after merge")
    print("  celebi doctor                        # General project validation")

    print("\nConfiguration:")
    print("  celebi git-config auto_validate true # Enable auto-validation")
    print("  celebi git-config merge_strategy auto # Set default merge strategy")

    print("\nShell commands (inside Celebi shell):")
    print("  git_merge feature-branch             # Merge with validation")
    print("  git_validate                         # Validate project state")
    print("  git_status                           # Show git integration status")


def main():
    """Main function."""
    print("CELEBI GIT MERGE SYSTEM DEMONSTRATION")
    print("="*80)

    # Check if Celebi is available
    try:
        import CelebiChrono
        print("✓ Celebi package found")
    except ImportError:
        print("✗ Celebi package not found")
        print("  Install with: pip install -e .")
        return

    # Run simulation
    simulate_git_merge_scenario()

    # Show CLI usage
    show_cli_usage()

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\nTo use the git merge system:")
    print("1. Initialize a git repository: git init")
    print("2. Initialize a Celebi project: celebi init")
    print("3. Enable git integration: celebi git-enable")
    print("4. Install git hooks: celebi git-hooks")
    print("5. Create branches and make changes")
    print("6. Merge with validation: celebi git-merge <branch>")

    print("\nFor more information:")
    print("  - Run: celebi --help")
    print("  - See tests in: UnitTest/test_*.py")
    print("  - Check implementation in: CelebiChrono/utils/git_*.py")


if __name__ == '__main__':
    main()