# task_manager/cli.py
import argparse
from datetime import datetime

from task_manager import TaskManager
from models import TaskStatus, TaskPriority


def format_task(task):
    """Format a task object for display in the CLI.

    Converts a :class:`models.Task` instance into a human-readable string
    that includes status, priority, title, description, due date, tags, and
    creation timestamp. Status and priority are represented by simple
    symbols to keep output compact when listing multiple tasks.

    Args:
        task (models.Task): The task instance to format. The object is
            expected to have attributes ``id``, ``title``, ``description``,
            ``status``, ``priority``, ``due_date``, ``tags`` and
            ``created_at``.

    Returns:
        str: A multi-line string suitable for printing to the console. The
            first line shows the status symbol, truncated task ID, priority
            indicator, and title. Subsequent lines include the description,
            due date or placeholder text, tags or a fallback message, and
            creation timestamp.

    Notes:
        - ``task.id`` is truncated to the first eight characters for brevity.
        - ``due_date`` may be ``None``; in that case "No due date" is shown.
        - ``tags`` is expected to be an iterable of strings; an empty list
          results in "No tags" text.
        - The formatting logic assumes ``status`` and ``priority`` are
          members of :class:`TaskStatus` and :class:`TaskPriority`,
          respectively.
    """
    status_symbol = {
        TaskStatus.TODO: "[ ]",
        TaskStatus.IN_PROGRESS: "[>]",
        TaskStatus.REVIEW: "[?]",
        TaskStatus.DONE: "[✓]"
    }

    priority_symbol = {
        TaskPriority.LOW: "!",
        TaskPriority.MEDIUM: "!!",
        TaskPriority.HIGH: "!!!",
        TaskPriority.URGENT: "!!!!"
    }

    due_str = f"Due: {task.due_date.strftime('%Y-%m-%d')}" if task.due_date else "No due date"
    tags_str = f"Tags: {', '.join(task.tags)}" if task.tags else "No tags"

    return (
        f"{status_symbol[task.status]} {task.id[:8]} - {priority_symbol[task.priority]} {task.title}\n"
        f"  {task.description}\n"
        f"  {due_str} | {tags_str}\n"
        f"  Created: {task.created_at.strftime('%Y-%m-%d %H:%M')}"
    )

def main():
    """Entry point for the Task Manager command-line interface.

    This function configures and parses command-line arguments for a
    variety of task management operations (create, list, update status,
    update priority, due date, tag management, show, delete, stats). It
    instantiates a :class:`TaskManager` and dispatches the requested
    command, handling output formatting and error reporting.

    The CLI supports filtering, tagging, and statistics reporting to
    facilitate task organization. Arguments are validated using argparse
    to ensure correct types and choices where appropriate.

    Returns:
        None: This function does not return a value; it exits the
        program after printing results or help text.

    Raises:
        SystemExit: ``argparse`` may raise this when parsing fails or
            when ``--help`` is invoked. Other errors raised by
            :class:`TaskManager` methods are propagated.

    Example:
        >>> # create a new task
        >>> python cli.py create "Buy groceries" -d "Milk, eggs" -p 2 -u 2025-01-01 -t shopping,errands
        Created task with ID: 123e4567

        >>> # list overdue tasks
        >>> python cli.py list -o

    Notes:
        - The ``TaskManager`` class is responsible for data persistence
          and business logic; the CLI only orchestrates user input and
          output.
        - Date arguments must follow the YYYY-MM-DD format; invalid dates will
          result in a failure message.
        - Tags supplied as a comma-separated string are trimmed of whitespace.
    """
    parser = argparse.ArgumentParser(description="Task Manager CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create task command
    create_parser = subparsers.add_parser("create", help="Create a new task")
    create_parser.add_argument("title", help="Task title")
    create_parser.add_argument("-d", "--description", help="Task description", default="")
    create_parser.add_argument("-p", "--priority", help="Task priority (1-4)", type=int, choices=[1, 2, 3, 4], default=2)
    create_parser.add_argument("-u", "--due", help="Due date (YYYY-MM-DD)", default=None)
    create_parser.add_argument("-t", "--tags", help="Comma-separated tags", default="")

    # List tasks command
    list_parser = subparsers.add_parser("list", help="List all tasks")
    list_parser.add_argument("-s", "--status", help="Filter by status", choices=["todo", "in_progress", "review", "done"])
    list_parser.add_argument("-p", "--priority", help="Filter by priority", type=int, choices=[1, 2, 3, 4])
    list_parser.add_argument("-o", "--overdue", help="Show only overdue tasks", action="store_true")

    # Update task commands
    update_status_parser = subparsers.add_parser("status", help="Update task status")
    update_status_parser.add_argument("task_id", help="Task ID")
    update_status_parser.add_argument("status", help="New status", choices=["todo", "in_progress", "review", "done"])

    update_priority_parser = subparsers.add_parser("priority", help="Update task priority")
    update_priority_parser.add_argument("task_id", help="Task ID")
    update_priority_parser.add_argument("priority", help="New priority", type=int, choices=[1, 2, 3, 4])

    update_due_parser = subparsers.add_parser("due", help="Update task due date")
    update_due_parser.add_argument("task_id", help="Task ID")
    update_due_parser.add_argument("due_date", help="New due date (YYYY-MM-DD)")

    # Tag management
    add_tag_parser = subparsers.add_parser("tag", help="Add tag to task")
    add_tag_parser.add_argument("task_id", help="Task ID")
    add_tag_parser.add_argument("tag", help="Tag to add")

    remove_tag_parser = subparsers.add_parser("untag", help="Remove tag from task")
    remove_tag_parser.add_argument("task_id", help="Task ID")
    remove_tag_parser.add_argument("tag", help="Tag to remove")

    # Other commands
    show_parser = subparsers.add_parser("show", help="Show task details")
    show_parser.add_argument("task_id", help="Task ID")

    delete_parser = subparsers.add_parser("delete", help="Delete a task")
    delete_parser.add_argument("task_id", help="Task ID")

    stats_parser = subparsers.add_parser("stats", help="Show task statistics")

    args = parser.parse_args()
    task_manager = TaskManager()

    if args.command == "create":
        tags = [tag.strip() for tag in args.tags.split(",")] if args.tags else []
        task_id = task_manager.create_task(
            args.title,
            args.description,
            args.priority,
            args.due,
            tags
        )
        if task_id:
            print(f"Created task with ID: {task_id}")

    elif args.command == "list":
        tasks = task_manager.list_tasks(args.status, args.priority, args.overdue)
        if tasks:
            for task in tasks:
                print(format_task(task))
                print("-" * 50)
        else:
            print("No tasks found matching the criteria.")

    elif args.command == "status":
        if task_manager.update_task_status(args.task_id, args.status):
            print(f"Updated task status to {args.status}")
        else:
            print("Failed to update task status. Task not found.")

    elif args.command == "priority":
        if task_manager.update_task_priority(args.task_id, args.priority):
            print(f"Updated task priority to {args.priority}")
        else:
            print("Failed to update task priority. Task not found.")

    elif args.command == "due":
        if task_manager.update_task_due_date(args.task_id, args.due_date):
            print(f"Updated task due date to {args.due_date}")
        else:
            print("Failed to update task due date. Task not found or invalid date.")

    elif args.command == "tag":
        if task_manager.add_tag_to_task(args.task_id, args.tag):
            print(f"Added tag '{args.tag}' to task")
        else:
            print("Failed to add tag. Task not found.")

    elif args.command == "untag":
        if task_manager.remove_tag_from_task(args.task_id, args.tag):
            print(f"Removed tag '{args.tag}' from task")
        else:
            print("Failed to remove tag. Task or tag not found.")

    elif args.command == "show":
        task = task_manager.get_task_details(args.task_id)
        if task:
            print(format_task(task))
        else:
            print("Task not found.")

    elif args.command == "delete":
        if task_manager.delete_task(args.task_id):
            print(f"Deleted task {args.task_id}")
        else:
            print("Failed to delete task. Task not found.")

    elif args.command == "stats":
        stats = task_manager.get_statistics()
        print(f"Total tasks: {stats['total']}")
        print(f"By status:")
        for status, count in stats['by_status'].items():
            print(f"  {status}: {count}")
        print(f"By priority:")
        for priority, count in stats['by_priority'].items():
            print(f"  {priority}: {count}")
        print(f"Overdue tasks: {stats['overdue']}")
        print(f"Completed in last 7 days: {stats['completed_last_week']}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()