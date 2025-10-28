# Data Storage Structure

This document describes how the EmpathyScale project organizes and stores runtime data.

## Overview

The system uses timestamp-isolated storage where each workflow execution gets a unique directory. This ensures:
- **No data conflicts** between different runs
- **Easy tracking** of results over time
- **Simple cleanup** of old runs
- **Reproducible results** with complete run history

## Directory Structure

```
data/
├── latest_run.txt                    # Contains the latest run_id
└── runs/                             # All run directories
    └── YYYY-MM-DD_HHMMSS/           # Timestamped run directory
        ├── metadata.json             # Run metadata (start/end time, status)
        ├── interview_agent_group/    # Interview phase data
        │   ├── summary.json          # Structured interview summary
        │   └── conversation.json     # Full conversation history
        └── literature_search_agent_group/  # Literature search phase data
            ├── summary.json          # Search results summary
            ├── conversation.json     # (if applicable)
            ├── queries.json          # Generated search queries
            ├── findings.json         # Extracted findings
            └── pdfs/                 # Downloaded PDFs
                ├── definitions/      # Papers on empathy definitions
                │   └── paper_XX_YYYY.pdf
                ├── behaviors/        # Papers on empathic behaviors
                │   └── paper_XX_YYYY.pdf
                └── measurement/      # Papers on measurement methods
                    └── paper_XX_YYYY.pdf
```

## Run Directory Naming

Run directories use the format: `YYYY-MM-DD_HHMMSS`

Example: `2025-10-28_194143` (October 28, 2025, 7:41:43 PM)

## File Descriptions

### `metadata.json`

Contains high-level information about the run:

```json
{
  "run_id": "2025-10-28_194143",
  "start_time": "2025-10-28T19:41:43.123456",
  "end_time": "2025-10-28T19:45:30.654321",
  "status": "completed",
  "agent_groups": ["interview_agent_group", "literature_search_agent_group"]
}
```

**Fields:**
- `run_id`: Unique identifier matching directory name
- `start_time`: ISO format timestamp when run started
- `end_time`: ISO format timestamp when run completed (null if still running)
- `status`: `"running"` or `"completed"`
- `agent_groups`: List of agent groups that executed in this run

### `interview_agent_group/summary.json`

Structured summary of the interview session:

```json
{
  "assessment_context": "Healthcare robot assisting nurses with patient care",
  "robot_platform": "Humanoid robot with dual arms and vision sensors",
  "environmental_setting": "Hospital ward with patient rooms and nursing stations",
  "collaboration_pattern": "Supervised collaboration with robot following nurse instructions",
  "interaction_modalities": "Speech communication, visual indicator lights, physical gestures",
  "assessment_goals": [
    "Measure emotional trust in robot",
    "Assess perceived empathy during patient care interactions"
  ],
  "expected_empathy_forms": [
    "Adaptive responses to patient needs",
    "Calming voice tone during stressful situations"
  ],
  "assessment_challenges": [
    "Measuring subjective emotional responses",
    "Ensuring consistent evaluation across different nurses"
  ],
  "measurement_requirements": [
    "Scale capturing both emotional and functional aspects",
    "Validated measurement methods"
  ]
}
```

### `interview_agent_group/conversation.json`

Complete conversation history as an array of message objects:

```json
[
  {
    "timestamp": "2025-10-28T19:41:45.123456",
    "type": "agent",
    "content": "Hello! I'm here to learn about your robot collaboration scenario..."
  },
  {
    "timestamp": "2025-10-28T19:42:15.654321",
    "type": "user",
    "content": "We want to evaluate a healthcare robot that helps nurses..."
  }
]
```

**Message Types:**
- `"agent"`: Message from the interview agent
- `"user"`: User input/response
- `"system"`: System messages or tool invocations (if logged)

### `literature_search_agent_group/summary.json`

Summary of literature search results:

```json
{
  "queries": [
    "robot empathy in healthcare collaboration",
    "measuring perceived empathy in human-robot interaction",
    "empathy scale construction for robots"
  ],
  "total_papers_searched": 120,
  "papers_screened": 80,
  "papers_downloaded": 15,
  "findings_extracted": 15,
  "categories": {
    "definitions": 5,
    "behaviors": 6,
    "measurement": 4
  }
}
```

### `literature_search_agent_group/queries.json`

Generated search queries with metadata:

```json
[
  {
    "query": "robot empathy scale construction methods",
    "source": "generated",
    "timestamp": "2025-10-28T19:43:00.123456"
  }
]
```

### `literature_search_agent_group/findings.json`

Extracted findings from papers, organized by category:

```json
{
  "definitions": [
    {
      "paper_title": "Empathy in Human-Robot Interaction",
      "finding": "Robot empathy is defined as...",
      "category": "definitions"
    }
  ],
  "behaviors": [...],
  "measurement": [...]
}
```

### `literature_search_agent_group/pdfs/`

Downloaded PDF files organized by category:
- `definitions/`: Papers on empathy definitions and frameworks
- `behaviors/`: Papers on empathic robot behaviors
- `measurement/`: Papers on measurement methods and scale construction

**File Naming:** `paper_{index}_{year}.pdf`

Example: `paper_01_2024.pdf`, `paper_02_2023.pdf`

## Accessing Data

### Using DataManager

```python
from utils.data_manager import DataManager

# Initialize
data_manager = DataManager()

# Get latest run
latest_run_id = data_manager.get_latest_run_id()

# Load interview data
interview_data = data_manager.load_agent_group_data(
    latest_run_id, 
    "interview_agent_group"
)
summary = interview_data['summary']
conversation = interview_data['conversation']

# Get run path
run_path = data_manager.get_run_path(latest_run_id)
```

### Direct File Access

```python
from pathlib import Path
import json

# Construct path
run_id = "2025-10-28_194143"
summary_path = Path(f"data/runs/{run_id}/interview_agent_group/summary.json")

# Load JSON
with open(summary_path, 'r', encoding='utf-8') as f:
    summary = json.load(f)
```

## Run Lifecycle

### 1. Run Creation
- `DataManager.new_run()` creates a new timestamped directory
- `metadata.json` is created with `status: "running"`
- `latest_run.txt` is updated with the new run_id

### 2. Data Collection
- Each agent group saves its data to `{run_id}/{agent_group_name}/`
- Files are created incrementally as agents execute
- Each agent group manages its own subdirectory structure

### 3. Run Completion
- `DataManager.complete_run()` updates `metadata.json`
- Sets `status: "completed"` and `end_time`
- Records which agent groups participated

## Cleanup and Maintenance

### List All Runs
```python
from pathlib import Path

runs_dir = Path("data/runs")
run_dirs = [d.name for d in runs_dir.iterdir() if d.is_dir()]
print(f"Total runs: {len(run_dirs)}")
```

### Clean Old Runs
```python
# Delete runs older than 30 days
from datetime import datetime, timedelta
from pathlib import Path

cutoff = datetime.now() - timedelta(days=30)
runs_dir = Path("data/runs")

for run_dir in runs_dir.iterdir():
    if run_dir.is_dir():
        # Parse timestamp from directory name
        run_date = datetime.strptime(run_dir.name.split('_')[0], "%Y-%m-%d")
        if run_date < cutoff.date():
            import shutil
            shutil.rmtree(run_dir)
```

### Keep Only Latest Run
```python
from utils.data_manager import DataManager
from pathlib import Path
import shutil

data_manager = DataManager()
latest_run = data_manager.get_latest_run_id()
runs_dir = Path("data/runs")

for run_dir in runs_dir.iterdir():
    if run_dir.is_dir() and run_dir.name != latest_run:
        shutil.rmtree(run_dir)
```

## Best Practices

1. **Never modify run directories during execution**: Wait for completion before accessing data
2. **Use DataManager methods**: Don't manually create/modify run directories
3. **Check run status**: Verify `status: "completed"` before processing results
4. **Handle missing data gracefully**: Some fields may be `null` if not collected
5. **Preserve run history**: Archive important runs before cleanup

## Encoding and Format

- All JSON files use UTF-8 encoding with `ensure_ascii=False` to support Unicode
- Timestamps use ISO 8601 format: `YYYY-MM-DDTHH:MM:SS.microseconds`
- File paths use forward slashes (Windows converts automatically)

## Troubleshooting

### Run Directory Not Found
- Check that `data/runs/` directory exists
- Verify run_id format matches `YYYY-MM-DD_HHMMSS`
- Ensure DataManager was initialized with correct base_dir

### Missing Files
- Some agent groups may not create all files if execution was interrupted
- Check `metadata.json` status to see if run completed
- Verify agent group actually executed (check `agent_groups` in metadata)

### Encoding Errors
- Ensure all JSON files are opened with `encoding='utf-8'`
- Use `errors='replace'` or `errors='ignore'` for robust reading

