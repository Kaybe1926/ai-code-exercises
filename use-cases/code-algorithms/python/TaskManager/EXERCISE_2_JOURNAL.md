
# Exercise 2 – Task Prioritization Deep Dive

## Initial Understanding

At first, I understood that task priority is just a value assigned to a task to indicate how important it is.

From what I saw in the code, there seems to be a `TaskPriority` enum that defines different priority levels. I think these levels are represented as numeric values (like 1–4), and they probably map to labels like `LOW`, `MEDIUM`, `HIGH`, and `URGENT`.

It looks like when a task is created or updated through the CLI, a priority value can be passed in. The `TaskManager` then stores this value in the `Task` object.

I also suspect that priority might affect how tasks are sorted or filtered, but I'm not fully sure yet how that works internally.

# Task Prioritization Feature Investigation

## Challenge: High-Priority Task Creation Flow
When a user creates a task like "Finish report !high #tomorrow @work":
1. `task_parser.py` reads the text and finds the `!high` marker → converts it to `TaskPriority.HIGH`.
2. `task_manager.py` creates a new Task object and sets the priority attribute.
3. `storage.py` saves the Task (including priority) in `tasks.json`.
4. `task_priority.py` calculates the task’s score based on priority, due date, status, and tags.
5. `cli.py` displays the task when listing or showing it, using symbols or labels to indicate its priority.

## File-by-File Analysis
### models.py
Defines the `Task` class and the `TaskPriority` enum.  
`TaskPriority` has levels LOW, MEDIUM, HIGH, URGENT, which map to numbers. The Task object has a `priority` field that stores this value.

### task_parser.py  
Parses CLI input or text markers. Converts `!high` into `TaskPriority.HIGH` so the rest of the program can use it consistently.

### task_manager.py
Contains the main business logic.  
- `create_task()` assigns the priority to a new Task object.  
- `update_task_priority()` updates the priority later if needed.  
- Calls storage to save the task after changes.

### task_priority.py
Calculates a task score to sort tasks by importance.  
Takes into account priority, due date, status, tags, and recency.  
Used for sorting tasks in CLI commands and showing stats.

### cli.py
User-facing commands:  
- `create --priority` → set priority on creation  
- `priority <task_id> <level>` → update priority  
- `list --priority` → filter tasks by priority  
Displays tasks including priority markers.

### storage.py
Saves tasks to `tasks.json`.  
Handles reading/writing the priority field. Ensures that the priority persists between sessions.

### tests/
Contains unit tests for task priorities.  
Covers scoring, filtering, updating, and CLI behavior to make sure priorities work correctly.

## Key Insights
- Priority spans multiple layers: input, model, manager, storage, scoring, display.  
- CLI commands may have different names than what the README shows, so it’s important to check canonical names.  
- Text parsing allows multiple ways to set priority (`!high`, `--priority 3`).  
- Creating a task triggers several files in sequence: parser → manager → storage → scoring → CLI display.  

## Misconceptions Clarified

- At first, I thought priority was just a number attached to a task, but I learned it flows through multiple layers: parser → manager → storage → scoring → CLI display.  
- I assumed the CLI used the same command names as the README, but they actually differ (`priority` vs `update-priority`).  
- I didn’t realize that priority affects scoring, sorting, and statistics, not just display.  
- I thought parsing only handled `!high/!low` markers, but it also handles numeric levels and integrates with CLI arguments.

## Verification Notes

- Created a task "Finish report !high #tomorrow @work" via the CLI.
- CLI showed the task with HIGH priority (!!) correctly.
- Verified in `tasks.json` that the task’s priority and details were saved as expected.
- This confirms the flow works: CLI input → task_parser.py → task_manager.py → storage.py → CLI display.