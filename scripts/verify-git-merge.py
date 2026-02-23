#!/usr/bin/env python3
"""
Verification script for git merge system implementation.

This script checks that all required components are implemented
and can be imported correctly.
"""
import os
import sys

def check_import(module_path, class_name=None):
    """Check if a module or class can be imported."""
    try:
        if class_name:
            exec(f"from {module_path} import {class_name}")
            print(f"✓ {module_path}.{class_name}")
            return True
        else:
            exec(f"import {module_path}")
            print(f"✓ {module_path}")
            return True
    except ImportError as e:
        print(f"✗ {module_path}{'.' + class_name if class_name else ''}: {e}")
        return False
    except Exception as e:
        print(f"✗ {module_path}{'.' + class_name if class_name else ''}: {e}")
        return False

def main():
    """Main verification function."""
    print("VERIFYING GIT MERGE SYSTEM IMPLEMENTATION")
    print("="*80)

    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

    checks = []

    print("\n1. Core DAG Merge Components:")
    checks.append(check_import("CelebiChrono.kernel.vobj_arc_merge", "DAGMerger"))
    checks.append(check_import("CelebiChrono.kernel.vobj_arc_merge", "MergeConflictType"))
    checks.append(check_import("CelebiChrono.kernel.vobj_arc_merge", "MergeResolutionStrategy"))

    print("\n2. Config Merge Components:")
    checks.append(check_import("CelebiChrono.utils.config_merge", "ConfigMerger"))
    checks.append(check_import("CelebiChrono.utils.config_merge", "detect_config_file_type"))

    print("\n3. Visualization Components:")
    checks.append(check_import("CelebiChrono.utils.dag_visualizer", "DAGVisualizer"))

    print("\n4. Git Integration Components:")
    checks.append(check_import("CelebiChrono.utils.git_merge_coordinator", "GitMergeCoordinator"))
    checks.append(check_import("CelebiChrono.utils.git_merge_coordinator", "MergeStrategy"))
    checks.append(check_import("CelebiChrono.utils.git_optional", "GitOptionalIntegration"))

    print("\n5. Interactive Resolution:")
    checks.append(check_import("CelebiChrono.interface.merge_resolver", "MergeResolver"))
    checks.append(check_import("CelebiChrono.interface.merge_resolver", "ResolutionAction"))

    print("\n6. Doctor System Extensions:")
    # Check if doctor has merge methods (can't import directly, check file)
    doctor_path = "CelebiChrono/kernel/vobj_arc_doctor.py"
    if os.path.exists(doctor_path):
        with open(doctor_path, 'r') as f:
            content = f.read()
            if "validate_merge" in content and "repair_merge_conflicts" in content:
                print(f"✓ Doctor extensions found in {doctor_path}")
                checks.append(True)
            else:
                print(f"✗ Doctor extensions missing in {doctor_path}")
                checks.append(False)
    else:
        print(f"✗ Doctor file not found: {doctor_path}")
        checks.append(False)

    print("\n7. Impression Regeneration:")
    checks.append(check_import("CelebiChrono.kernel.vobj_impression_regenerate", "ImpressionRegenerator"))

    print("\n8. CLI Commands:")
    # Check main.py for git commands
    main_path = "CelebiChrono/main.py"
    if os.path.exists(main_path):
        with open(main_path, 'r') as f:
            content = f.read()
            git_commands = ['git_merge', 'git_validate', 'git_status', 'git_enable', 'git_disable', 'git_hooks', 'git_config']
            found = [cmd for cmd in git_commands if f"def {cmd}" in content or f"@{cmd}" in content]
            if len(found) >= 5:  # At least 5 of 7 commands
                print(f"✓ CLI commands found: {', '.join(found)}")
                checks.append(True)
            else:
                print(f"✗ Missing CLI commands. Found: {', '.join(found)}")
                checks.append(False)
    else:
        print(f"✗ Main CLI file not found: {main_path}")
        checks.append(False)

    print("\n9. Shell Commands:")
    # Check utilities.py for git functions
    utilities_path = "CelebiChrono/interface/shell_modules/utilities.py"
    if os.path.exists(utilities_path):
        with open(utilities_path, 'r') as f:
            content = f.read()
            git_functions = ['git_merge', 'git_validate', 'git_status', 'git_enable', 'git_disable', 'git_hooks']
            found = [func for func in git_functions if f"def {func}" in content]
            if len(found) >= 4:  # At least 4 of 6 functions
                print(f"✓ Shell functions found: {', '.join(found)}")
                checks.append(True)
            else:
                print(f"✗ Missing shell functions. Found: {', '.join(found)}")
                checks.append(False)
    else:
        print(f"✗ Utilities file not found: {utilities_path}")
        checks.append(False)

    print("\n10. Test Files:")
    test_files = [
        "UnitTest/test_dag_merge.py",
        "UnitTest/test_config_merge.py",
        "UnitTest/test_git_integration.py",
        "UnitTest/test_merge_resolver.py"
    ]
    test_checks = []
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"✓ {test_file}")
            test_checks.append(True)
        else:
            print(f"✗ {test_file}")
            test_checks.append(False)
    checks.append(all(test_checks))

    print("\n11. Example Scripts:")
    example_files = [
        "scripts/git-merge-example.py",
        "scripts/git-hooks/post-merge",
        "scripts/git-hooks/install-hooks"
    ]
    example_checks = []
    for example_file in example_files:
        if os.path.exists(example_file):
            print(f"✓ {example_file}")
            example_checks.append(True)
        else:
            print(f"✗ {example_file}")
            example_checks.append(False)
    checks.append(all(example_checks))

    print("\n" + "="*80)
    success_count = sum(checks)
    total_count = len(checks)

    if success_count == total_count:
        print(f"✅ ALL {total_count} CHECKS PASSED")
        print("\nGit merge system implementation is complete and ready for testing.")
    else:
        print(f"⚠ {success_count}/{total_count} CHECKS PASSED")
        print(f"\n{total_count - success_count} checks failed.")
        print("Some components may be missing or have import issues.")

    print("\nNext steps:")
    print("1. Install dependencies: pip install -e .")
    print("2. Run tests: python -m pytest UnitTest/test_*.py -v")
    print("3. Try example: python scripts/git-merge-example.py")
    print("4. Test in a real project: celebi git-enable")

    return success_count == total_count

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)