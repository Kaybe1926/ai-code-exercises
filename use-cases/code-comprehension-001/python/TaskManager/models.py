# task_manager/models.py
from datetime import datetime
from enum import Enum
import uuid

class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

class Task:
    def __init__(self, title, description="", priority=TaskPriority.MEDIUM,
                 due_date=None, tags=None):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.priority = priority
        self.status = TaskStatus.TODO
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.due_date = due_date
        self.completed_at = None
        self.tags = tags or []

    def update(self, **kwargs):
        """Update attributes of the task instance and refresh the timestamp.

        This method accepts any number of keyword arguments and will assign
        their values to matching attributes on the task object. Only
        attributes that already exist on the instance are modified; unknown
        keys are ignored. After applying the updates, ``updated_at`` is set
        to the current time to reflect the change.

        Args:
            **kwargs: Arbitrary keyword arguments where the key is the name of
                an attribute on :class:`Task` and the value is the new value
                to set. Common keys include ``title``, ``description``,
                ``priority``, ``status``, ``due_date``, ``tags``, etc.

        Returns:
            None: This method modifies the object in place and does not
            return a value.

        Raises:
            AttributeError: This method does **not** raise an exception if an
                unknown attribute is provided; those keys are silently
                ignored. However, attempting to set a read-only property or
                otherwise restricted attribute outside of ``hasattr`` checks
                could still raise errors.

        Example:
            >>> task = Task("Write report")
            >>> task.update(title="Write final report", priority=TaskPriority.HIGH)
            >>> task.title
            'Write final report'
            >>> task.priority == TaskPriority.HIGH
            True

        Notes:
            - ``updated_at`` will always be refreshed even if no valid
              attributes were provided.
            - Values are assigned directly; validation should be performed by
              callers if needed (e.g. ensuring priority is a
              ``TaskPriority`` member).
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now()

    def mark_as_done(self):
        """Mark the task as completed and update timestamps.

        When invoked, this method transitions the task's status to
        :attr:`TaskStatus.DONE`, records the current time as the
        ``completed_at`` timestamp, and synchronizes ``updated_at`` with
        that value. This allows other components (e.g. statistics or
        overdue checks) to recognize the task as finished.

        Args:
            None: This method does not take any parameters beyond ``self``.

        Returns:
            None: The task object is modified in place; no value is returned.

        Raises:
            This method does not intentionally raise any exceptions. If the
            ``TaskStatus`` enum or ``datetime.now`` fails unexpectedly, the
            exception will propagate.

        Example:
            >>> task = Task("Send invoice")
            >>> task.status
            <TaskStatus.TODO: 'todo'>
            >>> task.mark_as_done()
            >>> task.status
            <TaskStatus.DONE: 'done'>
            >>> isinstance(task.completed_at, datetime)
            True

        Notes:
            - Calling this method repeatedly will overwrite ``completed_at``
              and ``updated_at`` with the latest invocation time.
            - No validation is performed; it is the caller's responsibility
              to ensure the operation makes sense in context (e.g., a task
              should not be marked done twice in a workflow)."""
        self.status = TaskStatus.DONE
        self.completed_at = datetime.now()
        self.updated_at = self.completed_at

    def is_overdue(self):
        """Determine whether the task has passed its due date and is not done.

        Checks the task's ``due_date`` against the current time. A task with
        no ``due_date`` is never considered overdue. Completed tasks are also
        excluded from being overdue, even if the due date has passed.

        Args:
            None: This method relies solely on the instance's attributes.

        Returns:
            bool: ``True`` if the task has a due date, the current datetime is
            later than that due date, and the task's status is not
            :attr:`TaskStatus.DONE`. ``False`` otherwise.

        Raises:
            This method should not raise under normal circumstances. If
            ``datetime.now()`` fails, its exception will propagate. The
            comparison assumes ``due_date`` is a ``datetime`` instance or
            ``None``; passing another type may trigger a ``TypeError``.

        Example:
            >>> task = Task("Finish assignment", due_date=datetime(2021,1,1))
            >>> task.status = TaskStatus.TODO
            >>> # assuming current date > 2021-01-01
            >>> task.is_overdue()
            True
            >>> task.mark_as_done()
            >>> task.is_overdue()
            False

        Notes:
            - This method performs a simple, local time check; timezone-aware
              comparisons should be handled by callers if needed.
            - ``due_date`` should be a naive or aware ``datetime`` object
              consistent with ``datetime.now()`` for accurate results.
        """
        if not self.due_date:
            return False
        return self.due_date < datetime.now() and self.status != TaskStatus.DONE

