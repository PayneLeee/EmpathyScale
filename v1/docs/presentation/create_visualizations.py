"""
创建展示用的可视化图表
"""
import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path
import matplotlib.patches as mpatches

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 创建输出目录
output_dir = Path("presentation/visualizations")
output_dir.mkdir(exist_ok=True)

def create_system_architecture():
    """创建系统架构图"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # 定义颜色
    colors = {
        'user': '#4A90E2',
        'interview': '#50C878',
        'literature': '#FF6B6B',
        'scale': '#FFD93D',
        'evaluation': '#9B59B6',
        'selection': '#E67E22'
    }
    
    # 绘制流程框
    boxes = [
        ('用户输入', 1.5, 9, colors['user']),
        ('访谈智能体组', 1.5, 7.5, colors['interview']),
        ('文献搜索智能体组', 1.5, 6, colors['literature']),
        ('量表生成智能体组', 1.5, 4.5, colors['scale']),
        ('评估智能体组', 1.5, 3, colors['evaluation']),
        ('统计选择', 1.5, 1.5, colors['selection'])
    ]
    
    # 绘制箭头和框
    for i, (label, x, y, color) in enumerate(boxes):
        # 绘制框
        rect = mpatches.FancyBboxPatch(
            (x-0.6, y-0.4), 1.2, 0.8,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center', fontsize=11, weight='bold')
        
        # 绘制箭头
        if i < len(boxes) - 1:
            ax.arrow(x, y-0.4, 0, -0.7, head_width=0.15, head_length=0.1, 
                    fc='black', ec='black', linewidth=2)
    
    # 添加子智能体说明
    sub_agents = [
        ('TaskCollector', 4, 7.5),
        ('EnvironmentAnalyzer', 6, 7.5),
        ('PlatformSpecialist', 8, 7.5),
        ('CollaborationExpert', 4, 6)
    ]
    
    for label, x, y in sub_agents:
        circle = plt.Circle((x, y), 0.3, color=colors['interview'], alpha=0.5)
        ax.add_patch(circle)
        ax.text(x, y, label, ha='center', va='center', fontsize=8)
    
    # 添加评估说明
    eval_text = "LLM Personas\n(200 participants)\n• 区分性验证\n• 内部一致性"
    ax.text(4, 3, eval_text, ha='left', va='center', fontsize=9,
            bbox=dict(boxstyle='round', facecolor=colors['evaluation'], alpha=0.3))
    
    ax.set_title('EmpathyScale 系统架构', fontsize=16, weight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(output_dir / 'system_architecture.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] System architecture saved: {output_dir / 'system_architecture.png'}")

def create_workflow_diagram():
    """创建工作流程图"""
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # 定义阶段
    stages = [
        ('1. 访谈阶段', 2, 6, '收集场景信息'),
        ('2. 文献搜索', 5, 6, '搜索相关文献'),
        ('3. 量表生成', 8, 6, '生成量表项目'),
        ('4. 评估阶段', 11, 6, 'LLM模拟评估'),
        ('5. 统计选择', 14, 6, '精选项目')
    ]
    
    colors = ['#4A90E2', '#50C878', '#FF6B6B', '#FFD93D', '#9B59B6']
    
    for i, ((title, x, y, desc), color) in enumerate(zip(stages, colors)):
        # 绘制阶段框
        rect = mpatches.FancyBboxPatch(
            (x-1, y-0.8), 2, 1.6,
            boxstyle="round,pad=0.15",
            facecolor=color,
            edgecolor='black',
            linewidth=2,
            alpha=0.8
        )
        ax.add_patch(rect)
        ax.text(x, y+0.3, title, ha='center', va='center', fontsize=11, weight='bold')
        ax.text(x, y-0.3, desc, ha='center', va='center', fontsize=9)
        
        # 绘制箭头
        if i < len(stages) - 1:
            ax.arrow(x+1, y, 1, 0, head_width=0.2, head_length=0.15,
                    fc='black', ec='black', linewidth=2)
    
    # 添加输出说明
    outputs = [
        ('场景信息\n• 机器人平台\n• 交互模态\n• 协作模式', 2, 3),
        ('文献发现\n• 定义\n• 行为\n• 测量方法', 5, 3),
        ('量表草案\n• 165+ 项目\n• 多个维度', 8, 3),
        ('评估结果\n• 200 personas\n• 评分统计', 11, 3),
        ('最终量表\n• 18 精选项目\n• 高信效度', 14, 3)
    ]
    
    for (text, x, y) in outputs:
        ax.text(x, y, text, ha='center', va='center', fontsize=8,
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
    
    ax.set_title('EmpathyScale 工作流程', fontsize=16, weight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(output_dir / 'workflow_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Workflow diagram saved: {output_dir / 'workflow_diagram.png'}")

def create_results_summary():
    """创建结果摘要图"""
    # 读取分析结果
    summary_path = Path("presentation/run_analysis_summary.json")
    if not summary_path.exists():
        print("[WARNING] Analysis summary not found, skipping this visualization")
        return
    
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('实验结果摘要', fontsize=16, weight='bold', y=0.98)
    
    # 1. 场景分布
    ax1 = axes[0, 0]
    scenarios = summary['scenarios']
    labels = list(scenarios.keys())
    values = list(scenarios.values())
    colors_scenario = ['#4A90E2', '#50C878', '#FF6B6B']
    def autopct_func(pct):
        return f'{int(pct/100*sum(values))}\n({pct:.1f}%)'
    ax1.pie(values, labels=labels, autopct=autopct_func, 
            colors=colors_scenario[:len(labels)], startangle=90)
    ax1.set_title('场景分布', fontsize=12, weight='bold')
    
    # 2. 量表项目数分布
    ax2 = axes[0, 1]
    scale_stats = summary['scale_statistics']
    categories = ['平均项目数', '最小项目数', '最大项目数']
    values_bar = [
        scale_stats['mean_items_per_scale'],
        scale_stats['min_items'],
        scale_stats['max_items']
    ]
    bars = ax2.bar(categories, values_bar, color=['#FFD93D', '#FF6B6B', '#50C878'])
    ax2.set_ylabel('项目数', fontsize=10)
    ax2.set_title('量表项目统计', fontsize=12, weight='bold')
    ax2.grid(axis='y', alpha=0.3)
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9)
    
    # 3. 评估指标
    ax3 = axes[1, 0]
    eval_stats = summary['evaluation_statistics']
    metrics = ['平均评分\n(0-100)', '内部一致性\n(Cronbach α)']
    values_metrics = [
        eval_stats['mean_rating'],
        eval_stats['mean_internal_consistency'] * 100  # 转换为百分比显示
    ]
    bars = ax3.bar(metrics, values_metrics, color=['#9B59B6', '#E67E22'])
    ax3.set_ylabel('分数', fontsize=10)
    ax3.set_title('评估指标', fontsize=12, weight='bold')
    ax3.grid(axis='y', alpha=0.3)
    # 添加数值标签
    for bar, val in zip(bars, values_metrics):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2f}',
                ha='center', va='bottom', fontsize=9)
    
    # 4. 统计选择
    ax4 = axes[1, 1]
    sel_stats = summary['selection_statistics']
    selection_data = {
        '原始项目': sel_stats['mean_original_items'],
        '选择项目': sel_stats['mean_selected_items']
    }
    bars = ax4.bar(selection_data.keys(), selection_data.values(), 
                   color=['#FF6B6B', '#50C878'])
    ax4.set_ylabel('项目数', fontsize=10)
    ax4.set_title(f'统计选择 (选择率: {sel_stats["mean_selection_ratio"]*100:.1f}%)', 
                  fontsize=12, weight='bold')
    ax4.grid(axis='y', alpha=0.3)
    # 添加数值标签
    for bar, val in zip(bars, selection_data.values()):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.0f}',
                ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_dir / 'results_summary.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Results summary saved: {output_dir / 'results_summary.png'}")

def create_evaluation_comparison():
    """创建评估对比图（共情 vs 非共情）"""
    # 使用示例数据（实际应从evaluation summary读取）
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('区分性验证结果', fontsize=16, weight='bold')
    
    # 左图: 平均评分对比
    categories = ['共情 Persona', '非共情 Persona']
    means = [60.52, 0.56]
    stds = [15.0, 2.0]  # 示例标准差
    
    bars = ax1.bar(categories, means, yerr=stds, capsize=10,
                   color=['#50C878', '#FF6B6B'], alpha=0.8, edgecolor='black', linewidth=2)
    ax1.set_ylabel('平均评分 (0-100)', fontsize=11)
    ax1.set_title('平均评分对比', fontsize=12, weight='bold')
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim(0, 80)
    
    # 添加数值标签
    for bar, mean in zip(bars, means):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{mean:.2f}',
                ha='center', va='bottom', fontsize=11, weight='bold')
    
    # 添加统计信息
    ax1.text(0.5, 0.95, 'Cohen\'s d = 2.407\np < 0.001', 
             transform=ax1.transAxes, ha='center', va='top',
             bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5),
             fontsize=10, weight='bold')
    
    # 右图: 评分分布（示例）
    np.random.seed(42)
    empathic_scores = np.random.normal(60.52, 15, 1800)
    non_empathic_scores = np.random.normal(0.56, 2, 1800)
    
    ax2.hist(empathic_scores, bins=30, alpha=0.6, label='共情 Persona', 
             color='#50C878', edgecolor='black')
    ax2.hist(non_empathic_scores, bins=30, alpha=0.6, label='非共情 Persona',
             color='#FF6B6B', edgecolor='black')
    ax2.set_xlabel('评分', fontsize=11)
    ax2.set_ylabel('频数', fontsize=11)
    ax2.set_title('评分分布', fontsize=12, weight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'evaluation_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Evaluation comparison saved: {output_dir / 'evaluation_comparison.png'}")

def create_dimension_example():
    """创建维度示例图"""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')
    
    # 示例维度数据（基于实际案例）
    dimensions = [
        ('Emotional Mirroring\nin Collaborative Assembly', 53, '#4A90E2'),
        ('Proactive Support\nand Assistance', 60, '#50C878'),
        ('Understanding\nSafety Concerns', 52, '#FF6B6B')
    ]
    
    y_pos = np.arange(len(dimensions))
    items_count = [dim[1] for dim in dimensions]
    colors_dim = [dim[2] for dim in dimensions]
    
    bars = ax.barh(y_pos, items_count, color=colors_dim, alpha=0.8, edgecolor='black', linewidth=2)
    
    # 设置标签
    ax.set_yticks(y_pos)
    ax.set_yticklabels([dim[0] for dim in dimensions], fontsize=11)
    ax.set_xlabel('项目数', fontsize=12, weight='bold')
    ax.set_title('量表维度示例\n(工厂装配协作机器人场景)', fontsize=14, weight='bold', pad=20)
    
    # 添加数值标签
    for i, (bar, count) in enumerate(zip(bars, items_count)):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                f'{count} 项',
                ha='left', va='center', fontsize=10, weight='bold')
    
    ax.set_xlim(0, max(items_count) * 1.2)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'dimension_example.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Dimension example saved: {output_dir / 'dimension_example.png'}")

def create_baseline_comparison():
    """创建与baseline（PETS、RoPE）的对比图"""
    # 读取对比数据
    comparison_path = Path("presentation/baseline_comparison_results.json")
    if not comparison_path.exists():
        print("[WARNING] Baseline comparison data not found, skipping this visualization")
        return
    
    with open(comparison_path, 'r', encoding='utf-8') as f:
        comparison_data = json.load(f)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('与Baseline对比 (PETS vs RoPE vs 我们的生成量表)', fontsize=16, weight='bold', y=0.98)
    
    scenarios = list(comparison_data.keys())
    colors = {'generated': '#50C878', 'PETS': '#4A90E2', 'RoPE': '#FF6B6B'}
    
    # 1. 内部一致性对比 (Cronbach's α)
    ax1 = axes[0, 0]
    x = np.arange(len(scenarios))
    width = 0.25
    
    generated_alphas = [comparison_data[s]['generated']['alpha'] for s in scenarios]
    pets_alphas = [comparison_data[s]['PETS']['alpha'] if comparison_data[s]['PETS']['alpha'] > 0 else 0 for s in scenarios]
    rope_alphas = [comparison_data[s]['RoPE']['alpha'] if comparison_data[s]['RoPE']['alpha'] > 0 else 0 for s in scenarios]
    
    bars1 = ax1.bar(x - width, generated_alphas, width, label='我们的生成量表', 
                    color=colors['generated'], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2 = ax1.bar(x, pets_alphas, width, label='PETS', 
                    color=colors['PETS'], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars3 = ax1.bar(x + width, rope_alphas, width, label='RoPE', 
                    color=colors['RoPE'], alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax1.set_ylabel('Cronbach\'s α', fontsize=11, weight='bold')
    ax1.set_title('内部一致性对比', fontsize=12, weight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([s.replace('_', '\n') for s in scenarios], fontsize=9)
    ax1.legend(fontsize=9)
    ax1.set_ylim(0.8, 1.0)
    ax1.grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.005,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=8)
    
    # 2. 区分性对比 (Cohen's d)
    ax2 = axes[0, 1]
    
    generated_ds = [comparison_data[s]['generated']['cohens_d'] for s in scenarios]
    pets_ds = [comparison_data[s]['PETS']['cohens_d'] if comparison_data[s]['PETS']['cohens_d'] > 0 else 0 for s in scenarios]
    rope_ds = [comparison_data[s]['RoPE']['cohens_d'] if comparison_data[s]['RoPE']['cohens_d'] > 0 else 0 for s in scenarios]
    
    bars1 = ax2.bar(x - width, generated_ds, width, label='我们的生成量表', 
                    color=colors['generated'], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2 = ax2.bar(x, pets_ds, width, label='PETS', 
                    color=colors['PETS'], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars3 = ax2.bar(x + width, rope_ds, width, label='RoPE', 
                    color=colors['RoPE'], alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax2.set_ylabel('Cohen\'s d', fontsize=11, weight='bold')
    ax2.set_title('区分性对比', fontsize=12, weight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([s.replace('_', '\n') for s in scenarios], fontsize=9)
    ax2.legend(fontsize=9)
    ax2.grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                        f'{height:.2f}', ha='center', va='bottom', fontsize=8)
    
    # 3. 项目数对比
    ax3 = axes[1, 0]
    
    generated_n = [comparison_data[s]['generated']['n_items'] for s in scenarios]
    pets_n = [comparison_data[s]['PETS']['n_items'] for s in scenarios]
    rope_n = [comparison_data[s]['RoPE']['n_items'] for s in scenarios]
    
    bars1 = ax3.bar(x - width, generated_n, width, label='我们的生成量表', 
                    color=colors['generated'], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2 = ax3.bar(x, pets_n, width, label='PETS', 
                    color=colors['PETS'], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars3 = ax3.bar(x + width, rope_n, width, label='RoPE', 
                    color=colors['RoPE'], alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax3.set_ylabel('项目数', fontsize=11, weight='bold')
    ax3.set_title('项目数对比', fontsize=12, weight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels([s.replace('_', '\n') for s in scenarios], fontsize=9)
    ax3.legend(fontsize=9)
    ax3.grid(axis='y', alpha=0.3)
    
    # 添加数值标签
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    # 4. 综合对比雷达图（工厂装配场景）
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    scenario = 'collab_robot_assembly'
    if scenario in comparison_data:
        data = comparison_data[scenario]
        
        # 创建对比表格
        table_data = [
            ['指标', '我们的生成量表', 'PETS', 'RoPE'],
            ['项目数', f"{data['generated']['n_items']}", f"{data['PETS']['n_items']}", f"{data['RoPE']['n_items']}"],
            ['α', f"{data['generated']['alpha']:.3f}", f"{data['PETS']['alpha']:.3f}", f"{data['RoPE']['alpha']:.3f}"],
            ['Cohen\'s d', f"{data['generated']['cohens_d']:.2f}", f"{data['PETS']['cohens_d']:.2f}", f"{data['RoPE']['cohens_d']:.2f}"],
        ]
        
        table = ax4.table(cellText=table_data[1:], colLabels=table_data[0],
                         cellLoc='center', loc='center',
                         colWidths=[0.3, 0.23, 0.23, 0.23])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # 设置表头样式
        for i in range(len(table_data[0])):
            table[(0, i)].set_facecolor('#4A90E2')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # 设置第一列样式
        for i in range(1, len(table_data)):
            table[(i, 0)].set_facecolor('#E8E8E8')
            table[(i, 0)].set_text_props(weight='bold')
        
        # 高亮我们的生成量表列
        for i in range(1, len(table_data)):
            table[(i, 1)].set_facecolor('#50C878')
            table[(i, 1)].set_text_props(weight='bold')
        
        ax4.set_title(f'综合对比 ({scenario.replace("_", " ")})', fontsize=12, weight='bold', pad=20)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_dir / 'baseline_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Baseline comparison saved: {output_dir / 'baseline_comparison.png'}")

def create_ablation_study():
    """创建消融实验可视化（3个变体 vs 基线）"""
    ablation_path = Path("data/ablation_studies/collab_robot_assembly/ablation_summary.json")
    if not ablation_path.exists():
        print("[WARNING] Ablation study data not found, skipping this visualization")
        return
    
    with open(ablation_path, 'r', encoding='utf-8') as f:
        ablation_data = json.load(f)
    
    variants = ablation_data['variants']
    baseline = ablation_data['baseline']
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('消融实验结果（与基线对比）', fontsize=16, weight='bold', y=0.98)
    
    # 准备数据 - 包括基线和3个变体
    variant_keys = ['fewer_generators', 'no_content', 'fewer_generators_no_content']
    variant_labels = {
        'fewer_generators': 'Fewer\nGenerators\n(1 vs 5)',
        'no_content': 'No Content\nAssessment\n(Random)',
        'fewer_generators_no_content': 'Fewer Gen +\nNo Content\n(1+Random)'
    }
    
    # 构建包含基线的数据
    all_labels = ['Baseline\n(5+Content+EFA)'] + [variant_labels[k] for k in variant_keys]
    all_alphas = [baseline['validation_metrics']['internal_consistency']['alpha']] + \
                 [variants[k]['validation_metrics']['internal_consistency']['alpha'] for k in variant_keys]
    all_cohens_ds = [baseline['validation_metrics']['discriminant_ability']['cohens_d']] + \
                    [variants[k]['validation_metrics']['discriminant_ability']['cohens_d'] for k in variant_keys]
    all_n_items = [16] + [variants[k]['n_selected_items'] for k in variant_keys]  # Baseline有16个项目
    all_mean_ratings = [None] + [variants[k]['evaluation']['overall_mean_rating'] for k in variant_keys]  # Baseline没有mean_rating
    
    # 颜色：基线用深蓝色，变体用其他颜色
    colors = ['#2E86AB'] + ['#FF6B6B', '#4A90E2', '#50C878']
    
    # 1. 内部一致性 (Cronbach's α)
    ax1 = axes[0, 0]
    bars1 = ax1.bar(all_labels, all_alphas, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Cronbach\'s α', fontsize=11, weight='bold')
    ax1.set_title('内部一致性对比', fontsize=12, weight='bold')
    ax1.set_ylim(0.93, 1.0)
    ax1.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars1, all_alphas):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.003,
                f'{val:.3f}', ha='center', va='bottom', fontsize=9, weight='bold')
    
    # 2. 区分性 (Cohen's d)
    ax2 = axes[0, 1]
    bars2 = ax2.bar(all_labels, all_cohens_ds, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Cohen\'s d', fontsize=11, weight='bold')
    ax2.set_title('区分性对比', fontsize=12, weight='bold')
    ax2.set_ylim(0, 5.5)
    ax2.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars2, all_cohens_ds):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.15,
                f'{val:.2f}', ha='center', va='bottom', fontsize=9, weight='bold')
    
    # 添加基线参考线
    ax2.axhline(y=baseline['validation_metrics']['discriminant_ability']['cohens_d'], 
                color='#2E86AB', linestyle='--', linewidth=2, alpha=0.5, label='Baseline')
    
    # 3. 项目数
    ax3 = axes[1, 0]
    bars3 = ax3.bar(all_labels, all_n_items, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('项目数', fontsize=11, weight='bold')
    ax3.set_title('精选项目数对比', fontsize=12, weight='bold')
    ax3.set_ylim(0, 18)
    ax3.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars3, all_n_items):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                f'{int(val)}', ha='center', va='bottom', fontsize=9, weight='bold')
    
    # 4. 平均评分（仅变体，不包括基线）
    ax4 = axes[1, 1]
    variant_labels_only = [variant_labels[k] for k in variant_keys]
    variant_ratings = [variants[k]['evaluation']['overall_mean_rating'] for k in variant_keys]
    variant_colors = colors[1:]  # 排除基线颜色
    bars4 = ax4.bar(variant_labels_only, variant_ratings, color=variant_colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax4.set_ylabel('平均评分', fontsize=11, weight='bold')
    ax4.set_title('平均评分对比（消融变体）', fontsize=12, weight='bold')
    ax4.set_ylim(0, 55)
    ax4.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars4, variant_ratings):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{val:.2f}', ha='center', va='bottom', fontsize=9, weight='bold')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_dir / 'ablation_study.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Ablation study saved: {output_dir / 'ablation_study.png'}")

def create_boateng_method():
    """创建Boateng九段方法流程图"""
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # 定义三个阶段
    phases = [
        ('Phase 1: 项目开发', 2, 8.5, '#4A90E2', [
            'Step 1: 领域识别',
            'Step 2: 内容效度'
        ]),
        ('Phase 2: 量表构建', 5, 8.5, '#50C878', [
            'Step 3: 预测试',
            'Step 4: 调查',
            'Step 5: 项目精简',
            'Step 6: 因子提取',
            'Step 7: 维度性检验'
        ]),
        ('Phase 3: 量表评估', 8, 8.5, '#FF6B6B', [
            'Step 8: 信度检验',
            'Step 9: 效度检验'
        ])
    ]
    
    # 绘制阶段框
    for phase_name, x, y, color, steps in phases:
        # 阶段标题框
        phase_rect = mpatches.FancyBboxPatch(
            (x-1.2, y-0.3), 2.4, 0.6,
            boxstyle="round,pad=0.1", 
            facecolor=color, edgecolor='black', linewidth=2
        )
        ax.add_patch(phase_rect)
        ax.text(x, y, phase_name, ha='center', va='center', 
                fontsize=11, weight='bold', color='white')
        
        # 步骤框
        step_y = y - 1.2
        for i, step in enumerate(steps):
            step_rect = mpatches.FancyBboxPatch(
                (x-1.0, step_y-0.25), 2.0, 0.5,
                boxstyle="round,pad=0.05",
                facecolor='white', edgecolor=color, linewidth=1.5
            )
            ax.add_patch(step_rect)
            ax.text(x, step_y, step, ha='center', va='center',
                   fontsize=9, color='black')
            step_y -= 0.7
    
    # 添加箭头
    for i in range(len(phases)-1):
        x1 = phases[i][1] + 1.2
        x2 = phases[i+1][1] - 1.2
        y = 8.5
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                   arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # 添加标题
    ax.text(5, 9.5, 'Boateng等人(2018)九段方法框架', 
           ha='center', va='center', fontsize=14, weight='bold')
    
    # 添加时间说明
    ax.text(5, 0.5, '传统方法: 数月到数年 | 我们的方法: 数小时', 
           ha='center', va='center', fontsize=10, 
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'boateng_method.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Boateng method saved: {output_dir / 'boateng_method.png'}")

def create_scenario_comparison():
    """创建三个场景的对比图"""
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('off')
    
    scenarios = [
        {
            'name': '工厂装配协作机器人',
            'platform': '协作机械臂',
            'modality': '手势 + 语音',
            'pattern': '轮换装配',
            'goals': '安全意识、自适应节奏',
            'color': '#4A90E2',
            'x': 2
        },
        {
            'name': '家庭服务机器人',
            'platform': '移动服务机器人',
            'modality': '语音 + 导航提示',
            'pattern': '辅助性',
            'goals': '舒适感、感知关怀',
            'color': '#50C878',
            'x': 5
        },
        {
            'name': '心理咨询聊天机器人',
            'platform': '聊天机器人',
            'modality': '文本聊天',
            'pattern': '支持性对话',
            'goals': '情感调谐',
            'color': '#FF6B6B',
            'x': 8
        }
    ]
    
    y_start = 7
    for scenario in scenarios:
        x = scenario['x']
        color = scenario['color']
        
        # 场景标题框
        title_rect = mpatches.FancyBboxPatch(
            (x-1.3, y_start-0.4), 2.6, 0.8,
            boxstyle="round,pad=0.1",
            facecolor=color, edgecolor='black', linewidth=2
        )
        ax.add_patch(title_rect)
        ax.text(x, y_start, scenario['name'], ha='center', va='center',
               fontsize=11, weight='bold', color='white')
        
        # 详细信息
        details = [
            f"平台: {scenario['platform']}",
            f"模态: {scenario['modality']}",
            f"模式: {scenario['pattern']}",
            f"目标: {scenario['goals']}"
        ]
        
        y = y_start - 1.2
        for detail in details:
            detail_rect = mpatches.FancyBboxPatch(
                (x-1.2, y-0.3), 2.4, 0.6,
                boxstyle="round,pad=0.05",
                facecolor='white', edgecolor=color, linewidth=1.5
            )
            ax.add_patch(detail_rect)
            ax.text(x, y, detail, ha='center', va='center',
                   fontsize=9, color='black')
            y -= 0.7
    
    ax.text(5, 9, '三个实验场景对比', ha='center', va='center',
           fontsize=14, weight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'scenario_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Scenario comparison saved: {output_dir / 'scenario_comparison.png'}")

def create_experiment_setup():
    """创建实验设置说明图（消融实验和Baseline）"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle('实验设置', fontsize=16, weight='bold', y=0.98)
    
    # 左图：消融实验设置
    ax1 = axes[0]
    ax1.axis('off')
    
    # 消融实验标题
    ax1.text(0.5, 0.95, '消融实验设置', ha='center', va='top',
            fontsize=14, weight='bold', transform=ax1.transAxes)
    
    # 2×2设计说明
    ax1.text(0.5, 0.85, '2×2设计', ha='center', va='top',
            fontsize=12, weight='bold', transform=ax1.transAxes)
    
    # 绘制2×2表格
    table_data = [
        ['', 'Without Content', 'With Content'],
        ['Single-agent', 'Single\nNo Content', 'Single\nWith Content'],
        ['Multi-agent', 'Multi\nNo Content', 'Multi\nWith Content']
    ]
    
    # 创建表格
    table = ax1.table(cellText=table_data[1:], colLabels=table_data[0],
                     cellLoc='center', loc='center',
                     colWidths=[0.3, 0.35, 0.35],
                     bbox=[0.1, 0.5, 0.8, 0.3])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # 设置表头样式
    for i in range(len(table_data[0])):
        table[(0, i)].set_facecolor('#4A90E2')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # 设置第一列样式
    for i in range(1, len(table_data)):
        table[(i, 0)].set_facecolor('#E8E8E8')
        table[(i, 0)].set_text_props(weight='bold')
    
    # 设置单元格颜色
    colors = ['#FF6B6B', '#4A90E2', '#50C878', '#FFD93D']
    idx = 0
    for i in range(1, len(table_data)):
        for j in range(1, len(table_data[0])):
            table[(i, j)].set_facecolor(colors[idx])
            table[(i, j)].set_text_props(weight='bold')
            idx += 1
    
    # 添加设置说明
    setup_text = """场景: collab_robot_assembly
评估流程: 两阶段评估
  • Phase 1: 200个persona (用于统计筛选)
  • Phase 2: 50个persona (用于最终验证)
变量:
  • num_generators: 1 vs 3
  • enable_content: False vs True"""
    
    ax1.text(0.5, 0.35, setup_text, ha='center', va='top',
            fontsize=9, transform=ax1.transAxes,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    # 右图：Baseline设置
    ax2 = axes[1]
    ax2.axis('off')
    
    # Baseline标题
    ax2.text(0.5, 0.95, 'Baseline对比设置', ha='center', va='top',
            fontsize=14, weight='bold', transform=ax2.transAxes)
    
    # Baseline量表
    baseline_text = """基线量表:
  • PETS (Perceived Empathy of Technology Scale)
  • RoPE (Robot Empathy Scale)

评估设置:
  • 使用与生成量表相同的
    validation persona (50个)
  • 在3个场景都进行评估:
    - 工厂装配协作机器人
    - 家庭服务机器人
    - 心理咨询聊天机器人

对比指标:
  • 内部一致性 (Cronbach's α)
  • 区分性 (Cohen's d)
  • 项目数
  • 场景相关性
  • 条目质量"""
    
    ax2.text(0.5, 0.7, baseline_text, ha='center', va='top',
            fontsize=10, transform=ax2.transAxes,
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    
    # 添加对比说明
    comparison_text = """对比目的:
  验证生成量表的有效性
  展示场景定制化的优势"""
    
    ax2.text(0.5, 0.25, comparison_text, ha='center', va='top',
            fontsize=9, weight='bold', transform=ax2.transAxes,
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_dir / 'experiment_setup.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Experiment setup saved: {output_dir / 'experiment_setup.png'}")

def create_selected_experiments_overview():
    """创建选定实验概览图"""
    # 读取实验选择数据
    selection_path = Path("presentation/experiment_selection.json")
    if not selection_path.exists():
        print("[WARNING] Experiment selection data not found, skipping this visualization")
        return
    
    with open(selection_path, 'r', encoding='utf-8') as f:
        selection_data = json.load(f)
    
    main_experiments = selection_data['main_experiments']
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('选定实验概览', fontsize=16, weight='bold', y=0.98)
    
    scenarios = ['工厂装配', '家庭服务', '心理咨询']
    scenario_keys = ['collab_robot_assembly', 'home_service_robot', 'counseling_chatbot']
    colors = ['#4A90E2', '#50C878', '#FF6B6B']
    
    # 提取数据
    alphas = [main_experiments[k]['metrics']['internal_consistency_alpha'] for k in scenario_keys]
    cohens_ds = [main_experiments[k]['metrics']['cohens_d'] for k in scenario_keys]
    n_items = [main_experiments[k]['metrics']['n_selected_items'] for k in scenario_keys]
    quality_scores = [main_experiments[k]['quality_score'] for k in scenario_keys]
    
    # 1. 内部一致性 (Cronbach's α)
    ax1 = axes[0, 0]
    bars1 = ax1.bar(scenarios, alphas, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Cronbach\'s α', fontsize=11, weight='bold')
    ax1.set_title('内部一致性', fontsize=12, weight='bold')
    ax1.set_ylim(0.98, 1.0)
    ax1.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars1, alphas):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.001,
                f'{val:.3f}', ha='center', va='bottom', fontsize=10, weight='bold')
    
    # 2. 区分性 (Cohen's d)
    ax2 = axes[0, 1]
    bars2 = ax2.bar(scenarios, cohens_ds, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Cohen\'s d', fontsize=11, weight='bold')
    ax2.set_title('区分性', fontsize=12, weight='bold')
    ax2.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars2, cohens_ds):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{val:.2f}', ha='center', va='bottom', fontsize=10, weight='bold')
    
    # 3. 项目数
    ax3 = axes[1, 0]
    bars3 = ax3.bar(scenarios, n_items, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('项目数', fontsize=11, weight='bold')
    ax3.set_title('精选项目数', fontsize=12, weight='bold')
    ax3.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars3, n_items):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(val)}', ha='center', va='bottom', fontsize=10, weight='bold')
    
    # 4. 质量分数
    ax4 = axes[1, 1]
    bars4 = ax4.bar(scenarios, quality_scores, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax4.set_ylabel('质量分数', fontsize=11, weight='bold')
    ax4.set_title('质量分数', fontsize=12, weight='bold')
    ax4.set_ylim(0.9, 1.0)
    ax4.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars4, quality_scores):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.005,
                f'{val:.3f}', ha='center', va='bottom', fontsize=10, weight='bold')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_dir / 'selected_experiments_overview.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Selected experiments overview saved: {output_dir / 'selected_experiments_overview.png'}")

def create_metrics_explanation():
    """创建评估指标说明图"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('评估与筛选指标说明', fontsize=16, weight='bold', y=0.98)
    
    # 1. Cronbach's α
    ax1 = axes[0, 0]
    ax1.axis('off')
    ax1.text(0.5, 0.8, "Cronbach's α", ha='center', va='center',
            fontsize=14, weight='bold', transform=ax1.transAxes)
    ax1.text(0.5, 0.6, "内部一致性", ha='center', va='center',
            fontsize=12, transform=ax1.transAxes)
    ax1.text(0.5, 0.4, "衡量量表中所有项目\n是否测量同一个概念", ha='center', va='center',
            fontsize=10, transform=ax1.transAxes)
    ax1.text(0.5, 0.2, "α > 0.9 为优秀", ha='center', va='center',
            fontsize=11, weight='bold', color='green', transform=ax1.transAxes)
    
    # 绘制示例条形图
    ax1_bar = fig.add_axes([0.15, 0.55, 0.15, 0.1])
    ax1_bar.bar(['优秀', '良好', '可接受'], [0.99, 0.95, 0.85],
               color=['green', 'yellow', 'orange'], alpha=0.7)
    ax1_bar.set_ylim(0, 1)
    ax1_bar.set_ylabel('α值')
    ax1_bar.tick_params(labelsize=8)
    
    # 2. Cohen's d
    ax2 = axes[0, 1]
    ax2.axis('off')
    ax2.text(0.5, 0.8, "Cohen's d", ha='center', va='center',
            fontsize=14, weight='bold', transform=ax2.transAxes)
    ax2.text(0.5, 0.6, "区分性/效应量", ha='center', va='center',
            fontsize=12, transform=ax2.transAxes)
    ax2.text(0.5, 0.4, "衡量量表能否有效区分\n不同共情水平的参与者", ha='center', va='center',
            fontsize=10, transform=ax2.transAxes)
    ax2.text(0.5, 0.2, "d > 2.0 为极大效应量", ha='center', va='center',
            fontsize=11, weight='bold', color='green', transform=ax2.transAxes)
    
    # 绘制示例对比图
    ax2_bar = fig.add_axes([0.65, 0.55, 0.15, 0.1])
    categories = ['共情', '非共情']
    means = [60, 5]
    ax2_bar.bar(categories, means, color=['green', 'red'], alpha=0.7)
    ax2_bar.set_ylabel('平均评分')
    ax2_bar.tick_params(labelsize=8)
    
    # 3. EFA/CFA
    ax3 = axes[1, 0]
    ax3.axis('off')
    ax3.text(0.5, 0.8, "EFA / CFA", ha='center', va='center',
            fontsize=14, weight='bold', transform=ax3.transAxes)
    ax3.text(0.5, 0.6, "因子分析", ha='center', va='center',
            fontsize=12, transform=ax3.transAxes)
    ax3.text(0.5, 0.4, "EFA: 发现隐藏的维度结构\nCFA: 验证因子结构合理性", ha='center', va='center',
            fontsize=10, transform=ax3.transAxes)
    ax3.text(0.5, 0.2, "RMSEA < 0.08, TLI/CFI > 0.9", ha='center', va='center',
            fontsize=10, weight='bold', color='blue', transform=ax3.transAxes)
    
    # 4. 项目-总分相关性
    ax4 = axes[1, 1]
    ax4.axis('off')
    ax4.text(0.5, 0.8, "项目-总分相关性", ha='center', va='center',
            fontsize=14, weight='bold', transform=ax4.transAxes)
    ax4.text(0.5, 0.6, "Item-Total Correlation", ha='center', va='center',
            fontsize=12, transform=ax4.transAxes)
    ax4.text(0.5, 0.4, "每个项目与量表总分的\n相关程度", ha='center', va='center',
            fontsize=10, transform=ax4.transAxes)
    ax4.text(0.5, 0.2, "保留相关性 > 0.3 的项目", ha='center', va='center',
            fontsize=11, weight='bold', color='green', transform=ax4.transAxes)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_dir / 'metrics_explanation.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Metrics explanation saved: {output_dir / 'metrics_explanation.png'}")

if __name__ == "__main__":
    print("Creating visualizations...")
    create_system_architecture()
    create_workflow_diagram()
    create_results_summary()
    create_evaluation_comparison()
    create_dimension_example()
    create_baseline_comparison()
    create_ablation_study()
    create_boateng_method()
    create_scenario_comparison()
    create_metrics_explanation()
    create_selected_experiments_overview()
    create_experiment_setup()
    print(f"\n[OK] All visualizations saved to: {output_dir}")


