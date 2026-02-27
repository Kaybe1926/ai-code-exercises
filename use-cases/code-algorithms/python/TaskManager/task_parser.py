import re
from datetime import datetime, timedelta

from models import TaskStatus, TaskPriority, Task


def parse_task_from_text(text):
    """
    Parse free-form text to extract task properties.

    Examples of format it can parse:
    "Buy milk @shopping !2 #tomorrow"
    "Finish report for client XYZ !urgent #friday #work @project"

    Where:
    - Basic text is the task title
    - @tag adds a tag
    - !N sets priority (1=low, 2=medium, 3=high, 4=urgent)
    - !urgent/!high/!medium/!low sets priority by name
    - #date sets a due date
    """
    # Default task properties
    title = text.strip()
    priority = TaskPriority.MEDIUM
    due_date = None
    tags = []

    # Extract priority markers (!N or !name)
    priority_matches = re.findall(r'\s!([1-4]|urgent|high|medium|low)\b', text, re.IGNORECASE)
    if priority_matches:
        priority_text = priority_matches[0].lower()
        # Remove from title
        title = re.sub(r'\s!([1-4]|urgent|high|medium|low)\b', '', title, flags=re.IGNORECASE)

        # Convert to TaskPriority
        if priority_text == '1' or priority_text == 'low':
            priority = TaskPriority.LOW
        elif priority_text == '2' or priority_text == 'medium':
            priority = TaskPriority.MEDIUM
        elif priority_text == '3' or priority_text == 'high':
            priority = TaskPriority.HIGH
        elif priority_text == '4' or priority_text == 'urgent':
            priority = TaskPriority.URGENT

    # Extract tags (@tag)
    tag_matches = re.findall(r'\s@(\w+)', text)
    if tag_matches:
        tags = tag_matches
        # Remove from title
        for tag in tag_matches:
            title = re.sub(r'\s@' + tag + r'\b', '', title)

    # Extract date markers (#date)
    date_matches = re.findall(r'\s#(\w+)', text)
    if date_matches:
        # Remove from title
        for date_str in date_matches:
            title = re.sub(r'\s#' + date_str + r'\b', '', title)

        # Try to parse date references
        for date_str in date_matches:
            date_str = date_str.lower()
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            if date_str in ('today', 'now'):
                due_date = today
                break
            elif date_str == 'tomorrow':
                due_date = today + timedelta(days=1)
                break
            elif date_str in ('next_week', 'nextweek'):
                due_date = today + timedelta(days=7)
                break
            elif date_str in ('monday', 'mon'):
                due_date = get_next_weekday(today, 0)  # 0 = Monday
                break
            elif date_str in ('tuesday', 'tue'):
                due_date = get_next_weekday(today, 1)
                break
            elif date_str in ('wednesday', 'wed'):
                due_date = get_next_weekday(today, 2)
                break
            elif date_str in ('thursday', 'thu'):
                due_date = get_next_weekday(today, 3)
                break
            elif date_str in ('friday', 'fri'):
                due_date = get_next_weekday(today, 4)
                break
            # Try to parse as YYYY-MM-DD
            try:
                due_date = datetime.strptime(date_str, '%Y-%m-%d')
                break
            except ValueError:
                pass

    # Trim excess whitespace from title
    title = re.sub(r'\s+', ' ', title).strip()

    # Create a new task with the extracted properties
    task = Task(title)
    task.priority = priority
    task.due_date = due_date
    task.tags = tags

    return task

def get_next_weekday(current_date, weekday):
    """Get the next occurrence of a specific weekday."""
    days_ahead = weekday - current_date.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return current_date + timedelta(days=days_ahead)


def parse_task_text(text):
    """Parse a free-form task text line into a structured Task object."""
    title = text
    priority = TaskPriority.MEDIUM  # default
    due_date = None
    tags = []

    # Detect priority markers like !!, !!!, etc.
    if "!" in text:
        count = text.count("!")
        if count >= 3:
            priority = TaskPriority.URGENT
        elif count == 2:
            priority = TaskPriority.HIGH
        elif count == 1:
            priority = TaskPriority.MEDIUM

    # Detect due date patterns like #YYYY-MM-DD or #tomorrow
    if "#" in text:
        parts = text.split()
        for part in parts:
            if part.startswith("#"):
                date_str = part[1:].lower()
                today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

                if date_str == "today":
                    due_date = today
                    break
                elif date_str == "tomorrow":
                    due_date = today + timedelta(days=1)
                    break
                elif date_str == "next_week":
                    due_date = today + timedelta(days=7)
                    break
                elif date_str in ("monday", "mon"):
                    due_date = get_next_weekday(today, 0)  # 0 = Monday
                    break
                elif date_str in ("tuesday", "tue"):
                    due_date = get_next_weekday(today, 1)
                    break
                elif date_str in ("wednesday", "wed"):
                    due_date = get_next_weekday(today, 2)
                    break
                elif date_str in ("thursday", "thu"):
                    due_date = get_next_weekday(today, 3)
                    break
                elif date_str in ("friday", "fri"):
                    due_date = get_next_weekday(today, 4)
                    break
                elif date_str in ("saturday", "sat"):
                    due_date = get_next_weekday(today, 5)
                    break
                elif date_str in ("sunday", "sun"):
                    due_date = get_next_weekday(today, 6)
                    break
                else:
                    # Try to parse as YYYY-MM-DD
                    try:
                        due_date = datetime.fromisoformat(date_str)
                        break
                    except ValueError:
                        pass

    # Detect tags marked with @
    if "@" in text:
        parts = text.split()
        for part in parts:
            if part.startswith("@"):
                tags.append(part[1:])

    # Clean up title by removing special markers
    title = " ".join(word for word in text.split() if not word.startswith("!") and not word.startswith("#") and not word.startswith("@"))

    return Task(
        title=title.strip(),
        priority=priority,
        due_date=due_date,
        tags=tags
    )
