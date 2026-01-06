import matplotlib.pyplot as plt
import numpy as np

# Data Preparation
scenarios = ['Factory Assembly\n(Collaborative)', 'Home Service\n(Assistive)', 'Counseling\n(Supportive)']
x = np.arange(len(scenarios))
width = 0.25  # Width of the bars

# Dataset 1: Internal Consistency (Cronbach's Alpha)
# Data source: baseline_comparison.jpg & selected_experiments_overview.jpg
alpha_ours = [0.992, 0.993, 0.999]
alpha_pets = [0.953, 0.955, 0.956]
alpha_rope = [0.859, 0.855, 0.884]

# Dataset 2: Discriminant Ability (Cohen's d)
# Data source: baseline_comparison.jpg & selected_experiments_overview.jpg
d_ours = [4.63, 5.24, 15.47]
d_pets = [1.95, 2.00, 2.33]
d_rope = [1.07, 1.00, 1.14]

# Setup Plot (2 Rows, 1 Column)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), dpi=300)
fig.suptitle('Performance Benchmark: Ours vs. Baselines (PETS, RoPE)', fontsize=20, fontweight='bold', y=0.96)

# --- Plot 1: Internal Consistency ---
rects1_alpha = ax1.bar(x - width, alpha_ours, width, label='Ours (Context-Aware)', color='#66c2a5', edgecolor='black', linewidth=1)
rects2_alpha = ax1.bar(x, alpha_pets, width, label='PETS (Standard)', color='#8da0cb', edgecolor='black', linewidth=1)
rects3_alpha = ax1.bar(x + width, alpha_rope, width, label='RoPE (Standard)', color='#fc8d62', edgecolor='black', linewidth=1)

# Formatting Ax1
ax1.set_ylabel('Internal Consistency\n(Cronbach\'s α)', fontsize=14, fontweight='bold')
ax1.set_ylim(0.7, 1.05) # Zoom in to show differences
ax1.set_xticks(x)
ax1.set_xticklabels(scenarios, fontsize=12)
ax1.legend(loc='upper left', fontsize=12, frameon=True, fancybox=True, framealpha=0.9)
ax1.grid(axis='y', linestyle='--', alpha=0.5)
ax1.set_title('Metric 1: Reliability (Higher is Better)', fontsize=16, pad=10, loc='left')

# Add Labels for Alpha
def autolabel(rects, ax):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.3f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=11, fontweight='bold')

autolabel(rects1_alpha, ax1)
autolabel(rects2_alpha, ax1)
autolabel(rects3_alpha, ax1)


# --- Plot 2: Discriminant Ability ---
rects1_d = ax2.bar(x - width, d_ours, width, label='Ours (Context-Aware)', color='#66c2a5', edgecolor='black', linewidth=1)
rects2_d = ax2.bar(x, d_pets, width, label='PETS (Standard)', color='#8da0cb', edgecolor='black', linewidth=1)
rects3_d = ax2.bar(x + width, d_rope, width, label='RoPE (Standard)', color='#fc8d62', edgecolor='black', linewidth=1)

# Formatting Ax2
ax2.set_ylabel('Discriminant Ability\n(Cohen\'s d)', fontsize=14, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(scenarios, fontsize=12)
# ax2.legend() # Legend already in top plot
ax2.grid(axis='y', linestyle='--', alpha=0.5)
ax2.set_title('Metric 2: Sensitivity (Higher is Better)', fontsize=16, pad=10, loc='left')

# Add Labels for Cohen's d
autolabel(rects1_d, ax2)
autolabel(rects2_d, ax2)
autolabel(rects3_d, ax2)

# Adjust layout
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.subplots_adjust(hspace=0.3)

# Save/Show
plt.savefig('merged_performance_chart_hd.png')
plt.show()