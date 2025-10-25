# Data Directory - 新的时间戳组织存储结构

这个目录包含了多智能体工作流程的所有中间结果和输出，采用按时间戳组织的新存储结构。

## 📁 新的目录结构

```
data/
├── runs/                         # 按时间戳组织的运行记录
│   ├── 20251025_160339/         # 每次运行的独立文件夹
│   │   ├── interview/           # 访谈阶段数据
│   │   │   ├── intermediate_results/
│   │   │   └── interview_data_*.json
│   │   ├── research/           # 研究阶段数据
│   │   │   ├── intermediate_results/
│   │   │   ├── papers/
│   │   │   ├── pdfs/
│   │   │   └── research_data_*.json
│   │   ├── workflow/           # 工作流程数据
│   │   │   └── workflow_summary_*.json
│   │   └── metadata.json       # 运行元数据
│   ├── 20251025_161500/         # 另一次运行
│   │   └── ...
│   └── latest/                  # 最新运行的副本
├── templates/                   # 模板和配置文件（预留）
└── README.md                   # 本文件
```

## 🎯 新结构特点

### ✅ **时间戳隔离**
- 每次运行都有独立的文件夹（格式：YYYYMMDD_HHMMSS）
- 不同运行的数据完全隔离，避免冲突
- 保留完整的历史运行记录

### ✅ **阶段分离**
- **interview/**: 访谈阶段的所有数据
- **research/**: 研究阶段的所有数据（包括papers和pdfs）
- **workflow/**: 工作流程级别的摘要和元数据

### ✅ **完整追踪**
- **metadata.json**: 每个运行的完整元数据
- 阶段状态追踪（pending → started → completed）
- 文件创建记录和时间戳
- 统计信息（总文件数、各阶段文件数）

### ✅ **快速访问**
- **latest/**: 最新运行的副本，便于快速访问
- 通过run_id可以快速定位特定运行

## 📊 数据流程

### 1. **运行创建**
```python
run_manager = RunManager("data")
run_id = run_manager.create_new_run()  # 创建新的时间戳文件夹
```

### 2. **阶段管理**
```python
# 更新阶段状态
run_manager.update_phase_status("interview", "started")
run_manager.update_phase_status("interview", "completed")
```

### 3. **数据保存**
```python
data_saver = DataSaver(run_manager)
# 自动保存到当前运行的相应阶段目录
data_saver.save_interview_data(data)
data_saver.save_research_data(data)
data_saver.save_pdf_metadata(data)
```

## 📋 元数据结构

### metadata.json 示例
```json
{
  "run_id": "20251025_160339",
  "created_at": "2025-10-25T16:03:39.978422",
  "status": "initialized",
  "phases": {
    "interview": {
      "status": "completed",
      "started_at": "2025-10-25T16:03:40.000000",
      "completed_at": "2025-10-25T16:05:00.000000",
      "files_created": [
        {
          "filename": "interview_data_20251025_160340.json",
          "created_at": "2025-10-25T16:03:40.044775"
        }
      ]
    },
    "research": {
      "status": "active",
      "started_at": "2025-10-25T16:05:00.000000",
      "completed_at": null,
      "files_created": [...]
    },
    "workflow": {
      "status": "pending",
      "started_at": null,
      "completed_at": null,
      "files_created": []
    }
  },
  "config": {
    "interview_agent": "interview_agent_group",
    "research_agent": "research_agent_group",
    "workflow_mode": "complete"
  },
  "statistics": {
    "total_files": 5,
    "interview_files": 2,
    "research_files": 2,
    "workflow_files": 1
  }
}
```

## 🔧 管理功能

### 运行管理
- **创建新运行**: `run_manager.create_new_run()`
- **获取运行信息**: `run_manager.get_run_info()`
- **列出所有运行**: `run_manager.list_all_runs()`
- **清理旧运行**: `run_manager.cleanup_old_runs(keep_last=10)`

### 数据保存
- **访谈数据**: `data_saver.save_interview_data(data)`
- **研究数据**: `data_saver.save_research_data(data)`
- **PDF元数据**: `data_saver.save_pdf_metadata(data)`
- **工作流程摘要**: `data_saver.save_workflow_summary(data)`

## 💡 使用建议

### 1. **运行管理**
- 每次启动工作流程都会创建新的运行记录
- 可以通过run_id追踪特定运行的所有数据
- 使用latest目录快速访问最新结果

### 2. **数据组织**
- 每个阶段的数据都保存在对应的子目录中
- 文件名包含时间戳，避免冲突
- 元数据文件记录完整的运行信息

### 3. **历史管理**
- 定期清理旧的运行记录以节省空间
- 重要运行可以手动备份
- 通过元数据快速了解运行状态

### 4. **调试和监控**
- 通过metadata.json了解运行状态
- 检查各阶段的文件创建情况
- 使用统计信息监控数据量

## 🚀 优势

1. **版本控制**: 每次运行都有完整的历史记录
2. **数据隔离**: 不同运行的数据不会相互干扰
3. **状态追踪**: 完整的阶段状态和文件追踪
4. **快速访问**: 通过latest链接快速访问最新结果
5. **易于管理**: 可以轻松清理、备份或归档运行记录
6. **扩展性**: 可以轻松添加新的阶段或数据类型

这种新的存储结构为多智能体工作流程提供了完整的数据管理和追踪能力！