# 1. 导入库
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 2. 定义常量（包括 NUM_SIMULATIONS）
DAYS = 4
MAX_HOURS_PER_DAY = 8
TOTAL_MAX_HOURS = DAYS * MAX_HOURS_PER_DAY
AVG_EVENTS_PER_DAY = 1.2
MEAN_IMPACT_HOURS = 1.5
NUM_SIMULATIONS = 100_000       # ← 这里定义

# 3. 定义函数（simulate_one_run）
np.random.seed(42)

def simulate_one_run():         # ← 函数定义
    total_impact = 0.0
    for _ in range(DAYS):
        n = np.random.poisson(AVG_EVENTS_PER_DAY)
        for _ in range(n):
            impact = np.random.exponential(MEAN_IMPACT_HOURS)
            total_impact += impact
    ratio = total_impact / TOTAL_MAX_HOURS
    return min(ratio, 1.0)

# 4. 执行模拟（此时可以引用 NUM_SIMULATIONS 和 simulate_one_run）
ratios = np.array([simulate_one_run() for _ in range(NUM_SIMULATIONS)])

# ==================== 剔除与分级 ====================
exclude_low, exclude_high = 0.10, 0.90
filtered = ratios[(ratios >= exclude_low) & (ratios < exclude_high)]

quantiles = np.linspace(0, 1, 6)
boundaries = np.quantile(filtered, quantiles)
level_bounds = [exclude_low] + list(boundaries[1:-1]) + [boundaries[-1]]

level_probs = []
for i in range(len(level_bounds)-1):
    low, high = level_bounds[i], level_bounds[i+1]
    prob = np.sum((filtered >= low) & (filtered < high)) / len(filtered)
    level_probs.append(prob)

prob_low = np.sum(ratios < exclude_low) / NUM_SIMULATIONS
prob_high = np.sum(ratios >= exclude_high) / NUM_SIMULATIONS

# ==================== KDE 数据 ====================
try:
    from scipy.stats import gaussian_kde
    kde = gaussian_kde(filtered)
    x_kde = np.linspace(exclude_low, filtered.max(), 300)
    y_kde = kde(x_kde)
    use_kde = True
except ImportError:
    use_kde = False
    print("未安装 scipy，将使用直方图代替 KDE。")

# ==================== CDF 降采样 ====================
sorted_ratios = np.sort(ratios)
sample_idx = np.linspace(0, len(sorted_ratios)-1, 1000, dtype=int)
cdf_x = sorted_ratios[sample_idx]
cdf_y = (sample_idx + 1) / len(sorted_ratios)   # 精确对应

# ==================== 小提琴图降采样 ====================
np.random.seed(42)  # 确保采样可复现
# 原 3000 → 改为 1000
sample_all = np.random.choice(ratios, size=1000, replace=False)
sample_filt = np.random.choice(filtered, size=1000, replace=False)

# ==================== 绘图部分 ====================
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "概率密度分布 (剔除区 & 等概率分级)",
        "累积分布函数 (CDF)",
        "剔除极端值后的等频分级",
        "分布对比 (全数据 vs 剔除后)"
    ),
    vertical_spacing=0.12,
    horizontal_spacing=0.10,
)

# 子图1：KDE / 直方图（不变）
if use_kde:
    fig.add_trace(go.Scatter(x=x_kde, y=y_kde, mode='lines', fill='tozeroy',
                             name='KDE 密度', line=dict(color='steelblue', width=2)), row=1, col=1)
else:
    fig.add_trace(go.Histogram(x=filtered, histnorm='probability density',
                               nbinsx=100, marker_color='steelblue', opacity=0.5,
                               name='密度直方图'), row=1, col=1)

fig.add_vrect(x0=0, x1=exclude_low, fillcolor="gray", opacity=0.15, layer="below", line_width=0, row=1, col=1)
fig.add_vrect(x0=exclude_high, x1=1.0, fillcolor="gray", opacity=0.15, layer="below", line_width=0, row=1, col=1)
for i, b in enumerate(level_bounds[1:-1], 1):
    fig.add_vline(x=b, line_dash="dash", line_color="darkorange", opacity=0.8, row=1, col=1)
    fig.add_annotation(x=b, y=0.95, yref="y domain", text=f"Q{i}", showarrow=False,
                       font=dict(color="darkorange", size=10), row=1, col=1)

fig.update_xaxes(tickformat=".0%", title_text="影响占比", row=1, col=1)
fig.update_yaxes(title_text="概率密度", row=1, col=1)

# 子图2：CDF（使用降采样数据）
fig.add_trace(go.Scatter(x=cdf_x, y=cdf_y, mode='lines',
                         line=dict(color='steelblue', width=2), name='CDF'), row=1, col=2)
fig.add_hline(y=0.5, line_dash="dot", line_color="gray", opacity=0.6, row=1, col=2)
fig.add_hline(y=0.9, line_dash="dot", line_color="gray", opacity=0.6, row=1, col=2)
fig.add_vline(x=exclude_low, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=2)
fig.add_vline(x=exclude_high, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=2)

fig.update_xaxes(tickformat=".0%", title_text="影响占比", row=1, col=2)
fig.update_yaxes(tickformat=".0%", title_text="累积概率", range=[0, 1.05], row=1, col=2)

# 子图3：分级条形图（不变）
widths = [level_bounds[i+1] - level_bounds[i] for i in range(len(level_bounds)-1)]
lefts = level_bounds[:-1]
labels = [f"Q{i+1} ({lefts[i]:.1%}–{lefts[i]+widths[i]:.1%})" for i in range(len(widths))]

fig.add_trace(go.Bar(y=labels, x=widths, base=lefts, orientation='h',
                     marker=dict(color=level_probs, colorscale='Viridis', showscale=False),
                     text=[f"{p:.0%}" for p in level_probs], textposition='inside',
                     insidetextanchor='middle', textfont=dict(color='white', size=12),
                     name='等级概率'), row=2, col=1)
fig.update_xaxes(tickformat=".0%", title_text="影响占比区间", range=[0.05, 1.0], row=2, col=1)
fig.update_yaxes(title_text="", row=2, col=1)

# 子图4：小提琴图（使用降采样数据）
fig.add_trace(go.Violin(x=['全部模拟']*len(sample_all), y=sample_all,
                        name='全部模拟', box_visible=True, meanline_visible=True,
                        line_color='steelblue', fillcolor='lightsteelblue', opacity=0.6,
                        points=False), row=2, col=2)
fig.add_trace(go.Violin(x=['剔除后']*len(sample_filt), y=sample_filt,
                        name='剔除极端值后', box_visible=True, meanline_visible=True,
                        line_color='salmon', fillcolor='salmon', opacity=0.6,
                        points=False), row=2, col=2)
fig.update_yaxes(tickformat=".0%", title_text="影响占比", row=2, col=2)

# 全局布局
fig.update_layout(
    title_text="未来四天突发事件影响占比模拟分析（固定种子 = 42）",
    font=dict(family="Microsoft YaHei, SimHei, sans-serif", size=12),
    showlegend=False,
    width=1200,
    height=900,
    margin=dict(l=60, r=30, t=80, b=60)
)

# 导出 HTML（可选：include_plotlyjs='cdn' 以获取极小文件，但需联网）
fig.write_html("impact_analysis.html", include_plotlyjs='cdn')
print("优化后的报告已生成：impact_analysis.html")