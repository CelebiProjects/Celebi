"""Test script for trace readability improvements.

This script verifies that the trace readability improvements work correctly,
including formatting utilities and Message object integration.
"""
import json
import os
import shutil
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from CelebiChrono.utils.format_utils import (  # pylint: disable=wrong-import-position  # requires sys.path setup above
    format_uuid_short,
    format_node_display,
    format_edge_display
)
from CelebiChrono.utils.message import Message  # pylint: disable=wrong-import-position
from CelebiChrono.kernel.vobj_impression import ImpressionManagement  # pylint: disable=wrong-import-position
from CelebiChrono.kernel.chern_cache import ChernCache  # pylint: disable=wrong-import-position
from CelebiChrono.kernel.vtask import VTask  # pylint: disable=wrong-import-position


def _write_json(path, data):
    """Write json data to the file at path."""
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(data, stream)


def _make_object(path, object_type):
    """Create a plain directory object."""
    os.makedirs(os.path.join(path, ".celebi"), exist_ok=True)
    _write_json(os.path.join(path, ".celebi", "config.json"),
                {"object_type": object_type})


def _make_task_or_algo(path, object_type, predecessors=(), successors=()):
    """Create a task or algorithm object."""
    _make_object(path, object_type)
    with open(os.path.join(path, "celebi.yaml"), "w",
              encoding="utf-8") as stream:
        yaml.safe_dump({"alias": [],
                        "environment": "celebichrono/lhcb-omegac:v0.2",
                        "kubernetes_memory_limit": "256Mi"}, stream)
    with open(os.path.join(path, "README.md"), "w",
              encoding="utf-8") as stream:
        stream.write("")
    _write_json(os.path.join(path, ".celebi", "config.json"), {
        "object_type": object_type,
        "predecessors": list(predecessors),
        "successors": list(successors),
        "alias_to_path": {}, "path_to_alias": {},
        "impression": "", "impressions": [],
        "output_md5s": {}, "output_md5": ""})


def _make_project_with_reimpressed_task():
    """Create a temp project with a task re-impressed after an edit.

    Returns:
        (root, task_path, old_impression_uuid)
    """
    root = os.path.realpath(tempfile.mkdtemp())
    _make_object(root, "project")
    with open(os.path.join(root, ".celebi", "project.json"),
              "w", encoding="utf-8") as stream:
        stream.write("")
    _make_object(os.path.join(root, "code"), "directory")
    gen = os.path.join(root, "code", "Gen")
    _make_task_or_algo(gen, "algorithm", successors=["GenTask1"])
    with open(os.path.join(gen, "gen.C"), "w", encoding="utf-8") as stream:
        stream.write("void gen() {}\n")
    task = os.path.join(root, "GenTask1")
    _make_task_or_algo(task, "task", predecessors=["code/Gen"])
    os.chdir(root)

    task_obj = VTask(task)
    task_obj.impress()
    old_uuid = task_obj.impression().uuid

    # Change the environment and impress again: the new impression's
    # parent is the old one, matching the reported trace scenario.
    yaml_file = os.path.join(task, "celebi.yaml")
    with open(yaml_file, encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    data["environment"] = "docker.io/celebichrono/lhcb-omegac:v0.2"
    with open(yaml_file, "w", encoding="utf-8") as stream:
        yaml.safe_dump(data, stream)
    ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
    task_obj.impress()

    return root, task, old_uuid


def test_formatting_utilities():
    """Test the formatting utilities for human-readable output."""
    print("Testing formatting utilities...")

    # Test format_uuid_short
    uuid = "abc123-def456-ghi789"
    short = format_uuid_short(uuid)
    assert short == "abc123d", f"Expected 'abc123d', got '{short}'"
    print(f"  ✓ format_uuid_short('{uuid}') = '{short}'")

    # Test format_node_display
    node_display = format_node_display(uuid, "task")
    assert node_display == "[TASK] abc123d", f"Expected '[TASK] abc123d', got '{node_display}'"
    print(f"  ✓ format_node_display('{uuid}', 'task') = '{node_display}'")

    # Test format_edge_display
    parent_uuid = "abc123-def456-ghi789"
    child_uuid = "def456-ghi789-jkl012"
    edge_display = format_edge_display(parent_uuid, child_uuid, "task", "algorithm")
    expected = "[TASK] abc123d → [ALGO] def456g"
    assert edge_display == expected, f"Expected '{expected}', got '{edge_display}'"
    print(f"  ✓ format_edge_display() = '{edge_display}'")

    print("All formatting utility tests passed!")


def test_message_object():
    """Verify Message object can be created and used."""
    print("\nTesting Message object...")

    message = Message()
    message.add("Test title", "title0")
    message.add("Test info", "info")
    message.add("Test diff", "diff")
    message.add("Test warning", "warning")

    assert len(message.messages) == 4, f"Expected 4 messages, got {len(message.messages)}"
    print(f"  ✓ Created Message with {len(message.messages)} messages")

    # Check message types
    msg_types = [msg[1] for msg in message.messages]
    assert "title0" in msg_types
    assert "info" in msg_types
    assert "diff" in msg_types
    assert "warning" in msg_types
    print("  ✓ All message types work correctly")

    print("Message object tests passed!")


def test_trace_output_line_breaks():
    """Every trace message entry ends its own line, nothing jams together."""
    root, task, old_uuid = _make_project_with_reimpressed_task()
    try:
        task_obj = VTask(task)
        text = str(task_obj.trace(old_uuid))

        assert "Added nodes (1):\n" in text
        assert "Removed nodes (1):\n" in text
        assert "Added edges (1):\n" in text
        assert "Removed edges (1):\n" in text
        assert "Diff in file: celebi.yaml\n" in text
        assert "celebi.yaml---" not in text
        assert "Changed incoming edges to [TASK]" in text
        assert "Added from (1):\n" in text
        assert "      • [ALGO]" in text
        assert text.endswith("\n")
    finally:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        ChernCache.instance().__init__()  # pylint: disable=unnecessary-dunder-call
        shutil.rmtree(root, ignore_errors=True)


def test_trace_method_exists():
    """Verify trace method exists with correct signature."""
    print("\nChecking trace method signature...")

    # Check that ImpressionManagement has trace method
    assert hasattr(ImpressionManagement, 'trace'), "ImpressionManagement has no 'trace' method"

    # Get the method
    trace_method = getattr(ImpressionManagement, 'trace')

    # Check it's callable
    assert callable(trace_method), "'trace' is not callable"

    # Check return type annotation (if available)
    import inspect
    sig = inspect.signature(trace_method)
    return_annotation = sig.return_annotation

    # Note: return_annotation might be 'Message' or the actual class
    # We'll just check it's not inspect.Signature.empty
    if return_annotation != inspect.Signature.empty:
        # Try to get the annotation as string
        annotation_str = str(return_annotation)
        # Check if it mentions Message (could be 'Message' or 'CelebiChrono.utils.message.Message')
        if 'Message' in annotation_str:
            print(f"  ✓ trace() method returns Message (annotation: {annotation_str})")
        else:
            print(f"  ⚠ trace() method annotation: {annotation_str}")
    else:
        print("  ⚠ trace() method has no return annotation")

    # Check parameters
    params = list(sig.parameters.keys())
    assert 'self' in params, "trace() missing 'self' parameter"
    assert 'impression' in params, "trace() missing 'impression' parameter"
    print(f"  ✓ trace() method has correct parameters: {params}")

    print("Trace method signature tests passed!")


def demonstrate_human_readable_format():
    """Demonstrate the human-readable formatting improvements."""
    print("\n" + "="*60)
    print("DEMONSTRATION: Human-Readable Trace Output Format")
    print("="*60)

    print("\n1. Node Display Examples:")
    print(f"   • {format_node_display('abc123-def456-ghi789', 'task')}")
    print(f"   • {format_node_display('def456-ghi789-jkl012', 'algorithm')}")
    print(f"   • {format_node_display('ghi789-jkl012-mno345', 'data')}")
    print(f"   • {format_node_display('jkl012-mno345-pqr678', 'project')}")
    print(f"   • {format_node_display('mno345-pqr678-stu901', '')} (no type)")

    print("\n2. Edge Display Examples:")
    print(
        "   • "
        + format_edge_display(
            'abc123-def456-ghi789', 'def456-ghi789-jkl012', 'task', 'algorithm'
        )
    )
    print(
        "   • "
        + format_edge_display(
            'def456-ghi789-jkl012', 'ghi789-jkl012-mno345', 'algorithm', 'data'
        )
    )
    print(
        "   • "
        + format_edge_display(
            'jkl012-mno345-pqr678', 'mno345-pqr678-stu901', 'project', ''
        )
    )

    print("\n3. Short UUID Examples:")
    uuids = [
        "abc123-def456-ghi789",
        "a1b2c3-d4e5f6-g7h8i9",
        "shortid",
        "very-long-uuid-with-many-characters-and-hyphens"
    ]
    for uuid in uuids:
        print(f"   • '{uuid}' → '{format_uuid_short(uuid)}'")

    print("\n" + "="*60)
    print("Formatting demonstration complete!")
    print("="*60)


def main():
    """Run all tests and demonstrations."""
    print("Testing trace readability improvements...\n")

    try:
        test_formatting_utilities()
        test_message_object()
        test_trace_method_exists()
        demonstrate_human_readable_format()

        print("\n" + "="*60)
        print("SUCCESS: All trace readability tests passed!")
        print("="*60)
        return 0
    except Exception as e:
        print(f"\nERROR: Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
