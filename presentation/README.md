# EmpathyScale 项目展示材料

本文件夹包含项目展示所需的所有材料，包括展示内容、可视化图表和分析脚本。

## 📁 文件结构

```
presentation/
├── README.md                          # 本文件
├── SUMMARY.md                         # 完成工作总结
├── EXPERIMENT_DIRECTORIES.md          # 实验目录快速参考
├── design_plan.md                     # 设计计划
├── presentation_content.md            # 详细展示内容（Markdown格式）
├── presentation_slides.md            # 幻灯片版本（适合转换为PPT）
├── item_analysis.md                  # 条目定性分析
├── experiment_selection_guide.md     # 实验选择说明
├── experiment_selection.json         # 实验选择结果
├── analyze_runs.py                    # 数据分析脚本
├── select_best_experiments.py        # 最佳实验选择脚本
├── create_visualizations.py           # 可视化生成脚本
├── baseline_comparison_analysis.py    # Baseline对比分析脚本
├── baseline_comparison.md             # Baseline对比分析文档
├── baseline_comparison_results.json   # Baseline对比数据
├── extract_persona_examples.py       # Persona示例提取脚本
├── persona_examples.json              # Persona示例数据
├── run_analysis_summary.json          # 运行数据分析摘要
└── visualizations/                    # 可视化图表目录
    ├── system_architecture.png        # 系统架构图
    ├── workflow_diagram.png           # 工作流程图
    ├── results_summary.png            # 结果摘要图
    ├── evaluation_comparison.png      # 评估对比图
    ├── dimension_example.png          # 维度示例图
    ├── baseline_comparison.png        # Baseline对比图
    ├── ablation_study.png             # 消融实验结果图
    ├── boateng_method.png             # Boateng九段方法流程图
    ├── scenario_comparison.png        # 三个场景对比图
    ├── metrics_explanation.png        # 评估指标说明图
    ├── selected_experiments_overview.png  # 选定实验概览图
    └── experiment_setup.png           # 实验设置图（消融实验和Baseline）（新增）
```

## 📋 实验选择

### 主实验（每个场景选择最佳）

基于质量评分系统选择的最佳实验：

1. **工厂装配协作机器人**: `data/runs/2025-12-22_215026`
   - 质量分数: 0.997
   - α = 0.992, Cohen's d = 4.634
   - 16个项目，2个因子

2. **家庭服务机器人**: `data/runs/2025-12-22_210718`
   - 质量分数: 0.947
   - α = 0.993, Cohen's d = 5.238
   - 12个项目，3因子

3. **心理咨询聊天机器人**: `data/runs/2025-12-22_212205`
   - 质量分数: 1.000
   - α = 0.999, Cohen's d = 15.473
   - 15个项目，2个因子

### 消融实验

消融实验目录: `data/ablation_studies/collab_robot_assembly/`

基线配置: 5 generators + Content Assessment + EFA+CFA
- Run ID: `data/runs/2025-12-22_215026` (主实验)
- α = 0.992, Cohen's d = 4.634, 16 items

三个消融变体:
- Fewer Generators (1 vs 5): `data/runs/2025-12-23_142045`
- No Content Assessment (random selection): `data/runs/2025-12-23_142911`
- Fewer Generators + No Content: `data/runs/2025-12-23_143310`

详细说明见: `experiment_selection_guide.md`

## 🎯 展示内容概览

### 1. 问题陈述
- 人机协作中感知共情的重要性
- 现有评估工具的局限性
- 研究问题和意义

### 2. 相关工作
- PETS和RoPE等现有量表
- 传统量表构建方法
- 我们的贡献

### 3. 技术方法
- 多智能体系统架构
- 五个核心智能体组的功能
- 技术特点

### 4. 实验与结果
- **场景设定**: 三个不同的人机协作场景（工厂装配、家庭服务、心理咨询）
- **Persona示例**: 多样化的LLM模拟persona，展示不同背景和共情水平
- 17次运行，3个场景
- 平均111.5项/量表，内部一致性α=0.968
- 强区分性（Cohen's d = 2.407）
- **与Baseline对比**: 我们的生成量表在定量和定性指标上都显著优于PETS和RoPE

### 5. 关键洞察
- 成功因素
- 挑战与解决方案
- 主要发现

### 6. 未来工作
- 短期改进方向
- 长期研究方向

## 📊 数据统计摘要

基于17次完整运行的统计：

- **总运行次数**: 17
- **场景分布**: 
  - 工厂装配协作机器人: 11次
  - 家庭服务机器人: 3次
  - 心理咨询聊天机器人: 3次
- **量表统计**:
  - 平均项目数: 111.5项
  - 项目数范围: 44-191项
  - 识别维度数: 31个独特维度
- **评估统计**:
  - 平均参与者数: 200
  - 平均评分: 41.85/100
  - 平均内部一致性: 0.968 (Cronbach's α)
- **统计选择**:
  - 平均原始项目数: 111.5项
  - 平均选择项目数: 16.2项
  - 平均选择比例: 18.6%

## 🖼️ 可视化图表说明

### system_architecture.png
展示系统的整体架构，包括：
- 用户输入到最终输出的完整流程
- 各个智能体组的位置和作用
- 子智能体的组织结构

### workflow_diagram.png
展示详细的工作流程：
- 5个主要阶段
- 每个阶段的输入输出
- 数据流向

### results_summary.png
包含4个子图：
1. 场景分布饼图
2. 量表项目统计柱状图
3. 评估指标柱状图
4. 统计选择对比图

### evaluation_comparison.png
展示区分性验证结果：
- 共情vs非共情persona的平均评分对比
- 评分分布直方图
- 统计显著性信息

### dimension_example.png
展示工厂装配场景的三个主要维度：
- Emotional Mirroring in Collaborative Assembly
- Proactive Support and Assistance
- Understanding Safety Concerns

### baseline_comparison.png
展示与baseline（PETS、RoPE）的对比：
- 内部一致性（Cronbach's α）对比
- 区分性（Cohen's d）对比
- 项目数对比
- 综合对比表格（工厂装配场景）

### ablation_study.png
展示消融实验结果（2×2设计）：
- 内部一致性（Cronbach's α）对比（4个变体）
- 区分性（Cohen's d）对比（4个变体）
- 项目数对比（4个变体）
- 平均评分对比（4个变体）

### boateng_method.png
展示Boateng等人(2018)的九段方法框架：
- Phase 1: 项目开发（2个步骤）
- Phase 2: 量表构建（5个步骤）
- Phase 3: 量表评估（2个步骤）
- 对比传统方法（数月到数年）vs 我们的方法（数小时）

### scenario_comparison.png
展示三个实验场景的对比：
- 工厂装配协作机器人：协作机械臂，手势+语音，轮换装配
- 家庭服务机器人：移动服务机器人，语音+导航提示，辅助性
- 心理咨询聊天机器人：聊天机器人，文本聊天，支持性对话

### metrics_explanation.png
展示评估与筛选指标的说明：
- Cronbach's α（内部一致性）：含义、解释、标准
- Cohen's d（区分性）：含义、解释、标准
- EFA/CFA（因子分析）：方法、标准
- 项目-总分相关性：含义、筛选标准

### selected_experiments_overview.png
展示选定的三个主实验的关键指标：
- 内部一致性（Cronbach's α）对比
- 区分性（Cohen's d）对比
- 项目数对比
- 质量分数对比

### experiment_setup.png
展示消融实验和Baseline对比的设置：
- 消融实验：2×2设计（Single/Multi-agent × With/Without Content Assessment）
- Baseline对比：PETS和RoPE的设置和对比指标
- 评估流程说明（两阶段评估）

## 🚀 使用方法

### 重新生成数据分析
```bash
python presentation/analyze_runs.py
```

### 重新生成可视化图表
```bash
python presentation/create_visualizations.py
```

### 重新生成Baseline对比分析
```bash
python presentation/baseline_comparison_analysis.py
```

### 重新提取Persona示例
```bash
python presentation/extract_persona_examples.py
```

### 查看展示内容
- 详细内容: 打开 `presentation_content.md`
- 幻灯片版本: 打开 `presentation_slides.md`

## 📝 展示建议

### 时间分配（7分钟总时长）
1. **问题陈述** (1分钟)
   - 快速介绍背景和问题
   - 强调研究意义

2. **技术方法** (2分钟)
   - 展示系统架构图
   - 简要介绍各智能体组
   - 强调自动化和场景定制

3. **实验结果** (2.5分钟)
   - 展示结果摘要图
   - 重点介绍关键指标
   - 展示案例

4. **关键洞察** (1分钟)
   - 成功因素
   - 主要发现

5. **总结与未来工作** (0.5分钟)
   - 主要贡献
   - 未来方向

### 展示技巧
- 使用可视化图表增强理解
- 重点强调自动化和场景定制化
- 突出高内部一致性和强区分性
- 准备回答关于LLM模拟评估的问题

## 📧 联系信息

如有问题或需要更多信息，请参考项目主README或联系项目维护者。


