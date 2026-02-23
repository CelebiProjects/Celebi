"""Test script for trace readability improvements.

This script verifies that the trace readability improvements work correctly,
including formatting utilities and Message object integration.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from CelebiChrono.utils.format_utils import (
    format_uuid_short,
    format_node_display,
    format_edge_display
)
from CelebiChrono.utils.message import Message
from CelebiChrono.kernel.vobj_impression import ImpressionManagement


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
    print(f"   • {format_edge_display('abc123-def456-ghi789', 'def456-ghi789-jkl012', 'task', 'algorithm')}")
    print(f"   • {format_edge_display('def456-ghi789-jkl012', 'ghi789-jkl012-mno345', 'algorithm', 'data')}")
    print(f"   • {format_edge_display('jkl012-mno345-pqr678', 'mno345-pqr678-stu901', 'project', '')}")

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