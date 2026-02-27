#!/usr/bin/env python3
"""Simple test script for parse_task_text function."""

from task_parser import parse_task_text

def test_parse_task_text():
    """Test the parse_task_text function with sample inputs."""

    test_cases = [
        "Buy milk !! #2026-03-01 @shopping",
        "Simple task",
        "!!! @tag #invalid-date",
        "Task !!! #tomorrow @work #2026-12-25",
        "Call dentist #today @health",
        "Prepare presentation #monday @work",
        "Review code #next_week @project",
        "Grocery shopping #friday @personal",
    ]

    for text in test_cases:
        print(f"Input: '{text}'")
        task = parse_task_text(text)
        print(f"  Title: '{task.title}'")
        print(f"  Priority: {task.priority}")
        print(f"  Due Date: {task.due_date}")
        print(f"  Tags: {task.tags}")
        print()

if __name__ == "__main__":
    test_parse_task_text()