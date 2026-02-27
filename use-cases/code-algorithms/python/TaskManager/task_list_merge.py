import copy

from models import TaskStatus, TaskPriority

def merge_task_lists(local_tasks, remote_tasks, conflict_resolution_mode="auto"):
    """
    Merge two task lists with conflict resolution.

    Args:
        local_tasks: Dictionary of tasks from local source {task_id: task}
        remote_tasks: Dictionary of tasks from remote source {task_id: task}
        conflict_resolution_mode: "auto" for automatic resolution, "manual" for user choice

    Returns:
        tuple: (
            merged tasks dictionary,
            tasks to be created in remote,
            tasks to be updated in remote,
            tasks to be created in local,
            tasks to be updated in local,
            conflicts requiring user choice (if manual mode)
        )
    """
    merged_tasks = {}
    to_create_remote = {}
    to_update_remote = {}
    to_create_local = {}
    to_update_local = {}
    conflicts = []

    # Step 1: Identify all unique task IDs across both sources
    all_task_ids = set(local_tasks.keys()) | set(remote_tasks.keys())

    for task_id in all_task_ids:
        local_task = local_tasks.get(task_id)
        remote_task = remote_tasks.get(task_id)

        # Case 1: Task exists only locally - add to remote
        if local_task and not remote_task:
            merged_tasks[task_id] = local_task
            to_create_remote[task_id] = local_task

        # Case 2: Task exists only in remote - add to local
        elif not local_task and remote_task:
            merged_tasks[task_id] = remote_task
            to_create_local[task_id] = remote_task

        # Case 3: Task exists in both - resolve conflicts
        else:
            merged_task, should_update_local, should_update_remote, task_conflicts = resolve_task_conflict(
                local_task, remote_task, conflict_resolution_mode
            )

            merged_tasks[task_id] = merged_task
            conflicts.extend(task_conflicts)

            if should_update_local:
                to_update_local[task_id] = merged_task

            if should_update_remote:
                to_update_remote[task_id] = merged_task

    return (
        merged_tasks,
        to_create_remote,
        to_update_remote,
        to_create_local,
        to_update_local,
        conflicts
    )

def resolve_task_conflict(local_task, remote_task, conflict_resolution_mode="auto"):
    """Resolve conflicts between two versions of the same task."""
    merged_task = copy.deepcopy(local_task)
    update_flags = MutableFlags()
    conflicts = []

    # Handle deletion conflicts first - deletion wins if more recent
    if remote_task.is_deleted() and not local_task.is_deleted():
        if remote_task.deleted_at > local_task.updated_at:
            # Remote deletion is more recent - delete the task
            merged_task.mark_as_deleted()
            update_flags.local = True
        # If local is more recent, keep local (don't delete)
    elif local_task.is_deleted() and not remote_task.is_deleted():
        if local_task.deleted_at > remote_task.updated_at:
            # Local deletion is more recent - keep deleted
            update_flags.remote = True
        else:
            # Remote is more recent - undelete and update with remote data
            merged_task.deleted_at = None
            copy_basic_fields(merged_task, remote_task)
            update_flags.local = True

    # If neither is deleted, or both are deleted, proceed with normal conflict resolution
    if not merged_task.is_deleted():
        field_conflicts = resolve_field_conflicts(merged_task, local_task, remote_task, update_flags, conflict_resolution_mode)
        status_conflicts = resolve_status_conflicts(merged_task, local_task, remote_task, update_flags, conflict_resolution_mode)
        tag_conflicts = resolve_tag_conflicts(merged_task, local_task, remote_task, update_flags)
        update_timestamps(merged_task, local_task, remote_task)
        
        conflicts.extend(field_conflicts)
        conflicts.extend(status_conflicts)

    return merged_task, update_flags.local, update_flags.remote, conflicts

class MutableFlags:
    def __init__(self):
        self.local = False
        self.remote = False

def copy_basic_fields(target_task, source_task):
    """Copy title, description, priority, and due_date from source to target."""
    target_task.title = source_task.title
    target_task.description = source_task.description
    target_task.priority = source_task.priority
    target_task.due_date = source_task.due_date

def resolve_field_conflicts(merged_task, local_task, remote_task, update_flags, conflict_resolution_mode):
    """Resolve conflicts for basic fields using timestamp comparison."""
    conflicts = []
    
    if remote_task.updated_at > local_task.updated_at:
        # Remote is newer - copy its fields
        copy_basic_fields(merged_task, remote_task)
        update_flags.local = True
    elif local_task.updated_at > remote_task.updated_at:
        # Local is newer - keep local fields, update remote
        update_flags.remote = True
    else:
        # Timestamps are equal - use task ID as tie-breaker for deterministic behavior
        if remote_task.id > local_task.id:
            # Remote task "wins" tie-breaker, update local fields
            copy_basic_fields(merged_task, remote_task)
            update_flags.local = True
        else:
            # Local task wins tie-breaker or IDs are equal, update remote
            update_flags.remote = True
    
    # Check for user choice conflicts in title/description
    if conflict_resolution_mode == "manual":
        if local_task.title != remote_task.title:
            conflicts.append({
                'type': 'title_conflict',
                'task_id': local_task.id,
                'field': 'title',
                'local_value': local_task.title,
                'remote_value': remote_task.title,
                'chosen': merged_task.title,
                'reason': 'Titles differ significantly'
            })
        if local_task.description != remote_task.description:
            conflicts.append({
                'type': 'description_conflict',
                'task_id': local_task.id,
                'field': 'description',
                'local_value': local_task.description,
                'remote_value': remote_task.description,
                'chosen': merged_task.description,
                'reason': 'Descriptions differ'
            })
    
    return conflicts

def resolve_status_conflicts(merged_task, local_task, remote_task, update_flags, conflict_resolution_mode):
    """Resolve status conflicts with special handling for completion."""
    conflicts = []
    
    if remote_task.status == TaskStatus.DONE and local_task.status != TaskStatus.DONE:
        # Remote completion wins
        merged_task.status = TaskStatus.DONE
        merged_task.completed_at = remote_task.completed_at
        update_flags.local = True
    elif local_task.status == TaskStatus.DONE and remote_task.status != TaskStatus.DONE:
        # Local completion wins (already set in merged_task)
        update_flags.remote = True
    elif remote_task.status != local_task.status:
        # Different non-completed statuses - most recent wins
        if remote_task.updated_at > local_task.updated_at:
            merged_task.status = remote_task.status
            update_flags.local = True
        else:
            update_flags.remote = True
    
    # Check for user choice conflicts in status
    if conflict_resolution_mode == "manual":
        if local_task.status != remote_task.status:
            # Consider status conflicts significant if they represent major state changes
            significant_status_change = (
                (local_task.status == TaskStatus.DONE and remote_task.status != TaskStatus.DONE) or
                (remote_task.status == TaskStatus.DONE and local_task.status != TaskStatus.DONE) or
                (local_task.status == TaskStatus.CANCELLED and remote_task.status != TaskStatus.CANCELLED) or
                (remote_task.status == TaskStatus.CANCELLED and local_task.status != TaskStatus.CANCELLED)
            )
            
            if significant_status_change:
                conflicts.append({
                    'type': 'status_conflict',
                    'task_id': local_task.id,
                    'field': 'status',
                    'local_value': local_task.status.value,
                    'remote_value': remote_task.status.value,
                    'chosen': merged_task.status.value,
                    'reason': 'Significant status change requiring user choice'
                })
    
    return conflicts

def resolve_tag_conflicts(merged_task, local_task, remote_task, update_flags):
    """Merge tags from both sources and set update flags if changed."""
    local_tags = set(local_task.tags)
    remote_tags = set(remote_task.tags)
    merged_tags = local_tags | remote_tags
    
    merged_task.tags = list(merged_tags)
    
    if merged_tags != local_tags:
        update_flags.local = True
    if merged_tags != remote_tags:
        update_flags.remote = True

def update_timestamps(merged_task, local_task, remote_task):
    """Set merged task timestamp to the most recent."""
    merged_task.updated_at = max(local_task.updated_at, remote_task.updated_at)
