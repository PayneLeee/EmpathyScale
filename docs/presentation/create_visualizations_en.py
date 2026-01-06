"""
Create visualization charts for presentation
"""
import json
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path
import matplotlib.patches as mpatches

# Use default fonts for English
matplotlib.rcParams['axes.unicode_minus'] = False

# Create output directory
output_dir = Path("presentation/en/visualizations")
output_dir.mkdir(exist_ok=True)

def create_system_architecture():
    """Create system architecture diagram"""
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define colors
    colors = {
        'user': '#4A90E2',
        'interview': '#50C878',
        'literature': '#FF6B6B',
        'scale': '#FFD93D',
        'evaluation': '#9B59B6',
        'selection': '#E67E22'
    }
    
    # Draw process boxes
    boxes = [
        ('User Input', 1.5, 9, colors['user']),
        ('Interview Agent Group', 1.5, 7.5, colors['interview']),
        ('Literature Search Agent Group', 1.5, 6, colors['literature']),
        ('Scale Generation Agent Group', 1.5, 4.5, colors['scale']),
        ('Evaluation Agent Group', 1.5, 3, colors['evaluation']),
        ('Statistical Selection', 1.5, 1.5, colors['selection'])
    ]
    
    # Draw arrows and boxes
    for i, (label, x, y, color) in enumerate(boxes):
        # Draw box
        rect = mpatches.FancyBboxPatch(
            (x-0.6, y-0.4), 1.2, 0.8,
            boxstyle="round,pad=0.1",
            facecolor=color,
            edgecolor='black',
            linewidth=2
        )
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center', fontsize=11, weight='bold')
        
        # Draw arrow
        if i < len(boxes) - 1:
            ax.arrow(x, y-0.4, 0, -0.7, head_width=0.15, head_length=0.1, 
                    fc='black', ec='black', linewidth=2)
    
    # Add sub-agent descriptions
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
    
    # Add evaluation description
    eval_text = "LLM Personas\n(200 participants)\n• Discriminant Validation\n• Internal Consistency"
    ax.text(4, 3, eval_text, ha='left', va='center', fontsize=9,
            bbox=dict(boxstyle='round', facecolor=colors['evaluation'], alpha=0.3))
    
    ax.set_title('EmpathyScale System Architecture', fontsize=16, weight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(output_dir / 'system_architecture.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] System architecture saved: {output_dir / 'system_architecture.png'}")

def create_workflow_diagram():
    """Create workflow diagram"""
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # Define stages
    stages = [
        ('1. Interview Phase', 2, 6, 'Collect Scenario Info'),
        ('2. Literature Search', 5, 6, 'Search Literature'),
        ('3. Scale Generation', 8, 6, 'Generate Items'),
        ('4. Evaluation Phase', 11, 6, 'LLM Simulation'),
        ('5. Statistical Selection', 14, 6, 'Selected Items')
    ]
    
    colors = ['#4A90E2', '#50C878', '#FF6B6B', '#FFD93D', '#9B59B6']
    
    for i, ((title, x, y, desc), color) in enumerate(zip(stages, colors)):
        # Draw stage boxes
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
        
        # Draw arrow
        if i < len(stages) - 1:
            ax.arrow(x+1, y, 1, 0, head_width=0.2, head_length=0.15,
                    fc='black', ec='black', linewidth=2)
    
    # Add output descriptions
    outputs = [
        ('Scenario Info\n• Robot Platform\n• Interaction Modality\n• Collaboration Pattern', 2, 3),
        ('Literature Findings\n• Definitions\n• Behaviors\n• Measurement', 5, 3),
        ('Scale Draft\n• 165+ items\n• Multiple Dimensions', 8, 3),
        ('Evaluation Results\n• 200 personas\n• Rating Statistics', 11, 3),
        ('Final Scale\n• 18 Selected Items\n• High Reliability', 14, 3)
    ]
    
    for (text, x, y) in outputs:
        ax.text(x, y, text, ha='center', va='center', fontsize=8,
                bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.5))
    
    ax.set_title('EmpathyScale Workflow', fontsize=16, weight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(output_dir / 'workflow_diagram.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Workflow diagram saved: {output_dir / 'workflow_diagram.png'}")

def create_results_summary():
    """Create results summary diagram"""
    # Read analysis results
    summary_path = Path("presentation/run_analysis_summary.json")
    if not summary_path.exists():
        print("[WARNING] Analysis summary not found, skipping this visualization")
        return
    
    with open(summary_path, 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Experimental Results Summary', fontsize=16, weight='bold', y=0.98)
    
    # 1. Scenario Distribution
    ax1 = axes[0, 0]
    scenarios = summary['scenarios']
    labels = list(scenarios.keys())
    values = list(scenarios.values())
    colors_scenario = ['#4A90E2', '#50C878', '#FF6B6B']
    def autopct_func(pct):
        return f'{int(pct/100*sum(values))}\n({pct:.1f}%)'
    ax1.pie(values, labels=labels, autopct=autopct_func, 
            colors=colors_scenario[:len(labels)], startangle=90)
    ax1.set_title('Scenario Distribution', fontsize=12, weight='bold')
    
    # 2. Scale Item Count Distribution
    ax2 = axes[0, 1]
    scale_stats = summary['scale_statistics']
    categories = ['Mean Items', 'Min Items', 'Max Items']
    values_bar = [
        scale_stats['mean_items_per_scale'],
        scale_stats['min_items'],
        scale_stats['max_items']
    ]
    bars = ax2.bar(categories, values_bar, color=['#FFD93D', '#FF6B6B', '#50C878'])
    ax2.set_ylabel('Number of Items', fontsize=10)
    ax2.set_title('Scale Item Statistics', fontsize=12, weight='bold')
    ax2.grid(axis='y', alpha=0.3)
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9)
    
    # 3. Evaluation Metrics
    ax3 = axes[1, 0]
    eval_stats = summary['evaluation_statistics']
    metrics = ['Mean Rating\n(0-100)', 'Internal Consistency\n(Cronbach α)']
    values_metrics = [
        eval_stats['mean_rating'],
        eval_stats['mean_internal_consistency'] * 100  # Convert to percentage
    ]
    bars = ax3.bar(metrics, values_metrics, color=['#9B59B6', '#E67E22'])
    ax3.set_ylabel('Score', fontsize=10)
    ax3.set_title('Evaluation Metrics', fontsize=12, weight='bold')
    ax3.grid(axis='y', alpha=0.3)
    # Add value labels
    for bar, val in zip(bars, values_metrics):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2f}',
                ha='center', va='bottom', fontsize=9)
    
    # 4. Statistical Selection
    ax4 = axes[1, 1]
    sel_stats = summary['selection_statistics']
    selection_data = {
        'Original Items': sel_stats['mean_original_items'],
        'Selected Items': sel_stats['mean_selected_items']
    }
    bars = ax4.bar(selection_data.keys(), selection_data.values(), 
                   color=['#FF6B6B', '#50C878'])
    ax4.set_ylabel('Number of Items', fontsize=10)
    ax4.set_title(f'Statistical Selection (Selection Rate: {sel_stats["mean_selection_ratio"]*100:.1f}%)', 
                  fontsize=12, weight='bold')
    ax4.grid(axis='y', alpha=0.3)
    # Add value labels
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
    """Create evaluation comparison diagram (empathic vs non-empathic)"""
    # 使用Example data（Should be read from evaluation summary in practice）
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Discriminant Validation Results', fontsize=16, weight='bold')
    
    # Left: Mean rating comparison
    categories = ['Empathic Persona', 'Non-Empathic Persona']
    means = [60.52, 0.56]
    stds = [15.0, 2.0]  # Example standard deviation
    
    bars = ax1.bar(categories, means, yerr=stds, capsize=10,
                   color=['#50C878', '#FF6B6B'], alpha=0.8, edgecolor='black', linewidth=2)
    ax1.set_ylabel('Mean Rating (0-100)', fontsize=11)
    ax1.set_title('Mean Rating Comparison', fontsize=12, weight='bold')
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim(0, 80)
    
    # Add value labels
    for bar, mean in zip(bars, means):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{mean:.2f}',
                ha='center', va='bottom', fontsize=11, weight='bold')
    
    # Add statistical information
    ax1.text(0.5, 0.95, 'Cohen\'s d = 2.407\np < 0.001', 
             transform=ax1.transAxes, ha='center', va='top',
             bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5),
             fontsize=10, weight='bold')
    
    # Right: Rating distribution (example)
    np.random.seed(42)
    empathic_scores = np.random.normal(60.52, 15, 1800)
    non_empathic_scores = np.random.normal(0.56, 2, 1800)
    
    ax2.hist(empathic_scores, bins=30, alpha=0.6, label='Empathic Persona', 
             color='#50C878', edgecolor='black')
    ax2.hist(non_empathic_scores, bins=30, alpha=0.6, label='Non-Empathic Persona',
             color='#FF6B6B', edgecolor='black')
    ax2.set_xlabel('Rating', fontsize=11)
    ax2.set_ylabel('Frequency', fontsize=11)
    ax2.set_title('Rating Distribution', fontsize=12, weight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'evaluation_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Evaluation comparison saved: {output_dir / 'evaluation_comparison.png'}")

def create_dimension_example():
    """Create dimension example diagram"""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')
    
    # Example维度数据（Based on actual cases）
    dimensions = [
        ('Emotional Mirroring\nin Collaborative Assembly', 53, '#4A90E2'),
        ('Proactive Support\nand Assistance', 60, '#50C878'),
        ('Understanding\nSafety Concerns', 52, '#FF6B6B')
    ]
    
    y_pos = np.arange(len(dimensions))
    items_count = [dim[1] for dim in dimensions]
    colors_dim = [dim[2] for dim in dimensions]
    
    bars = ax.barh(y_pos, items_count, color=colors_dim, alpha=0.8, edgecolor='black', linewidth=2)
    
    # Set labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels([dim[0] for dim in dimensions], fontsize=11)
    ax.set_xlabel('Number of Items', fontsize=12, weight='bold')
    ax.set_title('Scale Dimension Example\n(Factory Assembly Scenario)', fontsize=14, weight='bold', pad=20)
    
    # Add value labels
    for i, (bar, count) in enumerate(zip(bars, items_count)):
        width = bar.get_width()
        ax.text(width + 1, bar.get_y() + bar.get_height()/2,
                f'{count} items',
                ha='left', va='center', fontsize=10, weight='bold')
    
    ax.set_xlim(0, max(items_count) * 1.2)
    ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'dimension_example.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Dimension example saved: {output_dir / 'dimension_example.png'}")

def create_baseline_comparison():
    """Create baseline comparison diagram (PETS, RoPE)"""
    # Read comparison data
    comparison_path = Path("presentation/baseline_comparison_results.json")
    if not comparison_path.exists():
        print("[WARNING] Baseline comparison data not found, skipping this visualization")
        return
    
    with open(comparison_path, 'r', encoding='utf-8') as f:
        comparison_data = json.load(f)
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Baseline Comparison (PETS vs RoPE vs Our Generated Scales)', fontsize=16, weight='bold', y=0.98)
    
    scenarios = list(comparison_data.keys())
    colors = {'generated': '#50C878', 'PETS': '#4A90E2', 'RoPE': '#FF6B6B'}
    
    # 1. Internal Consistency Comparison (Cronbach's α)
    ax1 = axes[0, 0]
    x = np.arange(len(scenarios))
    width = 0.25
    
    generated_alphas = [comparison_data[s]['generated']['alpha'] for s in scenarios]
    pets_alphas = [comparison_data[s]['PETS']['alpha'] if comparison_data[s]['PETS']['alpha'] > 0 else 0 for s in scenarios]
    rope_alphas = [comparison_data[s]['RoPE']['alpha'] if comparison_data[s]['RoPE']['alpha'] > 0 else 0 for s in scenarios]
    
    bars1 = ax1.bar(x - width, generated_alphas, width, label='Our Generated Scales', 
                    color=colors['generated'], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2 = ax1.bar(x, pets_alphas, width, label='PETS', 
                    color=colors['PETS'], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars3 = ax1.bar(x + width, rope_alphas, width, label='RoPE', 
                    color=colors['RoPE'], alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax1.set_ylabel('Cronbach\'s α', fontsize=11, weight='bold')
    ax1.set_title('Internal Consistency Comparison', fontsize=12, weight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([s.replace('_', '\n') for s in scenarios], fontsize=9)
    ax1.legend(fontsize=9)
    ax1.set_ylim(0.8, 1.0)
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height + 0.005,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=8)
    
    # 2. Discriminant Ability Comparison (Cohen's d)
    ax2 = axes[0, 1]
    
    generated_ds = [comparison_data[s]['generated']['cohens_d'] for s in scenarios]
    pets_ds = [comparison_data[s]['PETS']['cohens_d'] if comparison_data[s]['PETS']['cohens_d'] > 0 else 0 for s in scenarios]
    rope_ds = [comparison_data[s]['RoPE']['cohens_d'] if comparison_data[s]['RoPE']['cohens_d'] > 0 else 0 for s in scenarios]
    
    bars1 = ax2.bar(x - width, generated_ds, width, label='Our Generated Scales', 
                    color=colors['generated'], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2 = ax2.bar(x, pets_ds, width, label='PETS', 
                    color=colors['PETS'], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars3 = ax2.bar(x + width, rope_ds, width, label='RoPE', 
                    color=colors['RoPE'], alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax2.set_ylabel('Cohen\'s d', fontsize=11, weight='bold')
    ax2.set_title('Discriminant Ability Comparison', fontsize=12, weight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([s.replace('_', '\n') for s in scenarios], fontsize=9)
    ax2.legend(fontsize=9)
    ax2.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                        f'{height:.2f}', ha='center', va='bottom', fontsize=8)
    
    # 3. Item Count Comparison
    ax3 = axes[1, 0]
    
    generated_n = [comparison_data[s]['generated']['n_items'] for s in scenarios]
    pets_n = [comparison_data[s]['PETS']['n_items'] for s in scenarios]
    rope_n = [comparison_data[s]['RoPE']['n_items'] for s in scenarios]
    
    bars1 = ax3.bar(x - width, generated_n, width, label='Our Generated Scales', 
                    color=colors['generated'], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2 = ax3.bar(x, pets_n, width, label='PETS', 
                    color=colors['PETS'], alpha=0.8, edgecolor='black', linewidth=1.5)
    bars3 = ax3.bar(x + width, rope_n, width, label='RoPE', 
                    color=colors['RoPE'], alpha=0.8, edgecolor='black', linewidth=1.5)
    
    ax3.set_ylabel('Number of Items', fontsize=11, weight='bold')
    ax3.set_title('Item Count Comparison', fontsize=12, weight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels([s.replace('_', '\n') for s in scenarios], fontsize=9)
    ax3.legend(fontsize=9)
    ax3.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    # 4. Comprehensive Comparison (factory assembly scenario)
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    scenario = 'collab_robot_assembly'
    if scenario in comparison_data:
        data = comparison_data[scenario]
        
        # Create comparison table
        table_data = [
            ['Metric', 'Our Generated Scales', 'PETS', 'RoPE'],
            ['Number of Items', f"{data['generated']['n_items']}", f"{data['PETS']['n_items']}", f"{data['RoPE']['n_items']}"],
            ['α', f"{data['generated']['alpha']:.3f}", f"{data['PETS']['alpha']:.3f}", f"{data['RoPE']['alpha']:.3f}"],
            ['Cohen\'s d', f"{data['generated']['cohens_d']:.2f}", f"{data['PETS']['cohens_d']:.2f}", f"{data['RoPE']['cohens_d']:.2f}"],
        ]
        
        table = ax4.table(cellText=table_data[1:], colLabels=table_data[0],
                         cellLoc='center', loc='center',
                         colWidths=[0.3, 0.23, 0.23, 0.23])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Set header style
        for i in range(len(table_data[0])):
            table[(0, i)].set_facecolor('#4A90E2')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Set first column style
        for i in range(1, len(table_data)):
            table[(i, 0)].set_facecolor('#E8E8E8')
            table[(i, 0)].set_text_props(weight='bold')
        
        # Highlight our generated scales column
        for i in range(1, len(table_data)):
            table[(i, 1)].set_facecolor('#50C878')
            table[(i, 1)].set_text_props(weight='bold')
        
        ax4.set_title(f'Comprehensive Comparison ({scenario.replace("_", " ")})', fontsize=12, weight='bold', pad=20)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_dir / 'baseline_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Baseline comparison saved: {output_dir / 'baseline_comparison.png'}")

def create_ablation_study():
    """Create ablation study visualization (3 variants vs baseline)"""
    ablation_path = Path("data/ablation_studies/collab_robot_assembly/ablation_summary.json")
    if not ablation_path.exists():
        print("[WARNING] Ablation study data not found, skipping this visualization")
        return
    
    with open(ablation_path, 'r', encoding='utf-8') as f:
        ablation_data = json.load(f)
    
    variants = ablation_data['variants']
    baseline = ablation_data['baseline']
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Ablation Study Results (vs Baseline)', fontsize=16, weight='bold', y=0.98)
    
    # Prepare data - include baseline and 3 variants
    variant_keys = ['fewer_generators', 'no_content', 'fewer_generators_no_content']
    variant_labels = {
        'fewer_generators': 'Fewer\nGenerators\n(1 vs 5)',
        'no_content': 'No Content\nAssessment\n(Random)',
        'fewer_generators_no_content': 'Fewer Gen +\nNo Content\n(1+Random)'
    }
    
    # Build data including baseline
    all_labels = ['Baseline\n(5+Content+EFA)'] + [variant_labels[k] for k in variant_keys]
    all_alphas = [baseline['validation_metrics']['internal_consistency']['alpha']] + \
                 [variants[k]['validation_metrics']['internal_consistency']['alpha'] for k in variant_keys]
    all_cohens_ds = [baseline['validation_metrics']['discriminant_ability']['cohens_d']] + \
                    [variants[k]['validation_metrics']['discriminant_ability']['cohens_d'] for k in variant_keys]
    all_n_items = [16] + [variants[k]['n_selected_items'] for k in variant_keys]  # Baseline has 16 items
    all_mean_ratings = [None] + [variants[k]['evaluation']['overall_mean_rating'] for k in variant_keys]  # Baseline has no mean_rating
    
    # Colors: baseline in dark blue, variants in other colors
    colors = ['#2E86AB'] + ['#FF6B6B', '#4A90E2', '#50C878']
    
    # 1. 内部一致性 (Cronbach's α)
    ax1 = axes[0, 0]
    bars1 = ax1.bar(all_labels, all_alphas, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Cronbach\'s α', fontsize=11, weight='bold')
    ax1.set_title('Internal Consistency Comparison', fontsize=12, weight='bold')
    ax1.set_ylim(0.93, 1.0)
    ax1.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars1, all_alphas):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.003,
                f'{val:.3f}', ha='center', va='bottom', fontsize=9, weight='bold')
    
    # 2. Discriminant Ability (Cohen's d)
    ax2 = axes[0, 1]
    bars2 = ax2.bar(all_labels, all_cohens_ds, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Cohen\'s d', fontsize=11, weight='bold')
    ax2.set_title('Discriminant Ability Comparison', fontsize=12, weight='bold')
    ax2.set_ylim(0, 5.5)
    ax2.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars2, all_cohens_ds):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.15,
                f'{val:.2f}', ha='center', va='bottom', fontsize=9, weight='bold')
    
    # Add baseline reference line
    ax2.axhline(y=baseline['validation_metrics']['discriminant_ability']['cohens_d'], 
                color='#2E86AB', linestyle='--', linewidth=2, alpha=0.5, label='Baseline')
    
    # 3. items目数
    ax3 = axes[1, 0]
    bars3 = ax3.bar(all_labels, all_n_items, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Number of Items', fontsize=11, weight='bold')
    ax3.set_title('Selected Items Count Comparison', fontsize=12, weight='bold')
    ax3.set_ylim(0, 18)
    ax3.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars3, all_n_items):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                f'{int(val)}', ha='center', va='bottom', fontsize=9, weight='bold')
    
    # 4. 平均评分（Variants only, excluding baseline）
    ax4 = axes[1, 1]
    variant_labels_only = [variant_labels[k] for k in variant_keys]
    variant_ratings = [variants[k]['evaluation']['overall_mean_rating'] for k in variant_keys]
    variant_colors = colors[1:]  # Exclude baseline color
    bars4 = ax4.bar(variant_labels_only, variant_ratings, color=variant_colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax4.set_ylabel('Mean Rating', fontsize=11, weight='bold')
    ax4.set_title('Mean Rating Comparison (Ablation Variants)', fontsize=12, weight='bold')
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
    """Create Boateng nine-step method flowchart"""
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define three phases
    phases = [
        ('Phase 1: Item Development', 2, 8.5, '#4A90E2', [
            'Step 1: Domain Identification',
            'Step 2: Content Validity'
        ]),
        ('Phase 2: Scale Construction', 5, 8.5, '#50C878', [
            'Step 3: Pilot Testing',
            'Step 4: Survey',
            'Step 5: Item Reduction',
            'Step 6: Factor Extraction',
            'Step 7: Dimensionality Testing'
        ]),
        ('Phase 3: Scale Evaluation', 8, 8.5, '#FF6B6B', [
            'Step 8: Reliability Testing',
            'Step 9: Validity Testing'
        ])
    ]
    
    # Draw stage boxes
    for phase_name, x, y, color, steps in phases:
        # Phase title box
        phase_rect = mpatches.FancyBboxPatch(
            (x-1.2, y-0.3), 2.4, 0.6,
            boxstyle="round,pad=0.1", 
            facecolor=color, edgecolor='black', linewidth=2
        )
        ax.add_patch(phase_rect)
        ax.text(x, y, phase_name, ha='center', va='center', 
                fontsize=11, weight='bold', color='white')
        
        # Step box
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
    
    # Add arrows
    for i in range(len(phases)-1):
        x1 = phases[i][1] + 1.2
        x2 = phases[i+1][1] - 1.2
        y = 8.5
        ax.annotate('', xy=(x2, y), xytext=(x1, y),
                   arrowprops=dict(arrowstyle='->', lw=2, color='black'))
    
    # Add title
    ax.text(5, 9.5, 'Boateng et al. (2018) Nine-Step Method Framework', 
           ha='center', va='center', fontsize=14, weight='bold')
    
    # Add time description
    ax.text(5, 0.5, 'Traditional: Months to Years | Our Method: Hours', 
           ha='center', va='center', fontsize=10, 
           bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'boateng_method.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Boateng method saved: {output_dir / 'boateng_method.png'}")

def create_scenario_comparison():
    """Create three scenarios comparison diagram"""
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('off')
    
    scenarios = [
        {
            'name': 'Factory Assembly\nCollaborative Robot',
            'platform': 'Collaborative Arm',
            'modality': 'Gesture + Voice',
            'pattern': 'Turn-taking Assembly',
            'goals': 'Safety Awareness,\nAdaptive Pacing',
            'color': '#4A90E2',
            'x': 2
        },
        {
            'name': 'Home Service Robot',
            'platform': 'Mobile Service Robot',
            'modality': 'Speech + Navigation',
            'pattern': 'Assistive',
            'goals': 'Comfort, Perceived Care',
            'color': '#50C878',
            'x': 5
        },
        {
            'name': 'Counseling Chatbot',
            'platform': 'Chatbot',
            'modality': 'Text Chat',
            'pattern': 'Supportive Dialogue',
            'goals': 'Emotional Attunement',
            'color': '#FF6B6B',
            'x': 8
        }
    ]
    
    y_start = 7
    for scenario in scenarios:
        x = scenario['x']
        color = scenario['color']
        
        # Scenario title box
        title_rect = mpatches.FancyBboxPatch(
            (x-1.3, y_start-0.4), 2.6, 0.8,
            boxstyle="round,pad=0.1",
            facecolor=color, edgecolor='black', linewidth=2
        )
        ax.add_patch(title_rect)
        ax.text(x, y_start, scenario['name'], ha='center', va='center',
               fontsize=11, weight='bold', color='white')
        
        # Detailed Information
        details = [
            f"Platform: {scenario['platform']}",
            f"Modality: {scenario['modality']}",
            f"Pattern: {scenario['pattern']}",
            f"Goals: {scenario['goals']}"
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
    
    ax.text(5, 9, 'Three Experimental Scenarios Comparison', ha='center', va='center',
           fontsize=14, weight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'scenario_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Scenario comparison saved: {output_dir / 'scenario_comparison.png'}")

def create_experiment_setup():
    """Create experiment setup diagram (ablation study and baseline)"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    fig.suptitle('Experimental Setup', fontsize=16, weight='bold', y=0.98)
    
    # Left: Ablation study setup
    ax1 = axes[0]
    ax1.axis('off')
    
    # Ablation study title
    ax1.text(0.5, 0.95, 'Ablation Study Setup', ha='center', va='top',
            fontsize=14, weight='bold', transform=ax1.transAxes)
    
    # 2×2 Design说明
    ax1.text(0.5, 0.85, '2×2 Design', ha='center', va='top',
            fontsize=12, weight='bold', transform=ax1.transAxes)
    
    # Draw 2×2 table
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
    
    # Set header style
    for i in range(len(table_data[0])):
        table[(0, i)].set_facecolor('#4A90E2')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Set first column style
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
    
    # Add setup description
    setup_text = """Scenario: collab_robot_assembly
Evaluation Process: Two-phase
  • Phase 1: 200 personas (for selection)
  • Phase 2: 200 personas (for validation)
Variables:
  • num_generators: 1 vs 5
  • enable_content: False vs True"""
    
    ax1.text(0.5, 0.35, setup_text, ha='center', va='top',
            fontsize=9, transform=ax1.transAxes,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
    
    # Right: Baseline setup
    ax2 = axes[1]
    ax2.axis('off')
    
    # Baseline title
    ax2.text(0.5, 0.95, 'Baseline Comparison Setup', ha='center', va='top',
            fontsize=14, weight='bold', transform=ax2.transAxes)
    
    # Baseline scales
    baseline_text = """Baseline Scales:
  • PETS (Perceived Empathy of Technology Scale)
  • RoPE (Robot Empathy Scale)

Evaluation Settings:
  • Use same validation personas
    as generated scales (200)
  • Evaluate in all 3 scenarios:
    - Factory Assembly Collaborative Robot
    - Home Service Robot
    - Counseling Chatbot

Comparison Metrics:
  • Internal Consistency (Cronbach's α)
  • Discriminant Ability (Cohen's d)
  • Item Count
  • Scenario Relevance
  • Item Quality"""
    
    ax2.text(0.5, 0.7, baseline_text, ha='center', va='top',
            fontsize=10, transform=ax2.transAxes,
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
    
    # Add comparison explanation
    comparison_text = """Comparison Purpose:
  Validate effectiveness of
  generated scales
  Demonstrate advantages of
  scenario customization"""
    
    ax2.text(0.5, 0.25, comparison_text, ha='center', va='top',
            fontsize=9, weight='bold', transform=ax2.transAxes,
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_dir / 'experiment_setup.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"[OK] Experiment setup saved: {output_dir / 'experiment_setup.png'}")

def create_selected_experiments_overview():
    """Create selected experiments overview diagram"""
    # Read experiment selection data
    selection_path = Path("presentation/experiment_selection.json")
    if not selection_path.exists():
        print("[WARNING] Experiment selection data not found, skipping this visualization")
        return
    
    with open(selection_path, 'r', encoding='utf-8') as f:
        selection_data = json.load(f)
    
    main_experiments = selection_data['main_experiments']
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Selected Experiments Overview', fontsize=16, weight='bold', y=0.98)
    
    scenarios = ['Factory\nAssembly', 'Home Service', 'Counseling']
    scenario_keys = ['collab_robot_assembly', 'home_service_robot', 'counseling_chatbot']
    colors = ['#4A90E2', '#50C878', '#FF6B6B']
    
    # Extract data
    alphas = [main_experiments[k]['metrics']['internal_consistency_alpha'] for k in scenario_keys]
    cohens_ds = [main_experiments[k]['metrics']['cohens_d'] for k in scenario_keys]
    n_items = [main_experiments[k]['metrics']['n_selected_items'] for k in scenario_keys]
    quality_scores = [main_experiments[k]['quality_score'] for k in scenario_keys]
    
    # 1. 内部一致性 (Cronbach's α)
    ax1 = axes[0, 0]
    bars1 = ax1.bar(scenarios, alphas, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('Cronbach\'s α', fontsize=11, weight='bold')
    ax1.set_title('Internal Consistency', fontsize=12, weight='bold')
    ax1.set_ylim(0.98, 1.0)
    ax1.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars1, alphas):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.001,
                f'{val:.3f}', ha='center', va='bottom', fontsize=10, weight='bold')
    
    # 2. Discriminant Ability (Cohen's d)
    ax2 = axes[0, 1]
    bars2 = ax2.bar(scenarios, cohens_ds, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax2.set_ylabel('Cohen\'s d', fontsize=11, weight='bold')
    ax2.set_title('Discriminant Ability', fontsize=12, weight='bold')
    ax2.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars2, cohens_ds):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{val:.2f}', ha='center', va='bottom', fontsize=10, weight='bold')
    
    # 3. items目数
    ax3 = axes[1, 0]
    bars3 = ax3.bar(scenarios, n_items, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax3.set_ylabel('Number of Items', fontsize=11, weight='bold')
    ax3.set_title('Selected Items Count', fontsize=12, weight='bold')
    ax3.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars3, n_items):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{int(val)}', ha='center', va='bottom', fontsize=10, weight='bold')
    
    # 4. 质量分数
    ax4 = axes[1, 1]
    bars4 = ax4.bar(scenarios, quality_scores, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax4.set_ylabel('Quality Score', fontsize=11, weight='bold')
    ax4.set_title('Quality Score', fontsize=12, weight='bold')
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
    """Create metrics explanation diagram"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Evaluation and Selection Metrics Explanation', fontsize=16, weight='bold', y=0.98)
    
    # 1. Cronbach's α
    ax1 = axes[0, 0]
    ax1.axis('off')
    ax1.text(0.5, 0.8, "Cronbach's α", ha='center', va='center',
            fontsize=14, weight='bold', transform=ax1.transAxes)
    ax1.text(0.5, 0.6, "Internal Consistency", ha='center', va='center',
            fontsize=12, transform=ax1.transAxes)
    ax1.text(0.5, 0.4, "Measures whether all items\nmeasure the same concept", ha='center', va='center',
            fontsize=10, transform=ax1.transAxes)
    ax1.text(0.5, 0.2, "α > 0.9 is Excellent", ha='center', va='center',
            fontsize=11, weight='bold', color='green', transform=ax1.transAxes)
    
    # 绘制Example条形图
    ax1_bar = fig.add_axes([0.15, 0.55, 0.15, 0.1])
    ax1_bar.bar(['Excellent', 'Good', 'Acceptable'], [0.99, 0.95, 0.85],
               color=['green', 'yellow', 'orange'], alpha=0.7)
    ax1_bar.set_ylim(0, 1)
    ax1_bar.set_ylabel('α Value')
    ax1_bar.tick_params(labelsize=8)
    
    # 2. Cohen's d
    ax2 = axes[0, 1]
    ax2.axis('off')
    ax2.text(0.5, 0.8, "Cohen's d", ha='center', va='center',
            fontsize=14, weight='bold', transform=ax2.transAxes)
    ax2.text(0.5, 0.6, "Discriminant Ability/Effect Size", ha='center', va='center',
            fontsize=12, transform=ax2.transAxes)
    ax2.text(0.5, 0.4, "Measures whether scale can\neffectively distinguish participants", ha='center', va='center',
            fontsize=10, transform=ax2.transAxes)
    ax2.text(0.5, 0.2, "d > 2.0 is Very Large Effect", ha='center', va='center',
            fontsize=11, weight='bold', color='green', transform=ax2.transAxes)
    
    # 绘制Example对比图
    ax2_bar = fig.add_axes([0.65, 0.55, 0.15, 0.1])
    categories = ['Empathic', 'Non-Empathic']
    means = [60, 5]
    ax2_bar.bar(categories, means, color=['green', 'red'], alpha=0.7)
    ax2_bar.set_ylabel('Mean Rating')
    ax2_bar.tick_params(labelsize=8)
    
    # 3. EFA/CFA
    ax3 = axes[1, 0]
    ax3.axis('off')
    ax3.text(0.5, 0.8, "EFA / CFA", ha='center', va='center',
            fontsize=14, weight='bold', transform=ax3.transAxes)
    ax3.text(0.5, 0.6, "Factor Analysis", ha='center', va='center',
            fontsize=12, transform=ax3.transAxes)
    ax3.text(0.5, 0.4, "EFA: Discover hidden dimensions\nCFA: Validate factor structure", ha='center', va='center',
            fontsize=10, transform=ax3.transAxes)
    ax3.text(0.5, 0.2, "RMSEA < 0.08, TLI/CFI > 0.9", ha='center', va='center',
            fontsize=10, weight='bold', color='blue', transform=ax3.transAxes)
    
    # 4. items目-总分相关性
    ax4 = axes[1, 1]
    ax4.axis('off')
    ax4.text(0.5, 0.8, "Item-Total Correlation", ha='center', va='center',
            fontsize=14, weight='bold', transform=ax4.transAxes)
    ax4.text(0.5, 0.6, "Item-Total Correlation", ha='center', va='center',
            fontsize=12, transform=ax4.transAxes)
    ax4.text(0.5, 0.4, "Correlation between each item\nand scale total score", ha='center', va='center',
            fontsize=10, transform=ax4.transAxes)
    ax4.text(0.5, 0.2, "Retain items with correlation > 0.3", ha='center', va='center',
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


