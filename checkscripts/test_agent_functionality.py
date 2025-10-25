#!/usr/bin/env python3
"""
Agent Functionality Test Script
检查两个agent组是否能完成各自的功能，以及是否能正确保存信息到data文件夹
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import MultiAgentWorkflow


class AgentFunctionalityChecker:
    """Agent功能检查器"""
    
    def __init__(self):
        self.workflow = MultiAgentWorkflow()
        self.data_dir = "data"
        self.test_results = {
            "interview_agent": {},
            "research_agent": {},
            "data_storage": {},
            "overall": {}
        }
        
    def check_interview_agent_functionality(self) -> Dict[str, Any]:
        """检查Interview Agent的功能"""
        print("=" * 60)
        print("检查 Interview Agent 功能")
        print("=" * 60)
        
        results = {
            "initialization": False,
            "opening_message": False,
            "data_collection": False,
            "sub_agents": False,
            "completion_check": False,
            "summary_generation": False
        }
        
        try:
            interview_agent = self.workflow.agents['interview']
            
            # 1. 检查初始化
            print("1. 检查初始化...")
            if hasattr(interview_agent, 'interview_data') and hasattr(interview_agent, 'sub_agents'):
                results["initialization"] = True
                print("   ✅ Interview Agent 初始化成功")
            else:
                print("   ❌ Interview Agent 初始化失败")
            
            # 2. 检查开场消息
            print("2. 检查开场消息...")
            opening_msg = interview_agent.start_interview()
            if opening_msg and len(opening_msg) > 10:
                results["opening_message"] = True
                print(f"   ✅ 开场消息生成成功: {opening_msg[:50]}...")
            else:
                print("   ❌ 开场消息生成失败")
            
            # 3. 检查子代理
            print("3. 检查子代理...")
            required_sub_agents = ['task_collector', 'environment_analyzer', 'platform_specialist', 'collaboration_expert']
            all_sub_agents_present = all(agent in interview_agent.sub_agents for agent in required_sub_agents)
            if all_sub_agents_present:
                results["sub_agents"] = True
                print("   ✅ 所有子代理初始化成功")
                for agent_name in required_sub_agents:
                    print(f"      - {agent_name}: ✅")
            else:
                print("   ❌ 部分子代理缺失")
            
            # 4. 测试数据收集功能
            print("4. 测试数据收集功能...")
            test_responses = [
                "我们正在评估医疗机器人在医院病房协助护士照顾病人的场景",
                "机器人是人形机器人，具有面部表情和语音功能",
                "这是监督式协作模式，机器人提供情感支持",
                "环境是医院病房，存在高压力情况",
                "我们的目标是测量机器人共情效果和用户情感反应"
            ]
            
            for i, response in enumerate(test_responses, 1):
                print(f"   测试响应 {i}: {response[:30]}...")
                agent_response = interview_agent.process_response(response)
                print(f"   Agent响应: {agent_response[:50]}...")
            
            # 检查数据是否被收集
            summary = interview_agent.get_interview_summary()
            data_collected = any(summary.values())
            if data_collected:
                results["data_collection"] = True
                print("   ✅ 数据收集功能正常")
                print(f"   收集的数据字段: {[k for k, v in summary.items() if v]}")
            else:
                print("   ❌ 数据收集功能异常")
            
            # 5. 检查完成状态检查
            print("5. 检查完成状态检查...")
            is_complete = interview_agent.is_interview_complete()
            results["completion_check"] = True
            print(f"   ✅ 完成状态检查功能正常 (当前状态: {'完成' if is_complete else '未完成'})")
            
            # 6. 检查摘要生成
            print("6. 检查摘要生成...")
            if summary and isinstance(summary, dict):
                results["summary_generation"] = True
                print("   ✅ 摘要生成功能正常")
                print(f"   摘要包含 {len([k for k, v in summary.items() if v])} 个有效字段")
            else:
                print("   ❌ 摘要生成功能异常")
                
        except Exception as e:
            print(f"   ❌ Interview Agent 检查过程中出错: {str(e)}")
        
        return results
    
    def check_research_agent_functionality(self) -> Dict[str, Any]:
        """检查Research Agent的功能"""
        print("\n" + "=" * 60)
        print("检查 Research Agent 功能")
        print("=" * 60)
        
        results = {
            "initialization": False,
            "research_start": False,
            "paper_search": False,
            "methodology_analysis": False,
            "context_insights": False,
            "scale_recommendations": False,
            "sub_agents": False,
            "summary_generation": False
        }
        
        try:
            research_agent = self.workflow.agents['research']
            
            # 1. 检查初始化
            print("1. 检查初始化...")
            if hasattr(research_agent, 'research_data') and hasattr(research_agent, 'sub_agents'):
                results["initialization"] = True
                print("   ✅ Research Agent 初始化成功")
            else:
                print("   ❌ Research Agent 初始化失败")
            
            # 2. 检查子代理
            print("2. 检查子代理...")
            required_sub_agents = ['paper_searcher', 'methodology_analyzer', 'context_specialist', 'scale_designer']
            all_sub_agents_present = all(agent in research_agent.sub_agents for agent in required_sub_agents)
            if all_sub_agents_present:
                results["sub_agents"] = True
                print("   ✅ 所有子代理初始化成功")
                for agent_name in required_sub_agents:
                    print(f"      - {agent_name}: ✅")
            else:
                print("   ❌ 部分子代理缺失")
            
            # 3. 准备测试用的interview summary
            test_interview_summary = {
                "assessment_context": "医疗机器人协助护士照顾病人的场景",
                "robot_platform": "人形机器人，具有面部表情和语音功能",
                "collaboration_pattern": "监督式协作，提供情感支持",
                "environmental_setting": "医院病房环境，存在高压力情况",
                "assessment_goals": ["测量机器人共情效果", "评估用户情感反应"],
                "expected_empathy_forms": ["语言共情", "面部表情", "主动情感支持"],
                "assessment_challenges": ["高压力环境", "病人隐私考虑"],
                "measurement_requirements": ["实时评估", "多模态评估"]
            }
            
            # 4. 测试研究启动
            print("3. 测试研究启动...")
            start_response = research_agent.start_research(test_interview_summary)
            if start_response and len(start_response) > 10:
                results["research_start"] = True
                print(f"   ✅ 研究启动成功: {start_response[:50]}...")
            else:
                print("   ❌ 研究启动失败")
            
            # 5. 测试论文搜索功能
            print("4. 测试论文搜索功能...")
            search_task = "搜索医疗机器人共情测量相关的学术论文"
            search_response = research_agent.process_research_task(search_task)
            if search_response and "paper" in search_response.lower():
                results["paper_search"] = True
                print("   ✅ 论文搜索功能正常")
                print(f"   搜索响应: {search_response[:100]}...")
            else:
                print("   ❌ 论文搜索功能异常")
            
            # 6. 测试方法论分析
            print("5. 测试方法论分析...")
            methodology_task = "分析机器人共情评估研究的方法论"
            methodology_response = research_agent.process_research_task(methodology_task)
            if methodology_response and len(methodology_response) > 50:
                results["methodology_analysis"] = True
                print("   ✅ 方法论分析功能正常")
                print(f"   分析响应: {methodology_response[:100]}...")
            else:
                print("   ❌ 方法论分析功能异常")
            
            # 7. 测试上下文洞察
            print("6. 测试上下文洞察...")
            context_task = "提取医疗场景下共情测量的上下文特定洞察"
            context_response = research_agent.process_research_task(context_task)
            if context_response and len(context_response) > 50:
                results["context_insights"] = True
                print("   ✅ 上下文洞察功能正常")
                print(f"   洞察响应: {context_response[:100]}...")
            else:
                print("   ❌ 上下文洞察功能异常")
            
            # 8. 测试量表设计建议
            print("7. 测试量表设计建议...")
            recommendation_task = "基于研究发现生成共情量表设计建议"
            recommendation_response = research_agent.process_research_task(recommendation_task)
            if recommendation_response and len(recommendation_response) > 50:
                results["scale_recommendations"] = True
                print("   ✅ 量表设计建议功能正常")
                print(f"   建议响应: {recommendation_response[:100]}...")
            else:
                print("   ❌ 量表设计建议功能异常")
            
            # 9. 检查研究摘要生成
            print("8. 检查研究摘要生成...")
            research_summary = research_agent.get_research_summary()
            if research_summary and isinstance(research_summary, dict):
                results["summary_generation"] = True
                print("   ✅ 研究摘要生成功能正常")
                print(f"   摘要包含 {len([k for k, v in research_summary.items() if v])} 个有效字段")
            else:
                print("   ❌ 研究摘要生成功能异常")
                
        except Exception as e:
            print(f"   ❌ Research Agent 检查过程中出错: {str(e)}")
        
        return results
    
    def check_data_storage_functionality(self) -> Dict[str, Any]:
        """检查数据存储功能"""
        print("\n" + "=" * 60)
        print("检查数据存储功能")
        print("=" * 60)
        
        results = {
            "directory_structure": False,
            "interview_data_saving": False,
            "research_data_saving": False,
            "file_permissions": False,
            "data_integrity": False
        }
        
        try:
            # 1. 检查目录结构
            print("1. 检查目录结构...")
            required_dirs = [
                "data",
                "data/intermediate_results",
                "data/intermediate_results/interview_agent_group",
                "data/intermediate_results/research_agent_group",
                "data/papers",
                "data/summaries"
            ]
            
            all_dirs_exist = True
            for dir_path in required_dirs:
                if os.path.exists(dir_path):
                    print(f"   ✅ {dir_path} 存在")
                else:
                    print(f"   ❌ {dir_path} 缺失")
                    all_dirs_exist = False
            
            results["directory_structure"] = all_dirs_exist
            
            # 2. 测试Interview Agent数据保存
            print("2. 测试Interview Agent数据保存...")
            interview_agent = self.workflow.agents['interview']
            
            # 模拟一些数据收集
            test_data = "测试数据：医疗机器人共情评估场景"
            interview_agent.process_response(test_data)
            
            # 检查是否有数据被保存
            summary = interview_agent.get_interview_summary()
            if any(summary.values()):
                results["interview_data_saving"] = True
                print("   ✅ Interview Agent 数据保存功能正常")
            else:
                print("   ❌ Interview Agent 数据保存功能异常")
            
            # 3. 测试Research Agent数据保存
            print("3. 测试Research Agent数据保存...")
            research_agent = self.workflow.agents['research']
            
            # 启动研究并执行任务
            test_summary = {"assessment_context": "测试场景"}
            research_agent.start_research(test_summary)
            research_agent.process_research_task("测试研究任务")
            
            # 检查研究数据
            research_summary = research_agent.get_research_summary()
            if research_summary.get("interview_summary"):
                results["research_data_saving"] = True
                print("   ✅ Research Agent 数据保存功能正常")
            else:
                print("   ❌ Research Agent 数据保存功能异常")
            
            # 4. 检查文件权限
            print("4. 检查文件权限...")
            test_file_path = os.path.join("data", "test_permissions.json")
            try:
                with open(test_file_path, 'w', encoding='utf-8') as f:
                    json.dump({"test": "data"}, f, ensure_ascii=False)
                
                # 尝试读取
                with open(test_file_path, 'r', encoding='utf-8') as f:
                    json.load(f)
                
                # 清理测试文件
                os.remove(test_file_path)
                
                results["file_permissions"] = True
                print("   ✅ 文件读写权限正常")
            except Exception as e:
                print(f"   ❌ 文件权限异常: {str(e)}")
            
            # 5. 检查数据完整性
            print("5. 检查数据完整性...")
            # 检查现有数据文件
            data_files = []
            for root, dirs, files in os.walk("data"):
                for file in files:
                    if file.endswith('.json'):
                        data_files.append(os.path.join(root, file))
            
            if data_files:
                print(f"   发现 {len(data_files)} 个数据文件")
                for file_path in data_files[:3]:  # 只检查前3个文件
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        print(f"   ✅ {file_path} 数据完整")
                    except Exception as e:
                        print(f"   ❌ {file_path} 数据损坏: {str(e)}")
                
                results["data_integrity"] = True
            else:
                print("   ⚠️ 未发现数据文件")
                
        except Exception as e:
            print(f"   ❌ 数据存储检查过程中出错: {str(e)}")
        
        return results
    
    def generate_test_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("生成测试报告")
        print("=" * 60)
        
        # 执行所有检查
        interview_results = self.check_interview_agent_functionality()
        research_results = self.check_research_agent_functionality()
        storage_results = self.check_data_storage_functionality()
        
        # 计算总体结果
        all_results = {
            "interview_agent": interview_results,
            "research_agent": research_results,
            "data_storage": storage_results
        }
        
        # 计算通过率
        total_tests = 0
        passed_tests = 0
        
        for category, results in all_results.items():
            for test_name, result in results.items():
                total_tests += 1
                if result:
                    passed_tests += 1
        
        overall_success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_success_rate": overall_success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "detailed_results": all_results,
            "recommendations": self._generate_recommendations(all_results)
        }
        
        # 保存报告
        report_file = f"checkscripts/agent_functionality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    def _generate_recommendations(self, results: Dict[str, Dict[str, bool]]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # Interview Agent 建议
        interview_results = results["interview_agent"]
        if not interview_results.get("data_collection", True):
            recommendations.append("建议检查Interview Agent的数据收集逻辑")
        if not interview_results.get("sub_agents", True):
            recommendations.append("建议检查Interview Agent的子代理初始化")
        
        # Research Agent 建议
        research_results = results["research_agent"]
        if not research_results.get("paper_search", True):
            recommendations.append("建议改进Research Agent的论文搜索功能")
        if not research_results.get("methodology_analysis", True):
            recommendations.append("建议优化Research Agent的方法论分析能力")
        
        # 数据存储建议
        storage_results = results["data_storage"]
        if not storage_results.get("directory_structure", True):
            recommendations.append("建议检查数据目录结构设置")
        if not storage_results.get("file_permissions", True):
            recommendations.append("建议检查文件读写权限设置")
        
        if not recommendations:
            recommendations.append("所有功能检查通过，系统运行正常")
        
        return recommendations
    
    def print_summary(self, report: Dict[str, Any]):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)
        
        print(f"总体成功率: {report['overall_success_rate']:.1f}%")
        print(f"总测试数: {report['total_tests']}")
        print(f"通过测试: {report['passed_tests']}")
        print(f"失败测试: {report['failed_tests']}")
        
        print("\n详细结果:")
        for category, results in report['detailed_results'].items():
            print(f"\n{category.replace('_', ' ').title()}:")
            for test_name, result in results.items():
                status = "✅ 通过" if result else "❌ 失败"
                print(f"  {test_name}: {status}")
        
        print("\n改进建议:")
        for i, recommendation in enumerate(report['recommendations'], 1):
            print(f"  {i}. {recommendation}")
        
        print(f"\n详细报告已保存到: checkscripts/agent_functionality_report_*.json")


def main():
    """主函数"""
    print("=" * 60)
    print("Agent 功能检查脚本")
    print("=" * 60)
    print("此脚本将检查两个agent组的功能和数据处理能力")
    print()
    
    try:
        checker = AgentFunctionalityChecker()
        report = checker.generate_test_report()
        checker.print_summary(report)
        
        # 返回适当的退出码
        if report['overall_success_rate'] >= 80:
            print("\n🎉 检查完成！系统功能正常")
            return 0
        else:
            print("\n⚠️ 检查完成！发现一些问题需要修复")
            return 1
            
    except Exception as e:
        print(f"\n❌ 检查过程中发生错误: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
