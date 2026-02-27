#!/usr/bin/env python3
"""Test suite for task list merging functionality."""

import copy
from datetime import datetime, timedelta
from task_list_merge import merge_task_lists, resolve_task_conflict
from models import Task, TaskStatus, TaskPriority

def create_test_task(title, status=TaskStatus.TODO, updated_at=None, tags=None, task_id=None):
    """Helper to create test tasks with minimal setup."""
    task = Task(title)
    task.status = status
    task.updated_at = updated_at or datetime.now()
    task.tags = tags or []
    if task_id:
        task.id = task_id
    return task

def test_scenario_1_local_newer_remote_done():
    """Test: Local newer, remote completed - status override."""
    print("=== Scenario 1: Local newer, remote completed ===")

    # Create test tasks
    local = create_test_task(
        "Buy milk",
        status=TaskStatus.TODO,
        updated_at=datetime(2026, 2, 26, 10, 0),
        tags=["shopping"]
    )

    remote = create_test_task(
        "Buy groceries",
        status=TaskStatus.DONE,
        updated_at=datetime(2026, 2, 25, 15, 0),
        tags=["errands"]
    )

    # Test conflict resolution
    merged, update_local, update_remote = resolve_task_conflict(local, remote)

    print(f"Local: {local.title}, {local.status.value}, tags={local.tags}")
    print(f"Remote: {remote.title}, {remote.status.value}, tags={remote.tags}")
    print(f"Merged: {merged.title}, {merged.status.value}, tags={merged.tags}")
    print(f"Update local: {update_local}, Update remote: {update_remote}")
    print()

def test_scenario_2_equal_timestamps():
    """Test: Equal timestamps with ID-based tie-breaking."""
    print("=== Scenario 2: Equal timestamps (local ID wins) ===")

    timestamp = datetime(2026, 2, 26, 12, 0)

    local = create_test_task(
        "Call doctor",
        status=TaskStatus.TODO,
        updated_at=timestamp,
        tags=["health"],
        task_id="local_task_001"
    )

    remote = create_test_task(
        "Call dentist",
        status=TaskStatus.TODO,
        updated_at=timestamp,
        tags=["medical"],
        task_id="remote_task_002"  # lexicographically after local
    )

    merged, update_local, update_remote = resolve_task_conflict(local, remote)

    print(f"Local ID: {local.id}, title: {local.title}, tags={local.tags}")
    print(f"Remote ID: {remote.id}, title: {remote.title}, tags={remote.tags}")
    print(f"Merged: title='{merged.title}', tags={merged.tags}")
    print(f"Update local: {update_local}, Update remote: {update_remote}")
    print("  (Remote wins tie-breaker since 'remote_task_002' > 'local_task_001')")
    print()

    # Test reverse scenario where remote wins
    print("=== Scenario 2b: Equal timestamps (remote ID wins) ===")

    local2 = create_test_task(
        "Call doctor",
        status=TaskStatus.TODO,
        updated_at=timestamp,
        tags=["health"],
        task_id="z_local_task"  # lexicographically after remote
    )

    remote2 = create_test_task(
        "Call dentist",
        status=TaskStatus.TODO,
        updated_at=timestamp,
        tags=["medical"],
        task_id="a_remote_task"  # lexicographically before local
    )

    merged2, update_local2, update_remote2 = resolve_task_conflict(local2, remote2)

    print(f"Local ID: {local2.id}, title: {local2.title}, tags={local2.tags}")
    print(f"Remote ID: {remote2.id}, title: {remote2.title}, tags={remote2.tags}")
    print(f"Merged: title='{merged2.title}', tags={merged2.tags}")
    print(f"Update local: {update_local2}, Update remote: {update_remote2}")
    print("  (Local wins tie-breaker since 'z_local_task' > 'a_remote_task')")
    print()

def test_scenario_4_deletion_conflicts():
    """Test: Handling deletion conflicts between sources."""
    print("=== Scenario 4: Deletion Conflicts ===")

    # Create base task
    base_task = create_test_task(
        "Base task",
        status=TaskStatus.TODO,
        updated_at=datetime(2026, 2, 26, 10, 0),
        tags=["base"]
    )

    # Local: task exists and was recently updated
    local = create_test_task(
        "Updated locally",
        status=TaskStatus.IN_PROGRESS,
        updated_at=datetime(2026, 2, 26, 14, 0),
        tags=["local"]
    )
    local.id = base_task.id

    # Remote: task was deleted more recently
    remote = create_test_task(
        "Should be deleted",
        status=TaskStatus.TODO,
        updated_at=datetime(2026, 2, 26, 10, 0),
        tags=["base"]
    )
    remote.id = base_task.id
    remote.mark_as_deleted()  # Simulate deletion at 15:00
    remote.deleted_at = datetime(2026, 2, 26, 15, 0)
    remote.updated_at = remote.deleted_at

    merged, update_local, update_remote = resolve_task_conflict(local, remote)

    print(f"Local: '{local.title}', status={local.status.value}, updated={local.updated_at}")
    print(f"Remote: DELETED at {remote.deleted_at}")
    print(f"Merged: '{merged.title}', status={merged.status.value}, deleted={merged.is_deleted()}")
    print(f"Update local: {update_local}, Update remote: {update_remote}")
    print("  (Remote deletion is more recent, so merged task should be deleted)")
    print()

    # Test reverse: local deletion, remote update
    print("=== Scenario 4b: Local deletion, remote update ===")

    local_del = create_test_task(
        "Should be deleted locally",
        status=TaskStatus.TODO,
        updated_at=datetime(2026, 2, 26, 10, 0),
        tags=["base"]
    )
    local_del.id = base_task.id
    local_del.mark_as_deleted()
    local_del.deleted_at = datetime(2026, 2, 26, 16, 0)
    local_del.updated_at = local_del.deleted_at

    remote_update = create_test_task(
        "Remote update",
        status=TaskStatus.DONE,
        updated_at=datetime(2026, 2, 26, 15, 0),  # Less recent than local deletion
        tags=["remote"]
    )
    remote_update.id = base_task.id

    merged2, update_local2, update_remote2 = resolve_task_conflict(local_del, remote_update)

    print(f"Local: DELETED at {local_del.deleted_at}")
    print(f"Remote: '{remote_update.title}', status={remote_update.status.value}, updated={remote_update.updated_at}")
    print(f"Merged: '{merged2.title}', status={merged2.status.value}, deleted={merged2.is_deleted()}")
    print(f"Update local: {update_local2}, Update remote: {update_remote2}")
    print("  (Local deletion is more recent, so merged task should stay deleted)")
    print()

def test_full_merge_workflow():
    """Test the complete merge workflow with multiple tasks."""
    print("=== Full Merge Workflow ===")

    # Create test data
    local_tasks = {
        "task1": create_test_task("Buy milk", tags=["shopping"]),
        "task2": create_test_task("Call doctor", tags=["health"]),
        "task4": create_test_task("Local only", tags=["local"]),
    }

    remote_tasks = {
        "task1": create_test_task("Buy groceries", status=TaskStatus.DONE, tags=["errands"]),
        "task3": create_test_task("Remote only", tags=["remote"]),
        "task4": create_test_task("Conflicting", tags=["conflict"]),
    }

    # Perform merge
    merged, to_create_remote, to_update_remote, to_create_local, to_update_local = merge_task_lists(
        local_tasks, remote_tasks
    )

    print(f"Merged tasks: {list(merged.keys())}")
    print(f"To create in remote: {list(to_create_remote.keys())}")
    print(f"To update in remote: {list(to_update_remote.keys())}")
    print(f"To create in local: {list(to_create_local.keys())}")
    print(f"To update in local: {list(to_update_local.keys())}")
    print()

def run_all_tests():
    """Run all test scenarios."""
    print("Running Task Merge Algorithm Tests")
    print("=" * 50)

    test_scenario_1_local_newer_remote_done()
    test_scenario_2_equal_timestamps()
    test_scenario_4_deletion_conflicts()
    test_full_merge_workflow()

    print("All tests completed!")

if __name__ == "__main__":
    run_all_tests()