# Exercise 3: Data Flow Analysis - Mark Task as Complete

## 1. Complete Data Flow Diagram

```
USER INPUT
    │
    ├─ Command: python cli.py status <task_id> done
    │
    ▼
[CLI PARSING LAYER] ─── cli.py:main()
    │
    ├─ argparse parses "status" subcommand
    ├─ Extracts: task_id="<uuid>" and status="done"
    ├─ Creates TaskManager instance
    │
    ▼
[BUSINESS LOGIC LAYER] ─── task_manager.py:update_task_status()
    │
    ├─ Receives: task_id (string), new_status_value ("done")
    ├─ Converts: "done" → TaskStatus.DONE enum (validation occurs here)
    ├─ Special Logic: If status == DONE, call task.mark_as_done()
    │
    ▼
[DOMAIN MODEL LAYER] ─── models.py:Task.mark_as_done()
    │
    ├─ Sets: task.status = TaskStatus.DONE
    ├─ Sets: task.completed_at = datetime.now()
    ├─ Sets: task.updated_at = datetime.now()
    │
    ▼
[PERSISTENCE LAYER] ─── storage.py:TaskStorage.save()
    │
    ├─ Serializes: Task objects → TaskEncoder
    │   ├─ Task.priority (enum) → priority.value (int)
    │   ├─ Task.status (enum) → status.value (string: "done")
    │   └─ Task.completed_at (datetime) → ISO format string
    │
    ├─ Writes: JSON to tasks.json
    │
    ▼
[FILE SYSTEM]
    │
    └─ tasks.json updated with completed_at timestamp
        and status = "done"
    
    ▼
[RESPONSE BACK TO USER]
    │
    └─ cli.py prints: "Updated task status to done"
```

## 2. State Changes Throughout the Process

### State 1: CLI Input State
```python
# User command at terminal:
# python cli.py status abc123def456 done

args.task_id    = "abc123def456"
args.status     = "done"  # Still a STRING at this point
```

### State 2: TaskManager Validation State
```python
# In task_manager.py:update_task_status()
task_id = "abc123def456"
new_status_value = "done"  # STRING input

# Conversion happens here:
new_status = TaskStatus("done")  # TaskStatus.DONE
# TaskStatus("done") is valid because TaskStatus enum values are strings:
# TaskStatus.DONE.value == "done"
```

### State 3: Storage Retrieval State
```python
# Retrieved from self.storage.tasks dictionary
task = Task(
    id="abc123def456",
    title="...",
    status=TaskStatus.TODO,  # Original state (enum)
    completed_at=None,  # Important: not yet set
    updated_at=datetime(2026, 2, 24, 10, 30, 45)
)
```

### State 4: Domain Model Modification State
```python
# After task.mark_as_done() is called:
task = Task(
    id="abc123def456",
    title="...",
    status=TaskStatus.DONE,  # CHANGED from TODO
    completed_at=datetime(2026, 2, 25, 14, 45, 30),  # NOW SET
    updated_at=datetime(2026, 2, 25, 14, 45, 30)  # UPDATED
)
# In-memory object is now modified
```

### State 5: JSON Serialization State
```python
# TaskEncoder converts before writing:
task_dict = {
    "id": "abc123def456",
    "title": "...",
    "status": "done",  # Enum.value (string)
    "priority": 2,  # Enum.value (int)
    "completed_at": "2026-02-25T14:45:30",  # ISO format
    "updated_at": "2026-02-25T14:45:30",
    # ... other fields
}

# JSON representation:
{
  "id": "abc123def456",
  "status": "done",
  "completed_at": "2026-02-25T14:45:30",
  ...
}
```

### State 6: Persistent Storage State
```json
// tasks.json file on disk now contains:
[
  {
    "id": "abc123def456",
    "status": "done",
    "completed_at": "2026-02-25T14:45:30",
    ...
  }
]
```

## 3. Data Transformations at Each Step

### Step 1: CLI → TaskManager
```
INPUT:  args.status (string: "done")
PROCESS: argparse validation (choices=["todo", "in_progress", "review", "done"])
OUTPUT: Validated string passed to update_task_status()
```

### Step 2: TaskManager Conversion
```
INPUT:  new_status_value (string: "done")
PROCESS: TaskStatus("done")  # Enum constructor validates
         Checks if status == TaskStatus.DONE
OUTPUT: TaskStatus enum object (safer for type checking)
```

### Step 3: Task Retrieval
```
INPUT:  task_id (string)
PROCESS: self.storage.get_task(task_id)
         Looks up in self.storage.tasks dictionary
OUTPUT: Task object reference (or None if not found)
```

### Step 4: Domain Logic
```
INPUT:  Task object with status=TaskStatus.TODO
PROCESS: task.mark_as_done()
         - Sets task.status = TaskStatus.DONE
         - Sets task.completed_at = datetime.now()
         - Sets task.updated_at = datetime.now()
OUTPUT: Task object with updated internal state
```

### Step 5: Serialization
```
INPUT:  Task object (Python object with enums and datetime objects)
PROCESS: TaskEncoder.default()
         - task.status (enum) → task.status.value ("done" string)
         - task.priority (enum) → task.priority.value (int)
         - datetime objects → ISO format strings
OUTPUT: Dictionary with native JSON-compatible types
```

### Step 6: File Write
```
INPUT:  Dictionary/list of task dictionaries
PROCESS: json.dump() with TaskEncoder
         - Validates JSON-serializable format
         - Writes to file with 2-space indentation
OUTPUT: tasks.json file updated
```

## 4. Failure Points & Error Handling

### Failure Point 1: Invalid Task ID
**Where it occurs:** `task_manager.update_task_status()`
```python
def update_task_status(self, task_id, new_status_value):
    new_status = TaskStatus(new_status_value)
    if new_status == TaskStatus.DONE:
        task = self.storage.get_task(task_id)  # ← Returns None if not found
        if task:
            task.mark_as_done()
            self.storage.save()
            return True
    # ...
    # Falls through to: return self.storage.update_task(...)
```

**Impact:** Function returns False, CLI prints "Failed to update task status. Task not found."

**How to debug:**
- Add print statements: `print(f"Looking for task: {task_id}")`
- Check storage.tasks dictionary: `print(self.storage.tasks.keys())`
- Verify task_id is not truncated or malformed

### Failure Point 2: Invalid Status Value
**Where it occurs:** `task_manager.update_task_status()`
```python
new_status = TaskStatus(new_status_value)  # ← Raises ValueError if invalid
```

**Impact:** Program crashes with ValueError
- User tries: `python cli.py status abc123 invalid_status`
- TaskStatus("invalid_status") raises: `ValueError: 'invalid_status' is not a valid TaskStatus`

**How to debug:**
- argparse already prevents this (choices constraint)
- But if called programmatically with invalid values, catch the exception:
  ```python
  try:
      new_status = TaskStatus(new_status_value)
  except ValueError:
      print(f"Invalid status: {new_status_value}")
      return False
  ```

### Failure Point 3: File System Errors
**Where it occurs:** `storage.save()`
```python
def save(self):
    try:
        with open(self.storage_path, 'w') as f:
            json.dump(list(self.tasks.values()), f, cls=TaskEncoder, indent=2)
    except Exception as e:
        print(f"Error saving tasks: {e}")  # ← Catches but doesn't retry
```

**Potential issues:**
- Permission denied (read-only filesystem)
- Disk full
- Path doesn't exist
- File locked by another process

**Impact:** Changes are lost, but user isn't notified of failure

**How to debug:**
- Check file permissions: `ls -la tasks.json`
- Verify disk space: `df -h`
- Monitor file locks: `lsof tasks.json`

### Failure Point 4: JSON Serialization Errors
**Where it occurs:** `TaskEncoder.default()`

**Potential issues:**
- Custom objects that can't serialize
- Circular references
- Non-serializable datetime objects (unlikely here, but possible)

**Impact:** `TypeError: Object of type X is not JSON serializable`

### Failure Point 5: Task Retrieval Data Corruption
**Where it occurs:** `storage.load()` or `TaskDecoder`

**Potential issues:**
- Malformed JSON in tasks.json
- Missing required fields
- Invalid enum values in JSON

**Impact:** Tasks fail to load, data is lost

**How to debug:**
```python
def load(self):
    if os.path.exists(self.storage_path):
        try:
            with open(self.storage_path, 'r') as f:
                tasks_data = json.load(f, cls=TaskDecoder)
                # Add validation:
                if not isinstance(tasks_data, list):
                    raise ValueError("Expected list of tasks")
```

## 5. Why Use Enums Instead of Plain Strings?

### The Problem with Strings
```python
# Without enums, you might write:
def update_task_status(self, task_id, status):
    task.status = status  # Could be "done", "DONE", "Done", "complete", etc.
    # No validation! Typos cause silent bugs.
```

### The Solution: Enums
```python
class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

# Now you write:
task.status = TaskStatus.DONE  # Type-safe, IDE autocomplete works
```

### Benefits of Enums

#### 1. **Type Safety**
```python
# Enum - catches errors
task.status = TaskStatus.DONE  # ✓ Correct
task.status = TaskStatus.MADE_UP  # ✗ AttributeError (caught immediately)

# String - silently wrong
task.status = "done"  # Could be correct
task.status = "Done"  # Silently wrong (typo in capitalization)
```

#### 2. **Validation at Constructor**
```python
# Enum constructor validates
TaskStatus("done")  # ✓ Returns TaskStatus.DONE
TaskStatus("invalid")  # ✗ Raises ValueError: 'invalid' is not a valid TaskStatus

# Strings have no validation
status = "invalid"  # ✓ No error caught here
```

#### 3. **IDE Support & Autocomplete**
```python
# With enums:
new_status = TaskStatus.  # IDE shows: DONE, IN_PROGRESS, REVIEW, TODO

# With strings:
new_status = "d"  # IDE can't help you
```

#### 4. **Prevents Invalid Transitions**
```python
# You can add logic to prevent invalid status transitions:
def update_task_status(self, task_id, new_status):
    task = self.storage.get_task(task_id)
    
    # Prevent reverting completed tasks
    if task.status == TaskStatus.DONE and new_status != TaskStatus.DONE:
        print("Cannot change status of completed task")
        return False
    
    task.status = new_status  # Type-safe assignment
```

#### 5. **Easy to Iterate Over All Valid Values**
```python
# Strings - need to maintain a list manually:
VALID_STATUSES = ["todo", "in_progress", "review", "done"]

# Enums - iteration is built-in:
for status in TaskStatus:
    print(f"{status.name}: {status.value}")
    # Output: TODO: todo, IN_PROGRESS: in_progress, REVIEW: review, DONE: done
```

### Dual Representation Strategy (Why Both Name and Value?)

```python
class TaskStatus(Enum):
    DONE = "done"  # "DONE" is the name, "done" is the value
```

- **Name** (`DONE`): Used in Python code for type safety
- **Value** (`"done"`): Used in JSON storage and CLI arguments for human readability

```python
# At different layers:
task.status = TaskStatus.DONE  # Name - in Python code
json_data = {"status": "done"}  # Value - in JSON file
cli_argument = "done"  # Value - from user input
```

## 6. Debugging Guide for Data Flow Issues

### Debug Checklist

```python
# 1. Verify CLI parsing
print(f"Task ID received: '{args.task_id}'")
print(f"Status received: '{args.status}'")

# 2. Check enum conversion
try:
    new_status = TaskStatus(args.status)
    print(f"Converted to enum: {new_status}, value: {new_status.value}")
except ValueError as e:
    print(f"Enum conversion failed: {e}")

# 3. Verify task exists
task = self.storage.get_task(task_id)
print(f"Task found: {task is not None}")
if task:
    print(f"Original status: {task.status}")
    print(f"Original completed_at: {task.completed_at}")

# 4. Check state change
task.mark_as_done()
print(f"After mark_as_done():")
print(f"  New status: {task.status}")
print(f"  completed_at: {task.completed_at}")
print(f"  updated_at: {task.updated_at}")

# 5. Verify persistence
before_save = len(self.storage.tasks)
self.storage.save()
print(f"Save completed, tasks count: {before_save}")

# 6. Verify file was written
import os
if os.path.exists("tasks.json"):
    print(f"File size: {os.path.getsize('tasks.json')} bytes")
    with open("tasks.json", "r") as f:
        import json
        data = json.load(f)
        print(f"Task count in file: {len(data)}")
```

### Common Issues and Fixes

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| "Task not found" returned | task_id doesn't exist in storage | Verify task_id is exactly correct (UUIDs are case-sensitive) |
| KeyError on task_id | Task was never added to storage.tasks | Check if create_task was called before update_task_status |
| ValueError: invalid TaskStatus | argparse not enforcing choices | Update choices list in update_status_parser |
| completed_at is None | Task status changed but mark_as_done() not called | Check if condition `new_status == TaskStatus.DONE` is true |
| File not updating | save() called but file not written | Check file permissions, disk space, exceptions in try/except |
| JSON decode error | Corrupted tasks.json | Back up file, delete tasks.json, start fresh |

## 7. Design Pattern: Special Case for DONE Status

Notice this asymmetry in the code:

```python
def update_task_status(self, task_id, new_status_value):
    new_status = TaskStatus(new_status_value)
    
    if new_status == TaskStatus.DONE:
        # Special handling: use task.mark_as_done()
        task = self.storage.get_task(task_id)
        if task:
            task.mark_as_done()  # ← Sets completed_at and updated_at
            self.storage.save()
            return True
    else:
        # Generic handling: use storage.update_task()
        return self.storage.update_task(task_id, status=new_status)
```

### Why This Design?

1. **Completion Tracking**: The `DONE` status is special because it needs to record `completed_at`
2. **Audit Trail**: We need to know exactly when a task was completed
3. **Statistics**: `get_statistics()` uses `completed_at` to calculate "completed_last_week"

### Alternative Pattern (More Flexible)

A cleaner design might be:

```python
def update_task_status(self, task_id, new_status_value):
    new_status = TaskStatus(new_status_value)
    task = self.storage.get_task(task_id)
    
    if task:
        if new_status == TaskStatus.DONE:
            task.mark_as_done()
        else:
            task.update(status=new_status)
        self.storage.save()
        return True
    return False
```

This removes the duplication and special cases.

## 8. Modifying the Data Flow: What to Consider

### If Adding a New Status (e.g., ARCHIVED)

1. **Update models.py:**
   ```python
   class TaskStatus(Enum):
       TODO = "todo"
       IN_PROGRESS = "in_progress"
       REVIEW = "review"
       DONE = "done"
       ARCHIVED = "archived"  # New status
   ```

2. **Update cli.py:**
   ```python
   update_status_parser.add_argument(
       "status", 
       help="New status", 
       choices=["todo", "in_progress", "review", "done", "archived"]  # Add here
   )
   ```

3. **Consider task_manager.py:**
   - Does ARCHIVED need special handling like DONE?
   - Add logic: `elif new_status == TaskStatus.ARCHIVED: task.archived_at = datetime.now()`

4. **Update task_priority.py:**
   - Should ARCHIVED tasks be scored lower? Check `calculate_task_score()`

5. **Update tests:**
   - Add test for new status transitions
   - Test serialization/deserialization
   - Test filtering and statistics

### If Adding a New Field to Track (e.g., archived_at)

1. **models.py** - Add field:
   ```python
   self.archived_at = None
   ```

2. **storage.py** - Update serialization:
   ```python
   # In TaskEncoder:
   for key in ['created_at', 'updated_at', 'due_date', 'completed_at', 'archived_at']:
       if task_dict.get(key) is not None:
           task_dict[key] = task_dict[key].isoformat()
   
   # In TaskDecoder:
   for key in ['created_at', 'updated_at', 'completed_at', 'archived_at']:
       if obj.get(key):
           setattr(task, key, datetime.fromisoformat(obj[key]))
   ```

3. **cli.py** - Update display:
   ```python
   archived_str = f"Archived: {task.archived_at.strftime('%Y-%m-%d')}" if task.archived_at else "Not archived"
   ```

4. **Test all layers** to ensure data flows correctly

## 9. Key Takeaways

### Mental Models to Remember

1. **Layer-based Architecture**: Each layer transforms data:
   - CLI: String → TaskManager
   - TaskManager: String → Enum → Task
   - Task: Python object state change
   - Storage: Task → JSON → File

2. **State is Centralized**: The `Task` object in memory is the source of truth until saved

3. **Enums = Validated Values**: They prevent the entire class of "typo" bugs

4. **Special Cases Matter**: The `DONE` status is special because it triggers `completed_at` tracking

5. **Serialization is Key**: The TaskEncoder/Decoder pair bridges Python objects and JSON

### Questions to Ask When Modifying This Code

- [ ] Does this change affect all layers (CLI, TaskManager, Task, Storage)?
- [ ] Are there enum values or strings that need to be synchronized?
- [ ] Do datetime objects need proper serialization?
- [ ] Should this field be indexed for performance?
- [ ] Are there new statistics to calculate?
- [ ] Have I updated all relevant enums?
- [ ] Do tests cover the new flow?

