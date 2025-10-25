"""
Run Manager for EmpathyScale Project
管理每次运行的数据存储和时间戳组织
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional


class RunManager:
    """运行管理器，负责创建和管理每次运行的独立数据目录"""
    
    def __init__(self, base_data_dir: str):
        self.base_data_dir = base_data_dir
        self.runs_dir = os.path.join(base_data_dir, "runs")
        self.templates_dir = os.path.join(base_data_dir, "templates")
        self.current_run_id = None
        self.current_run_dir = None
        
        # 确保基础目录存在
        os.makedirs(self.runs_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def create_new_run(self) -> str:
        """创建新的运行文件夹"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(self.runs_dir, timestamp)
        
        # 创建完整的目录结构
        directories = [
            os.path.join(run_dir, "interview", "intermediate_results"),
            os.path.join(run_dir, "research", "intermediate_results"),
            os.path.join(run_dir, "research", "papers"),
            os.path.join(run_dir, "research", "pdfs"),
            os.path.join(run_dir, "workflow"),
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
        # 保存运行元数据
        metadata = {
            "run_id": timestamp,
            "created_at": datetime.now().isoformat(),
            "status": "initialized",
            "phases": {
                "interview": {
                    "status": "pending", 
                    "started_at": None, 
                    "completed_at": None,
                    "files_created": []
                },
                "research": {
                    "status": "pending", 
                    "started_at": None, 
                    "completed_at": None,
                    "files_created": []
                },
                "workflow": {
                    "status": "pending", 
                    "started_at": None, 
                    "completed_at": None,
                    "files_created": []
                }
            },
            "config": {
                "interview_agent": "interview_agent_group",
                "research_agent": "research_agent_group",
                "workflow_mode": "complete"
            },
            "statistics": {
                "total_files": 0,
                "interview_files": 0,
                "research_files": 0,
                "workflow_files": 0
            }
        }
        
        metadata_path = os.path.join(run_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        # 更新latest链接（Windows兼容）
        latest_path = os.path.join(self.runs_dir, "latest")
        if os.path.exists(latest_path):
            if os.path.islink(latest_path):
                os.unlink(latest_path)
            else:
                shutil.rmtree(latest_path)
        
        # 在Windows上创建目录副本而不是符号链接
        shutil.copytree(run_dir, latest_path)
        
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
    
    def update_phase_status(self, phase: str, status: str, file_created: str = None):
        """更新阶段状态"""
        if not self.current_run_dir:
            return
        
        metadata_path = os.path.join(self.current_run_dir, "metadata.json")
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata["phases"][phase]["status"] = status
            
            if status == "started":
                metadata["phases"][phase]["started_at"] = datetime.now().isoformat()
            elif status == "completed":
                metadata["phases"][phase]["completed_at"] = datetime.now().isoformat()
            
            if file_created:
                metadata["phases"][phase]["files_created"].append({
                    "filename": file_created,
                    "created_at": datetime.now().isoformat()
                })
                metadata["statistics"]["total_files"] += 1
                metadata["statistics"][f"{phase}_files"] += 1
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Failed to update phase status: {e}")
    
    def get_run_info(self) -> Dict:
        """获取当前运行的信息"""
        if not self.current_run_dir:
            return {}
        
        metadata_path = os.path.join(self.current_run_dir, "metadata.json")
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to read run info: {e}")
            return {}
    
    def list_all_runs(self) -> List[Dict]:
        """列出所有运行记录"""
        runs = []
        
        if not os.path.exists(self.runs_dir):
            return runs
        
        for run_id in os.listdir(self.runs_dir):
            if run_id == "latest":
                continue
            
            run_path = os.path.join(self.runs_dir, run_id)
            if not os.path.isdir(run_path):
                continue
            
            metadata_path = os.path.join(run_path, "metadata.json")
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        run_info = json.load(f)
                    runs.append(run_info)
                except Exception as e:
                    print(f"Failed to read run {run_id}: {e}")
        
        # 按创建时间排序
        runs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return runs
    
    def cleanup_old_runs(self, keep_last: int = 10):
        """清理旧的运行记录，保留最近的N个"""
        runs = self.list_all_runs()
        
        if len(runs) <= keep_last:
            return
        
        runs_to_delete = runs[keep_last:]
        
        for run_info in runs_to_delete:
            run_id = run_info["run_id"]
            run_path = os.path.join(self.runs_dir, run_id)
            
            try:
                shutil.rmtree(run_path)
                print(f"Deleted old run: {run_id}")
            except Exception as e:
                print(f"Failed to delete run {run_id}: {e}")


class DataSaver:
    """数据保存器，负责将数据保存到当前运行的目录中"""
    
    def __init__(self, run_manager: RunManager):
        self.run_manager = run_manager
    
    def save_interview_data(self, data: dict, filename: str = None) -> str:
        """保存访谈数据"""
        interview_dir = self.run_manager.get_run_path("interview")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"interview_data_{timestamp}.json"
        
        filepath = os.path.join(interview_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 更新元数据
            self.run_manager.update_phase_status("interview", "active", filename)
            
            return filepath
        except Exception as e:
            print(f"Failed to save interview data: {e}")
            return ""
    
    def save_research_data(self, data: dict, filename: str = None) -> str:
        """保存研究数据"""
        research_dir = self.run_manager.get_run_path("research")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_data_{timestamp}.json"
        
        filepath = os.path.join(research_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 更新元数据
            self.run_manager.update_phase_status("research", "active", filename)
            
            return filepath
        except Exception as e:
            print(f"Failed to save research data: {e}")
            return ""
    
    def save_pdf_metadata(self, paper_data: dict) -> str:
        """保存PDF元数据"""
        pdfs_dir = os.path.join(self.run_manager.get_run_path("research"), "pdfs")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"paper_{timestamp}_metadata.json"
        filepath = os.path.join(pdfs_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(paper_data, f, indent=2, ensure_ascii=False)
            
            # 更新元数据
            self.run_manager.update_phase_status("research", "active", filename)
            
            return filepath
        except Exception as e:
            print(f"Failed to save PDF metadata: {e}")
            return ""
    
    def save_workflow_summary(self, summary: dict) -> str:
        """保存工作流程摘要"""
        workflow_dir = self.run_manager.get_run_path("workflow")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"workflow_summary_{timestamp}.json"
        filepath = os.path.join(workflow_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            # 更新元数据
            self.run_manager.update_phase_status("workflow", "active", filename)
            
            return filepath
        except Exception as e:
            print(f"Failed to save workflow summary: {e}")
            return ""
    
    def save_intermediate_result(self, phase: str, data: dict, filename: str = None) -> str:
        """保存中间结果"""
        intermediate_dir = os.path.join(self.run_manager.get_run_path(phase), "intermediate_results")
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"intermediate_{timestamp}.json"
        
        filepath = os.path.join(intermediate_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # 更新元数据
            self.run_manager.update_phase_status(phase, "active", filename)
            
            return filepath
        except Exception as e:
            print(f"Failed to save intermediate result: {e}")
            return ""


def get_run_manager(data_dir: str = None) -> RunManager:
    """获取运行管理器实例"""
    if not data_dir:
        # 默认使用项目根目录下的data文件夹
        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    
    return RunManager(data_dir)
