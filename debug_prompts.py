"""
Prompt调试工具 - 用于测试和修改agent的prompts
"""

import os
import sys

# Add the utils directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from prompt_manager import PromptManager


def main():
    """Prompt调试工具主函数"""
    print("🔧 Prompt调试工具")
    print("=" * 50)
    
    try:
        pm = PromptManager()
        
        while True:
            print("\n可用操作:")
            print("1. 查看所有agents")
            print("2. 查看特定agent的prompts")
            print("3. 测试prompt格式化")
            print("4. 重新加载所有prompts")
            print("5. 重新加载特定agent的prompts")
            print("6. 查看prompt文件路径")
            print("7. 退出")
            
            choice = input("\n请选择操作 (1-7): ").strip()
            
            if choice == "1":
                print("\n📋 可用的Agents:")
                agents = pm.list_available_agents()
                for i, agent in enumerate(agents, 1):
                    print(f"  {i}. {agent}")
            
            elif choice == "2":
                print("\n📋 可用的Agents:")
                agents = pm.list_available_agents()
                for i, agent in enumerate(agents, 1):
                    print(f"  {i}. {agent}")
                
                try:
                    agent_choice = int(input("\n选择agent (输入数字): ")) - 1
                    if 0 <= agent_choice < len(agents):
                        agent_name = agents[agent_choice]
                        print(f"\n🔍 {agent_name} 的Prompts:")
                        prompts = pm.list_agent_prompts(agent_name)
                        for i, prompt_key in enumerate(prompts, 1):
                            print(f"  {i}. {prompt_key}")
                        
                        prompt_choice = int(input("\n选择prompt (输入数字): ")) - 1
                        if 0 <= prompt_choice < len(prompts):
                            prompt_key = prompts[prompt_choice]
                            prompt_content = pm.get_agent_prompt(agent_name, prompt_key)
                            print(f"\n📝 {prompt_key}:")
                            print("-" * 40)
                            print(prompt_content)
                            print("-" * 40)
                    else:
                        print("❌ 无效选择")
                except (ValueError, IndexError):
                    print("❌ 输入无效")
            
            elif choice == "3":
                print("\n📋 可用的Agents:")
                agents = pm.list_available_agents()
                for i, agent in enumerate(agents, 1):
                    print(f"  {i}. {agent}")
                
                try:
                    agent_choice = int(input("\n选择agent (输入数字): ")) - 1
                    if 0 <= agent_choice < len(agents):
                        agent_name = agents[agent_choice]
                        prompts = pm.list_agent_prompts(agent_name)
                        print(f"\n🔍 {agent_name} 的Prompts:")
                        for i, prompt_key in enumerate(prompts, 1):
                            print(f"  {i}. {prompt_key}")
                        
                        prompt_choice = int(input("\n选择prompt (输入数字): ")) - 1
                        if 0 <= prompt_choice < len(prompts):
                            prompt_key = prompts[prompt_choice]
                            
                            # 检查是否需要格式化参数
                            prompt_template = pm.get_agent_prompt(agent_name, prompt_key)
                            if "{" in prompt_template and "}" in prompt_template:
                                print(f"\n📝 原始prompt:")
                                print("-" * 40)
                                print(prompt_template)
                                print("-" * 40)
                                
                                print("\n🔧 此prompt需要格式化参数")
                                print("请输入参数值 (格式: key1=value1, key2=value2):")
                                params_input = input("参数: ").strip()
                                
                                if params_input:
                                    try:
                                        params = {}
                                        for param in params_input.split(','):
                                            key, value = param.strip().split('=')
                                            params[key.strip()] = value.strip()
                                        
                                        formatted_prompt = pm.format_prompt(agent_name, prompt_key, **params)
                                        print(f"\n✅ 格式化后的prompt:")
                                        print("-" * 40)
                                        print(formatted_prompt)
                                        print("-" * 40)
                                    except Exception as e:
                                        print(f"❌ 格式化错误: {e}")
                                else:
                                    print("❌ 未提供参数")
                            else:
                                print(f"\n📝 {prompt_key}:")
                                print("-" * 40)
                                print(prompt_template)
                                print("-" * 40)
                    else:
                        print("❌ 无效选择")
                except (ValueError, IndexError):
                    print("❌ 输入无效")
            
            elif choice == "4":
                pm.reload_prompts()
                print("✅ 所有Prompts已重新加载")
            
            elif choice == "5":
                print("\n📋 可用的Agents:")
                agents = pm.list_available_agents()
                for i, agent in enumerate(agents, 1):
                    print(f"  {i}. {agent}")
                
                try:
                    agent_choice = int(input("\n选择要重新加载的agent (输入数字): ")) - 1
                    if 0 <= agent_choice < len(agents):
                        agent_name = agents[agent_choice]
                        pm.reload_agent_prompts(agent_name)
                        print(f"✅ {agent_name} 的Prompts已重新加载")
                    else:
                        print("❌ 无效选择")
                except (ValueError, IndexError):
                    print("❌ 输入无效")
            
            elif choice == "6":
                print(f"\n📁 Prompts目录: {pm.prompts_dir}")
                print("\n📄 Prompt文件路径:")
                agents = pm.list_available_agents()
                for agent in agents:
                    file_path = os.path.join(pm.prompts_dir, f"{agent}.json")
                    print(f"  {agent}: {file_path}")
            
            elif choice == "7":
                print("👋 再见!")
                break
            
            else:
                print("❌ 无效选择，请重新输入")
    
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
