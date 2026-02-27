import argparse
from datetime import datetime, timedelta

from models import TaskPriority, Task, TaskStatus
from storage import TaskStorage


class TaskManager:
    def __init__(self, storage_path="tasks.json"):
        self.storage = TaskStorage(storage_path)

    def create_task(self, title, description="", priority_value=2,
                   due_date_str=None, tags=None):
        priority = TaskPriority(priority_value)
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                print("Invalid date format. Use YYYY-MM-DD")
                return None

        task = Task(title, description, priority, due_date, tags)
        task_id = self.storage.add_task(task)
        return task_id

    def list_tasks(self, status_filter=None, priority_filter=None, show_overdue=False):
        if show_overdue:
            return self.storage.get_overdue_tasks()

        if status_filter:
            status = TaskStatus(status_filter)
            return self.storage.get_tasks_by_status(status)

        if priority_filter:
            priority = TaskPriority(priority_filter)
            return self.storage.get_tasks_by_priority(priority)

        return self.storage.get_all_tasks()

    def update_task_status(self, task_id, new_status_value):
        """Change the status of a task, handling completion specially.

        Converts the provided status value into a :class:`TaskStatus` enum
        member and updates the corresponding task in storage. When the
        new status is ``DONE`` the method retrieves the task object,
        marks it as completed (which updates timestamps) and forces an
        immediate save of the storage backend. For any other status the
        update is delegated to ``self.storage.update_task``.

        Args:
            task_id (str): Identifier of the task to update.
            new_status_value (str): New status value; must be one of the
                values accepted by :class:`TaskStatus` (e.g., ``"todo"``,
                ``"in_progress"``).

        Returns:
            bool | None: ``True`` if the status was successfully changed.
            ``False`` if the storage delegation indicated failure. If the
            task to mark done is not found, ``None`` is returned.
            A ``ValueError`` from invalid ``new_status_value`` is propagated.

        Raises:
            ValueError: Raised when ``new_status_value`` cannot be converted
                to a ``TaskStatus`` member.

        Example:
            >>> manager.update_task_status("abc123", "in_progress")
            True
            >>> manager.update_task_status("abc123", "done")
            True

        Notes:
            - The method treats the ``DONE`` status specially because
              tasks need their ``completed_at`` timestamp set; storage
              updates for other statuses do not trigger timestamp changes.
            - There is no check to prevent setting the same status again.
            - The return value is inconsistent when the task is missing in
              the DONE branch; callers should consider this when using the
              result.
        """
        new_status = TaskStatus(new_status_value)
        if new_status == TaskStatus.DONE:
            task = self.storage.get_task(task_id)
            if task:
                task.mark_as_done()
                self.storage.save()
                return True
        else:
            return self.storage.update_task(task_id, status=new_status)

    def update_task_priority(self, task_id, new_priority_value):
        new_priority = TaskPriority(new_priority_value)
        return self.storage.update_task(task_id, priority=new_priority)

    def update_task_due_date(self, task_id, due_date_str):
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            return self.storage.update_task(task_id, due_date=due_date)
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
            return False

    def delete_task(self, task_id):
        return self.storage.delete_task(task_id)

    def get_task_details(self, task_id):
        return self.storage.get_task(task_id)

    def add_tag_to_task(self, task_id, tag):
        task = self.storage.get_task(task_id)
        if task:
            if tag not in task.tags:
                task.tags.append(tag)
                self.storage.save()
            return True
        return False

    def remove_tag_from_task(self, task_id, tag):
        task = self.storage.get_task(task_id)
        if task and tag in task.tags:
            task.tags.remove(tag)
            self.storage.save()
            return True
        return False

    def get_statistics(self):
        tasks = self.storage.get_all_tasks()
        total = len(tasks)

        # Count by status
        status_counts = {status.value: 0 for status in TaskStatus}
        for task in tasks:
            status_counts[task.status.value] += 1

        # Count by priority
        priority_counts = {priority.name: 0 for priority in TaskPriority}
        for task in tasks:
            priority_counts[task.priority.name] += 1

        # Count overdue
        overdue_count = len([task for task in tasks if task.is_overdue()])

        # Count completed in last 7 days
        seven_days_ago = datetime.now() - timedelta(days=7)
        completed_recently = len([
            task for task in tasks
            if task.completed_at and task.completed_at >= seven_days_ago
        ])

        return {
            "total": total,
            "by_status": status_counts,
            "by_priority": priority_counts,
            "overdue": overdue_count,
            "completed_last_week": completed_recently
        }

