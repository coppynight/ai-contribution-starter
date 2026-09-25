def pending_tasks(tasks):
    """Return the pending view, preserving the input order and records."""
    return [dict(task) for task in tasks if not task["completed"]]
