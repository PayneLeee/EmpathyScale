# 新的数据存储结构设计

## 📁 目录结构设计

```
data/
├── runs/                         # 按时间戳组织的运行记录
│   ├── 20251025_160000/         # 每次运行的独立文件夹
│   │   ├── interview/           # 访谈阶段数据
│   │   │   ├── intermediate_results/
│   │   │   ├── interview_summary.json
│   │   │   └── assessment_data.json
│   │   ├── research/           # 研究阶段数据
│   │   │   ├── intermediate_results/
│   │   │   ├── papers/
│   │   │   ├── pdfs/
│   │   │   └── research_summary.json
│   │   ├── workflow/           # 工作流程数据
│   │   │   ├── complete_summary.json
│   │   │   └── execution_log.json
│   │   └── metadata.json       # 运行元数据
│   ├── 20251025_161500/         # 另一次运行
│   │   └── ...
│   └── latest -> 20251025_160000/  # 符号链接指向最新运行
├── templates/                   # 模板和配置文件
│   ├── interview_prompts.json
│   ├── research_prompts.json
│   └── workflow_config.json
└── README.md                   # 数据目录说明
```

## 🎯 设计原则

1. **时间戳隔离**: 每次运行都有独立的文件夹
2. **阶段分离**: 访谈、研究、工作流程数据分别存储
3. **版本追踪**: 保留历史运行记录
4. **快速访问**: 通过latest链接快速访问最新结果
5. **元数据管理**: 每个运行都有完整的元数据记录

## 📋 实现方案

### 1. 运行管理器
```python
class RunManager:
    def __init__(self, base_data_dir: str):
        self.base_data_dir = base_data_dir
        self.runs_dir = os.path.join(base_data_dir, "runs")
        self.templates_dir = os.path.join(base_data_dir, "templates")
        self.current_run_id = None
        self.current_run_dir = None
    
    def create_new_run(self) -> str:
        """创建新的运行文件夹"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(self.runs_dir, timestamp)
        
        # 创建目录结构
        os.makedirs(os.path.join(run_dir, "interview", "intermediate_results"), exist_ok=True)
        os.makedirs(os.path.join(run_dir, "research", "intermediate_results"), exist_ok=True)
        os.makedirs(os.path.join(run_dir, "research", "papers"), exist_ok=True)
        os.makedirs(os.path.join(run_dir, "research", "pdfs"), exist_ok=True)
        os.makedirs(os.path.join(run_dir, "workflow"), exist_ok=True)
        
        # 保存运行元数据
        metadata = {
            "run_id": timestamp,
            "created_at": datetime.now().isoformat(),
            "status": "initialized",
            "phases": {
                "interview": {"status": "pending", "started_at": None, "completed_at": None},
                "research": {"status": "pending", "started_at": None, "completed_at": None},
                "workflow": {"status": "pending", "started_at": None, "completed_at": None}
            },
            "config": {
                "interview_agent": "interview_agent_group",
                "research_agent": "research_agent_group",
                "workflow_mode": "complete"
            }
        }
        
        metadata_path = os.path.join(run_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 更新latest链接
        latest_path = os.path.join(self.runs_dir, "latest")
        if os.path.exists(latest_path):
            os.remove(latest_path)
        os.symlink(timestamp, latest_path)
        
        self.current_run_id = timestamp
        self.current_run_dir = run_dir
        
        return timestamp
    
    def get_run_path(self, phase: str = None) -> str:
        """获取当前运行的路径"""
        if not self.current_run_dir:
            raise ValueError("No active run. Call create_new_run() first.")
        
        if phase:
            return os.path.join(self.current_run_dir, phase)
        return self.current_run_dir
    
    def update_phase_status(self, phase: str, status: str):
        """更新阶段状态"""
        metadata_path = os.path.join(self.current_run_dir, "metadata.json")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        metadata["phases"][phase]["status"] = status
        if status == "started":
            metadata["phases"][phase]["started_at"] = datetime.now().isoformat()
        elif status == "completed":
            metadata["phases"][phase]["completed_at"] = datetime.now().isoformat()
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
```

### 2. 数据保存工具
```python
class DataSaver:
    def __init__(self, run_manager: RunManager):
        self.run_manager = run_manager
    
    def save_interview_data(self, data: dict, filename: str = None) -> str:
        """保存访谈数据"""
        interview_dir = self.run_manager.get_run_path("interview")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interview_data_{timestamp}.json"
        
        filepath = os.path.join(interview_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def save_research_data(self, data: dict, filename: str = None) -> str:
        """保存研究数据"""
        research_dir = self.run_manager.get_run_path("research")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_data_{timestamp}.json"
        
        filepath = os.path.join(research_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def save_pdf_metadata(self, paper_data: dict) -> str:
        """保存PDF元数据"""
        pdfs_dir = os.path.join(self.run_manager.get_run_path("research"), "pdfs")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"paper_{timestamp}_metadata.json"
        filepath = os.path.join(pdfs_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(paper_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def save_workflow_summary(self, summary: dict) -> str:
        """保存工作流程摘要"""
        workflow_dir = self.run_manager.get_run_path("workflow")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"workflow_summary_{timestamp}.json"
        filepath = os.path.join(workflow_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        return filepath
```

### 3. 集成到Agent Groups
```python
# 在InterviewAgentGroup中
class InterviewAgentGroup:
    def __init__(self, api_key: str, run_manager: RunManager = None):
        # ... 现有初始化代码 ...
        self.run_manager = run_manager
        self.data_saver = DataSaver(run_manager) if run_manager else None
    
    def save_interview_data(self, data: str) -> str:
        """保存访谈数据到当前运行目录"""
        if not self.data_saver:
            return "No run manager configured"
        
        timestamp = datetime.now().isoformat()
        interview_data = {
            "timestamp": timestamp,
            "data": data,
            "source": "interview_agent_group",
            "run_id": self.run_manager.current_run_id
        }
        
        filepath = self.data_saver.save_interview_data(interview_data)
        return f"Interview data saved to {filepath}"

# 在ResearchAgentGroup中
class ResearchAgentGroup:
    def __init__(self, api_key: str, run_manager: RunManager = None):
        # ... 现有初始化代码 ...
        self.run_manager = run_manager
        self.data_saver = DataSaver(run_manager) if run_manager else None
    
    def save_research_data(self, data: str) -> str:
        """保存研究数据到当前运行目录"""
        if not self.data_saver:
            return "No run manager configured"
        
        timestamp = datetime.now().isoformat()
        research_data = {
            "timestamp": timestamp,
            "data": data,
            "source": "research_agent_group",
            "run_id": self.run_manager.current_run_id
        }
        
        filepath = self.data_saver.save_research_data(research_data)
        return f"Research data saved to {filepath}"
```

## 🔄 工作流程集成

### 更新主工作流程
```python
class MultiAgentWorkflow:
    def __init__(self):
        # ... 现有初始化代码 ...
        self.run_manager = RunManager(self.data_dir)
        self.data_saver = DataSaver(self.run_manager)
    
    def run_complete_workflow(self):
        """运行完整工作流程"""
        # 创建新的运行
        run_id = self.run_manager.create_new_run()
        print(f"Starting new workflow run: {run_id}")
        
        # 更新阶段状态
        self.run_manager.update_phase_status("interview", "started")
        
        # 访谈阶段
        interview_agent_group = self.agents['interview']
        # ... 访谈逻辑 ...
        
        # 更新访谈阶段状态
        self.run_manager.update_phase_status("interview", "completed")
        self.run_manager.update_phase_status("research", "started")
        
        # 研究阶段
        research_agent_group = self.agents['research']
        # ... 研究逻辑 ...
        
        # 更新研究阶段状态
        self.run_manager.update_phase_status("research", "completed")
        self.run_manager.update_phase_status("workflow", "started")
        
        # 保存工作流程摘要
        workflow_summary = {
            "run_id": run_id,
            "interview_summary": interview_summary,
            "research_summary": research_summary,
            "completed_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        self.data_saver.save_workflow_summary(workflow_summary)
        self.run_manager.update_phase_status("workflow", "completed")
        
        print(f"Workflow completed. Run ID: {run_id}")
        print(f"Results saved in: {self.run_manager.get_run_path()}")
```

## 📊 优势

1. **版本控制**: 每次运行都有独立的历史记录
2. **数据隔离**: 不同运行的数据不会相互干扰
3. **快速访问**: 通过latest链接快速访问最新结果
4. **完整追踪**: 每个运行都有完整的元数据和状态追踪
5. **易于管理**: 可以轻松清理旧运行或归档重要结果
6. **扩展性**: 可以轻松添加新的阶段或数据类型

这种设计让每次运行都有完整的数据追踪，同时保持了系统的整洁和可管理性。
