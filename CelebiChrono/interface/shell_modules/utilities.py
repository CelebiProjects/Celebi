"""
Utility functions for shell interface.

Miscellaneous utility functions for workarounds, history, diagnostics, etc.
"""
from typing import Tuple

from ...utils.message import Message
from ._manager import MANAGER


def workaround_preshell() -> tuple[bool, str]:
    """Execute pre-shell workaround for the current task.

    Runs pre-execution workaround code for task preparation. Workarounds
    are custom scripts or operations that run before task shell execution
    to handle special cases or environment setup.

    Args:
        None: Function takes no parameters.

    Examples:
        workaround_preshell()  # Execute pre-shell workaround

    Returns:
        tuple[bool, str]: Success flag and message. Returns (False, error_message)
        if current object is not a task.

    Note:
        - Current object must be a task
        - Workaround code is defined in task configuration
        - Runs before task's main shell execution
        - Useful for environment preparation or data staging
    """
    if not MANAGER.current_object().is_task():
        return (False, "Not able to call workaround if you are not in a task.")
    return MANAGER.current_object().workaround_preshell()


def workaround_postshell(path: str) -> None:
    """Execute post-shell workaround for the current task.

    Runs post-execution workaround code for task cleanup or result
    processing. Workarounds are custom scripts that run after task
    shell execution to handle special cases or output processing.

    Args:
        path (str): Path parameter for workaround execution, typically
            indicating output location or result data.

    Examples:
        workaround_postshell results/  # Process results directory
        workaround_postshell output.csv  # Process output file

    Returns:
        None: Function executes workaround operations.

    Note:
        - Current object must be a task
        - Workaround code is defined in task configuration
        - Runs after task's main shell execution
        - Useful for result processing or cleanup operations
    """
    print("Working on postshell")
    if not MANAGER.current_object().is_task():
        print("Not able to call workaround if you are not in a task.")
        return
    print(MANAGER.current_object())
    MANAGER.current_object().workaround_postshell(path)


def history() -> Message:
    """Print the history of a task or algorithm.

    Retrieves and displays the execution history of the current object,
    including past runs, modifications, and state changes. History
    provides audit trail and debugging information.

    Args:
        None: Function takes no parameters.

    Examples:
        history()  # Display object history

    Returns:
        Message: Formatted message containing chronological history entries,
        timestamps, and change descriptions.

    Note:
        - History entries are automatically recorded
        - Includes both execution and configuration changes
        - Useful for debugging and understanding object evolution
        - History depth may be limited by configuration
    """
    return MANAGER.current_object().history()


def watermark() -> Message:
    """Print the watermark of a task or algorithm.

    Displays watermark information for the current object, which typically
    includes creation metadata, version information, and signature data.
    Watermarks help verify object authenticity and provenance.

    Args:
        None: Function takes no parameters.

    Examples:
        watermark()  # Display object watermark

    Returns:
        Message: Formatted message containing watermark details such as
        creation time, author, version, and cryptographic signatures.

    Note:
        - Watermarks are automatically generated
        - Includes both metadata and verification data
        - Useful for auditing and provenance tracking
        - May include digital signatures for verification
    """
    return MANAGER.current_object().watermark()


def changes() -> Message:
    """Print the changes of a task or algorithm.

    Displays recent changes made to the current object, including
    configuration modifications, input/output updates, and state
    transitions. Changes are tracked automatically by the system.

    Args:
        None: Function takes no parameters.

    Examples:
        changes()  # Display recent object changes

    Returns:
        Message: Formatted message containing change log with timestamps,
        change types, and detailed descriptions of modifications.

    Note:
        - Changes are automatically tracked
        - Includes both manual edits and system-generated changes
        - Useful for understanding recent modifications
        - Change history may be limited by retention settings
    """
    return MANAGER.current_object().changes()


def doctor() -> Message:
    """Doctor the impression.

    Performs diagnostic checks and repairs on impression data for the
    current object. Validates impression integrity, fixes inconsistencies,
    and reports any issues found.

    Args:
        None: Function takes no parameters.

    Examples:
        doctor()  # Diagnose and repair impressions

    Returns:
        Message: Diagnostic report containing validation results,
        issues found, repair actions taken, and overall health status.

    Note:
        - Checks impression data integrity and consistency
        - May attempt automatic repairs for fixable issues
        - Reports but cannot fix some serious data corruption
        - Useful for troubleshooting visualization problems
    """
    return MANAGER.current_object().doctor()


def bookkeep() -> Message:
    """Bookkeep the impression.

    Performs bookkeeping operations on impression data at the project
    root level. Manages impression storage, indexing, and cleanup
    across the entire project.

    Args:
        None: Function takes no parameters.

    Examples:
        bookkeep()  # Perform project-wide impression bookkeeping

    Returns:
        Message: Bookkeeping report containing operations performed,
        storage statistics, and any issues encountered.

    Note:
        - Operates at project root level, not current object
        - Manages impression storage and organization
        - May include cleanup of orphaned or outdated impressions
        - Helps maintain project performance and organization
    """
    return MANAGER.root_object().bookkeep()


def bookkeep_url() -> str:
    """Get the bookkeep URL.

    Retrieves the URL or path where bookkeeping information and reports
    can be accessed for the current project. This may be a local file
    path or web address depending on configuration.

    Args:
        None: Function takes no parameters.

    Examples:
        url = bookkeep_url()  # Get bookkeeping URL
        print(f"Bookkeeping at: {bookkeep_url()}")  # Display URL

    Returns:
        str: URL or file path for accessing bookkeeping information.

    Note:
        - Returns project-level bookkeeping location
        - May be local file path or remote URL
        - Location depends on project configuration
        - Used for accessing detailed bookkeeping reports
    """
    return MANAGER.root_object().bookkeep_url()


def tree(depth: int = -1) -> Message:
    """Get the directory tree.

    Displays the filesystem tree structure of the current object's directory, showing files and subdirectories with optional depth limitation.

    Args:
        depth (int, optional): Maximum depth to display. -1 shows unlimited depth (entire tree). Defaults to -1.

    Examples:
        tree()      # Show complete directory tree
        tree(2)     # Show tree up to depth 2
        tree(0)     # Show only current directory

    Returns:
        Message: Formatted tree structure showing directory hierarchy, file names, and optionally file metadata.

    Note:
        - Depth -1 shows unlimited recursion
        - Tree includes both files and directories
        - Output is formatted for readability
        - Useful for understanding object directory structure
    """
    return MANAGER.current_object().tree()


def error_log(index: int) -> Message:
    """Get the error log.

    Retrieves error log entries for the current object. Error logs
    capture execution failures, warnings, and diagnostic information
    for debugging purposes.

    Args:
        index (int): Log entry index to retrieve. Specific indexing
            depends on implementation (may be sequential, timestamp-based,
            or other scheme).

    Examples:
        error_log(0)    # Get most recent error log
        error_log(-1)   # Get oldest error log (if supported)
        error_log(5)    # Get specific log entry

    Returns:
        Message: Error log entry containing timestamp, error type,
        message, and stack trace or diagnostic details.

    Note:
        - Indexing scheme depends on implementation
        - Logs may be rotated or limited in retention
        - Includes both fatal errors and warnings
        - Useful for debugging execution problems
    """
    return MANAGER.current_object().error_log(index)


def danger_call(cmd: str) -> None:
    """Execute a dangerous command and print the result.

    Executes a shell command within the context of the current object,
    typically for debugging or advanced operations. Called "dangerous"
    because commands execute with object permissions and can affect
    system state.

    Args:
        cmd (str): Shell command to execute.

    Examples:
        danger_call "ls -la"  # List directory contents
        danger_call "pwd"     # Print working directory

    Returns:
        None: Command output is printed to console with coloring.

    Note:
        - Commands execute in object's context with its permissions
        - Use with caution as commands can modify system state
        - Output is captured and displayed with color coding
        - Intended for debugging and advanced operations only
    """
    message = MANAGER.current_object().danger_call(cmd)
    print(message.colored())