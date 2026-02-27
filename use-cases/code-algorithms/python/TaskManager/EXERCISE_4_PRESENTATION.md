# Exercise 4: Application Overview Presentation

## High-Level Architecture
- Brief description of layers (CLI → TaskManager → Models → Storage)
- Optional ASCII diagram of data flow

## Key Features
### 1. Task Creation
- How a task is created via CLI or API
- How priority and tags are handled
- Where the task is stored

### 2. Task Prioritization
- Priority flow through models.py, task_priority.py, task_manager.py
- How scores and sorting are calculated

### 3. Task Completion
- Marking tasks as done
- State changes in Task object and persistence in JSON
- CLI output formatting

## Design Pattern or Approach
- Example: Special handling for DONE status using mark_as_done()
- Why enums are used for statuses and priorities

## Challenges & Insights
- What was confusing at first
- How prompts helped you understand the code
- Key takeaways from tracing the data flows