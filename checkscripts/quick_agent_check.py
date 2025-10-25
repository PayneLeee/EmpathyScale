#!/usr/bin/env python3
"""
快速功能检查脚本
用于快速验证两个agent组的基本功能是否正常
"""

import json
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import MultiAgentWorkflow


def quick_check():
    """快速检查两个agent组的基本功能"""
    print("=" * 50)
    print("快速功能检查")
    print("=" * 50)
    
    try:
        # 初始化workflow
        print("1. 初始化Multi-Agent Workflow...")
        workflow = MultiAgentWorkflow()
        print("   ✅ Workflow初始化成功")
        
        # 检查Interview Agent
        print("2. 检查Interview Agent...")
        interview_agent = workflow.agents['interview']
        
        # 测试开场消息
        opening_msg = interview_agent.start_interview()
        if opening_msg and len(opening_msg) > 10:
            print("   ✅ 开场消息生成正常")
        else:
            print("   ❌ 开场消息生成异常")
            return False
        
        # 测试数据收集
        test_response = "测试：医疗机器人共情评估场景"
        agent_response = interview_agent.process_response(test_response)
        if agent_response and len(agent_response) > 10:
            print("   ✅ 数据收集功能正常")
        else:
            print("   ❌ 数据收集功能异常")
            return False
        
        # 检查Research Agent
        print("3. 检查Research Agent...")
        research_agent = workflow.agents['research']
        
        # 测试研究启动
        test_summary = {
            "assessment_context": "医疗机器人协助护士",
            "robot_platform": "人形机器人",
            "collaboration_pattern": "监督式协作",
            "environmental_setting": "医院病房"
        }
        
        start_response = research_agent.start_research(test_summary)
        if start_response and len(start_response) > 10:
            print("   ✅ 研究启动功能正常")
        else:
            print("   ❌ 研究启动功能异常")
            return False
        
        # 测试研究任务处理
        research_response = research_agent.process_research_task("搜索医疗机器人共情测量论文")
        if research_response and len(research_response) > 10:
            print("   ✅ 研究任务处理正常")
        else:
            print("   ❌ 研究任务处理异常")
            return False
        
        # 检查数据存储
        print("4. 检查数据存储...")
        required_dirs = [
            "data",
            "data/intermediate_results",
            "data/intermediate_results/interview_agent_group",
            "data/intermediate_results/research_agent_group",
            "data/papers",
            "data/summaries"
        ]
        
        all_dirs_exist = all(os.path.exists(dir_path) for dir_path in required_dirs)
        if all_dirs_exist:
            print("   ✅ 数据目录结构完整")
        else:
            print("   ❌ 数据目录结构不完整")
            return False
        
        # 检查数据文件
        data_files = []
        for root, dirs, files in os.walk("data"):
            for file in files:
                if file.endswith('.json'):
                    data_files.append(os.path.join(root, file))
        
        if data_files:
            print(f"   ✅ 发现 {len(data_files)} 个数据文件")
        else:
            print("   ⚠️ 未发现数据文件")
        
        print("\n" + "=" * 50)
        print("🎉 快速检查完成！所有基本功能正常")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {str(e)}")
        return False


def check_data_integrity():
    """检查数据完整性"""
    print("\n" + "=" * 50)
    print("数据完整性检查")
    print("=" * 50)
    
    try:
        data_files = []
        for root, dirs, files in os.walk("data"):
            for file in files:
                if file.endswith('.json'):
                    data_files.append(os.path.join(root, file))
        
        if not data_files:
            print("未发现数据文件")
            return True
        
        print(f"检查 {len(data_files)} 个数据文件...")
        
        valid_files = 0
        for file_path in data_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查基本结构
                if isinstance(data, dict) and ('timestamp' in data or 'data' in data):
                    valid_files += 1
                    print(f"   ✅ {os.path.basename(file_path)}")
                else:
                    print(f"   ⚠️ {os.path.basename(file_path)} (结构异常)")
                    
            except Exception as e:
                print(f"   ❌ {os.path.basename(file_path)} (损坏: {str(e)})")
        
        print(f"\n数据完整性: {valid_files}/{len(data_files)} 文件正常")
        return valid_files == len(data_files)
        
    except Exception as e:
        print(f"数据完整性检查失败: {str(e)}")
        return False


def main():
    """主函数"""
    print("Multi-Agent Workflow 快速检查")
    print("检查两个agent组的基本功能和数据存储")
    print()
    
    # 执行快速检查
    basic_check = quick_check()
    
    # 执行数据完整性检查
    data_check = check_data_integrity()
    
    # 总结
    print("\n" + "=" * 50)
    print("检查总结")
    print("=" * 50)
    
    if basic_check and data_check:
        print("✅ 所有检查通过，系统运行正常")
        print("💡 如需详细检查，请运行: python checkscripts/test_agent_functionality.py")
        return 0
    else:
        print("❌ 发现问题，建议运行完整检查")
        print("💡 运行完整检查: python checkscripts/test_agent_functionality.py")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
