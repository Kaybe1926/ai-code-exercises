#!/usr/bin/env python3
"""
Demonstration of User Choice Conflicts in Task List Merging

This script shows how the merge algorithm can detect conflicts that require
user intervention when using manual conflict resolution mode.
"""

from datetime import datetime, timedelta
from models import Task, TaskStatus, TaskPriority
from task_list_merge import merge_task_lists

def demo_user_choice_conflicts():
    """Demonstrate user choice conflicts in action."""
    print("=== Task List Merge - User Choice Conflicts Demo ===\n")

    # Create conflicting tasks
    now = datetime.now()

    # Local task (older)
    local_task = Task("Buy groceries", "Need milk and bread", TaskPriority.MEDIUM)
    local_task.id = "task1"
    local_task.updated_at = now - timedelta(hours=2)
    local_task.status = TaskStatus.TODO
    local_task.tags = ["shopping", "urgent"]

    # Remote task (newer)
    remote_task = Task("Purchase groceries", "Milk, bread, and eggs needed", TaskPriority.HIGH)
    remote_task.id = "task1"
    remote_task.updated_at = now - timedelta(minutes=30)
    remote_task.status = TaskStatus.DONE
    remote_task.completed_at = now - timedelta(minutes=30)
    remote_task.tags = ["shopping", "weekly"]

    print("Local Task:")
    print(f"  Title: {local_task.title}")
    print(f"  Description: {local_task.description}")
    print(f"  Status: {local_task.status.value}")
    print(f"  Priority: {local_task.priority.value}")
    print(f"  Tags: {local_task.tags}")
    print(f"  Updated: {local_task.updated_at}")
    print()

    print("Remote Task:")
    print(f"  Title: {remote_task.title}")
    print(f"  Description: {remote_task.description}")
    print(f"  Status: {remote_task.status.value}")
    print(f"  Priority: {remote_task.priority.value}")
    print(f"  Tags: {remote_task.tags}")
    print(f"  Updated: {remote_task.updated_at}")
    print()

    # Test automatic mode
    print("=== Automatic Mode (conflict_resolution_mode='auto') ===")
    local_tasks = {"task1": local_task}
    remote_tasks = {"task1": remote_task}

    merged, to_create_remote, to_update_remote, to_create_local, to_update_local, conflicts = merge_task_lists(
        local_tasks, remote_tasks, conflict_resolution_mode="auto"
    )

    print(f"Merged Task (Auto): {merged['task1'].title}")
    print(f"Status: {merged['task1'].status.value}")
    print(f"Priority: {merged['task1'].priority.value}")
    print(f"Tags: {merged['task1'].tags}")
    print(f"Conflicts Detected: {len(conflicts)}")
    print()

    # Test manual mode
    print("=== Manual Mode (conflict_resolution_mode='manual') ===")
    merged, to_create_remote, to_update_remote, to_create_local, to_update_local, conflicts = merge_task_lists(
        local_tasks, remote_tasks, conflict_resolution_mode="manual"
    )

    print(f"Merged Task (Manual): {merged['task1'].title}")
    print(f"Status: {merged['task1'].status.value}")
    print(f"Priority: {merged['task1'].priority.value}")
    print(f"Tags: {merged['task1'].tags}")
    print(f"Conflicts Detected: {len(conflicts)}")
    print()

    if conflicts:
        print("Conflicts requiring user choice:")
        for i, conflict in enumerate(conflicts, 1):
            print(f"  {i}. {conflict['type'].replace('_', ' ').title()}")
            print(f"     Field: {conflict['field']}")
            print(f"     Local: {conflict['local_value']}")
            print(f"     Remote: {conflict['remote_value']}")
            print(f"     Chosen: {conflict['chosen']}")
            print(f"     Reason: {conflict['reason']}")
            print()

if __name__ == "__main__":
    demo_user_choice_conflicts()