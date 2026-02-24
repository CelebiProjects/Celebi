"""
Utility functions for shell interface.

Miscellaneous utility functions for workarounds, history, diagnostics, etc.
"""

from ...utils.message import Message
from ._manager import MANAGER


def workaround_preshell() -> Message:
    """Execute pre-shell workaround for the current task.

    Runs pre-execution workaround code for task preparation. Workarounds
    are custom scripts or operations that run before task shell execution
    to handle special cases or environment setup.

    Args:
        None: Function takes no parameters.

    Examples:
        workaround_preshell()  # Execute pre-shell workaround

    Returns:
        Message: Message with success/error status and path data.

    Note:
        - Current object must be a task
        - Workaround code is defined in task configuration
        - Runs before task's main shell execution
        - Useful for environment preparation or data staging
    """
    message = Message()
    if not MANAGER.current_object().is_task():
        message.add("Not able to call workaround if you are not in a task.", "error")
        return message
    status, path = MANAGER.current_object().workaround_preshell()
    if not status:
        message.add(path, "error")
        return message
    message.add(path, "success")
    message.data["path"] = path
    return message


def workaround_postshell(path: str) -> Message:
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
        Message: Message with success/error status of the post-shell operation.

    Note:
        - Current object must be a task
        - Workaround code is defined in task configuration
        - Runs after task's main shell execution
        - Useful for result processing or cleanup operations
    """
    message = Message()
    if not MANAGER.current_object().is_task():
        message.add("Not able to call workaround if you are not in a task.", "error")
        return message
    MANAGER.current_object().workaround_postshell(path)
    message.add("Post-shell workaround completed", "success")
    return message


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


def bookkeep_url() -> Message:
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
        Message: Message containing the bookkeeping URL or file path.

    Note:
        - Returns project-level bookkeeping location
        - May be local file path or remote URL
        - Location depends on project configuration
        - Used for accessing detailed bookkeeping reports
    """
    message = Message()
    url = MANAGER.root_object().bookkeep_url()
    message.add(url, "normal")
    message.data["url"] = url
    return message


def tree(_depth: int = -1) -> Message:
    """Get the directory tree.

    Displays the filesystem tree structure of the current object's directory,
    showing files and subdirectories with optional depth limitation.

    Args:
        depth (int, optional): Maximum depth to display. -1 shows unlimited
            depth (entire tree). Defaults to -1.

    Examples:
        tree()      # Show complete directory tree
        tree(2)     # Show tree up to depth 2
        tree(0)     # Show only current directory

    Returns:
        Message: Formatted tree structure showing directory hierarchy,
            file names, and optionally file metadata.

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


def danger_call(cmd: str) -> Message:
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
        Message: Command output message with color coding.

    Note:
        - Commands execute in object's context with its permissions
        - Use with caution as commands can modify system state
        - Output is captured and displayed with color coding
        - Intended for debugging and advanced operations only
    """
    message = MANAGER.current_object().danger_call(cmd)
    return message


# ----------------------------------------------------------------------
# Git Integration Functions for Shell
# ----------------------------------------------------------------------

def git_merge(branch: str, strategy: str = "interactive") -> Message:
    """Merge a git branch with Celebi validation.

    Performs a git merge with Celebi-aware validation, conflict resolution,
    and impression regeneration.

    Args:
        branch (str): Name of the branch to merge from
        strategy (str, optional): Merge strategy. One of: interactive,
            auto, local, remote, union. Defaults to "interactive".

    Examples:
        git_merge feature-branch
        git_merge main --strategy=auto
        git_merge develop --strategy=local

    Returns:
        Message: Merge result with success/error status and details.

    Note:
        - Requires git repository
        - Validates DAG consistency after merge
        - Resolves conflicts interactively or automatically
        - Regenerates impressions for changed objects
        - Can be used with git hooks for automatic validation
    """
    from ...utils.git_merge_coordinator import GitMergeCoordinator, MergeStrategy

    message = Message()

    # Map string to enum
    strategy_map = {
        "interactive": MergeStrategy.INTERACTIVE,
        "auto": MergeStrategy.AUTO,
        "local": MergeStrategy.LOCAL,
        "remote": MergeStrategy.REMOTE,
        "union": MergeStrategy.UNION
    }

    merge_strategy = strategy_map.get(strategy.lower(), MergeStrategy.INTERACTIVE)

    try:
        coordinator = GitMergeCoordinator()
        results = coordinator.execute_merge(branch, merge_strategy, dry_run=False)

        if results['success']:
            message.add(f"Merge from {branch} completed successfully", "success")

            # Add details
            details = []
            if results.get('git_conflicts'):
                details.append(f"Git conflicts resolved: {len(results['git_conflicts'])}")
            if results.get('validation_conflicts'):
                details.append(f"Celebi conflicts resolved: {len(results['validation_conflicts'])}")
            if results.get('regeneration_stats'):
                stats = results['regeneration_stats']
                details.append(f"Impressions regenerated: {stats.get('regenerated', 0)}")

            if details:
                message.add("\n".join(details), "info")

            message.data.update(results)
        else:
            message.add(f"Merge from {branch} failed", "error")

            # Add error details
            if results.get('errors'):
                for error in results['errors']:
                    message.add(f"  - {error}", "error")

            if results.get('conflicts'):
                message.add(f"Unresolved conflicts: {len(results['conflicts'])}", "warning")

            message.data.update(results)

    except Exception as e:
        message.add(f"Error during git merge: {e}", "error")
        import traceback
        message.data['traceback'] = traceback.format_exc()

    return message


def git_validate() -> Message:
    """Validate Celebi project state after git operations.

    Validates the current project state for DAG consistency, config file
    validity, and impression integrity. Can be used after git operations
    to ensure project health.

    Args:
        None: Function takes no parameters.

    Examples:
        git_validate()  # Validate current project state

    Returns:
        Message: Validation results with issues found and repairs performed.

    Note:
        - Checks for DAG cycles and missing nodes
        - Validates config file syntax (JSON/YAML)
        - Verifies impression consistency
        - Can be called from git post-merge hooks
        - Attempts automatic repair of simple issues
    """
    from ...utils.git_merge_coordinator import GitMergeCoordinator

    message = Message()

    try:
        coordinator = GitMergeCoordinator()
        results = coordinator.validate_post_merge()

        if results['success']:
            message.add("Project validation successful", "success")

            if results.get('repairs'):
                repairs = "\n".join([f"  - {r}" for r in results['repairs']])
                message.add(f"Automatic repairs performed:\n{repairs}", "info")
        else:
            message.add("Project validation failed", "error")

            if results.get('issues'):
                issues = "\n".join([f"  - {i}" for i in results['issues']])
                message.add(f"Issues found:\n{issues}", "error")

            if results.get('repairs'):
                repairs = "\n".join([f"  - {r}" for r in results['repairs']])
                message.add(f"Attempted repairs:\n{repairs}", "warning")

        message.data.update(results)

    except Exception as e:
        message.add(f"Error during validation: {e}", "error")

    return message


def git_status() -> Message:
    """Show git integration status and merge readiness.

    Displays information about git repository status, Celebi git integration
    configuration, and merge readiness.

    Args:
        None: Function takes no parameters.

    Examples:
        git_status()  # Show git integration status

    Returns:
        Message: Status information including git repo info, integration
        configuration, and potential issues.

    Note:
        - Shows current git branch and remote
        - Indicates if git integration is enabled
        - Checks for uncommitted changes
        - Detects potential merge issues
        - Provides recommendations for git configuration
    """
    from ...utils.git_optional import GitOptionalIntegration
    from ...utils.git_merge_coordinator import GitMergeCoordinator

    message = Message()

    try:
        git_integration = GitOptionalIntegration()
        git_info = git_integration.get_git_info()
        config = git_integration.get_config()

        status_lines = []

        # Git repository info
        if git_info['is_git_repo']:
            status_lines.append("✓ Git repository detected")
            status_lines.append(
                f"  Current branch: {git_info.get('current_branch', 'unknown')}"
            )
            status_lines.append(
                f"  Remote: {git_info.get('remote_url', 'none')}"
            )
            status_lines.append(
                "  Uncommitted changes: "
                f"{'yes' if git_info['has_uncommitted_changes'] else 'no'}"
            )
        else:
            status_lines.append("✗ Not a git repository")
            status_lines.append("  Run 'git init' to initialize git in this directory")
            message.add("\n".join(status_lines), "warning")
            message.data.update(git_info)
            return message

        # Integration status
        status_lines.append(
            "\nCelebi Git Integration: "
            f"{'ENABLED' if config['enabled'] else 'DISABLED'}"
        )
        status_lines.append(f"  Hooks installed: {'yes' if config['hooks_installed'] else 'no'}")
        status_lines.append(f"  Auto-validate: {'yes' if config['auto_validate'] else 'no'}")
        status_lines.append(f"  Auto-regenerate: {'yes' if config['auto_regenerate'] else 'no'}")
        status_lines.append(f"  Merge strategy: {config['merge_strategy']}")

        # Merge readiness
        coordinator = GitMergeCoordinator()
        merge_status = coordinator.get_merge_status()

        status_lines.append(
            "\nMerge Readiness: "
            f"{'READY' if merge_status['ready_to_merge'] else 'NOT READY'}"
        )
        if merge_status['has_uncommitted_changes']:
            status_lines.append("  ⚠ Uncommitted changes detected")
        if merge_status['merge_in_progress']:
            status_lines.append("  ⚠ Merge already in progress")

        # Potential issues
        issues = git_integration.detect_potential_issues()
        if issues:
            status_lines.append(f"\nPotential Issues ({len(issues)}):")
            for issue in issues:
                level = issue['level']
                msg = issue['message']
                if level == 'error':
                    status_lines.append(f"  ✗ {msg}")
                else:
                    status_lines.append(f"  ⚠ {msg}")

                if 'suggestion' in issue:
                    status_lines.append(f"     Suggestion: {issue['suggestion']}")

        message.add("\n".join(status_lines), "info")
        message.data.update({
            'git_info': git_info,
            'config': config,
            'merge_status': merge_status,
            'issues': issues
        })

    except Exception as e:
        message.add(f"Error getting git status: {e}", "error")

    return message


def git_enable() -> Message:
    """Enable Celebi git integration for current project.

    Enables git integration features including automatic validation,
    impression regeneration, and git hooks.

    Args:
        None: Function takes no parameters.

    Examples:
        git_enable()  # Enable git integration

    Returns:
        Message: Success/error status of enabling git integration.

    Note:
        - Requires git repository
        - Can install git hooks for automatic validation
        - Sets configuration options for merge behavior
        - Provides recommended .gitignore additions
    """
    from ...utils.git_optional import GitOptionalIntegration

    message = Message()

    try:
        git_integration = GitOptionalIntegration()

        if not git_integration.is_git_repository():
            message.add("Error: Not a git repository. Run 'git init' first.", "error")
            return message

        if git_integration.enable_integration():
            message.add("Git integration enabled", "success")

            # Offer to install hooks
            message.add("Install git hooks for automatic validation? (Y/n): ", "prompt")
            message.data['needs_hook_decision'] = True

            # Show recommended settings
            recommendations = git_integration.get_recommended_settings()
            rec_lines = ["Recommended .gitignore additions:"]
            rec_lines.extend(
                f"  {line}" for line in recommendations['.gitignore_additions']
            )
            message.add("\n".join(rec_lines) + "\n", "info")

            message.data['recommendations'] = recommendations
        else:
            message.add("Failed to enable git integration", "error")

    except Exception as e:
        message.add(f"Error enabling git integration: {e}", "error")

    return message


def git_disable() -> Message:
    """Disable Celebi git integration for current project.

    Disables git integration features and removes git hooks.

    Args:
        None: Function takes no parameters.

    Examples:
        git_disable()  # Disable git integration

    Returns:
        Message: Success/error status of disabling git integration.

    Note:
        - Removes git hooks if installed
        - Disables automatic validation
        - Preserves project data (does not delete anything)
    """
    from ...utils.git_optional import GitOptionalIntegration

    message = Message()

    try:
        git_integration = GitOptionalIntegration()

        if git_integration.disable_integration():
            message.add("Git integration disabled", "success")
            message.add("  Hooks removed if installed", "info")
            message.add("  Auto-validation disabled", "info")
        else:
            message.add("Failed to disable git integration", "error")

    except Exception as e:
        message.add(f"Error disabling git integration: {e}", "error")

    return message


def git_hooks(install: bool = True) -> Message:
    """Install or uninstall Celebi git hooks.

    Manages git hooks for automatic Celebi validation after git operations.

    Args:
        install (bool, optional): True to install hooks, False to uninstall.
            Defaults to True.

    Examples:
        git_hooks()          # Install hooks
        git_hooks(False)     # Uninstall hooks

    Returns:
        Message: Success/error status of hook management.

    Note:
        - Installs post-merge hook for automatic validation
        - Requires git repository
        - Hooks only run if git integration is enabled
        - Post-merge hook validates project state after merges
    """
    from ...utils.git_optional import GitOptionalIntegration

    message = Message()

    try:
        git_integration = GitOptionalIntegration()

        if not git_integration.is_git_repository():
            message.add("Error: Not a git repository", "error")
            return message

        if install:
            if git_integration.install_hooks():
                message.add("Git hooks installed", "success")
                message.add("  Post-merge hook will validate Celebi state after git merges", "info")
            else:
                message.add("Failed to install git hooks", "error")
        else:
            if git_integration.uninstall_hooks():
                message.add("Git hooks uninstalled", "success")
            else:
                message.add("Failed to uninstall git hooks", "error")

    except Exception as e:
        message.add(f"Error managing git hooks: {e}", "error")

    return message
