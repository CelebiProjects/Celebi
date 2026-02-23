"""Formatting utilities for human-readable output."""


def format_uuid_short(uuid: str) -> str:
    """Return first 7 characters of UUID without hyphens."""
    if not uuid:
        return ""
    # Remove hyphens and take first 7 characters
    uuid_no_hyphens = uuid.replace("-", "")
    return uuid_no_hyphens[:7]


def format_node_display(uuid: str, obj_type: str = "") -> str:
    """Format node with type prefix and short UUID."""
    short = format_uuid_short(uuid)
    if obj_type:
        type_prefix = f"[{obj_type.upper()[:4]}] "  # TASK, ALGO, DATA, PROJ
        return f"{type_prefix}{short}"
    return short


def format_edge_display(parent_uuid: str, child_uuid: str,
                       parent_type: str = "", child_type: str = "") -> str:
    """Format edge as parent → child with type prefixes."""
    parent_fmt = format_node_display(parent_uuid, parent_type)
    child_fmt = format_node_display(child_uuid, child_type)
    return f"{parent_fmt} → {child_fmt}"