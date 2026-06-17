# 以下的依赖是程序正常运行必要且充分的条件，详细说明请查看requirements和README文件

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==================== 固定种子、参数、模拟 ====================
np.random.seed(42)

DAYS = 5
MAX_HOURS_PER_DAY = 9
TOTAL_MAX_HOURS = DAYS * MAX_HOURS_PER_DAY
AVG_EVENTS_PER_DAY = 1.2
MEAN_IMPACT_HOURS = 1.5
NUM_SIMULATIONS = 100_000

def simulate_one_run():
    total = 0.0
    for _ in range(DAYS):
        n = np.random.poisson(AVG_EVENTS_PER_DAY)
        for _ in range(n):
            total += np.random.exponential(MEAN_IMPACT_HOURS)
    return min(total / TOTAL_MAX_HOURS, 1.0)

ratios = np.array([simulate_one_run() for _ in range(NUM_SIMULATIONS)])

# ==================== 剔除与分级（保证每个区间都有数据） ====================
exclude_low, exclude_high = 0.10, 0.90
mask_mid = (ratios >= exclude_low) & (ratios < exclude_high)
filtered = ratios[mask_mid]

# 将中间数据排序，按样本数量分成 5 等份（或更少，如果数据不够）
sorted_f = np.sort(filtered)
n = len(sorted_f)

# 目标等级数
k = 5
if n < k:            # 数据太少，有多少分多少
    k = n
    # 每个区间一个点，边界直接取该点值和下一个点值之间的中点
    boundaries = []
    for i in range(k - 1):
        mid = (sorted_f[i] + sorted_f[i+1]) / 2.0
        boundaries.append(mid)
    level_bounds = [exclude_low] + boundaries + [sorted_f[-1]]
else:
    # 计算每个区间的样本数（尽量平均）
    counts = np.full(k, n // k, dtype=int)
    counts[:n % k] += 1                # 前几个区间多放一个样本
    # 分割点索引（前 k-1 个区间的最后一个样本位置）
    indices = np.cumsum(counts)[:-1]
    boundaries = []
    for idx in indices:
        # 边界取该样本与下一个样本的正中间，避免与数据点重合
        mid = (sorted_f[idx] + sorted_f[idx + 1]) / 2.0
        boundaries.append(mid)
    level_bounds = [exclude_low] + boundaries + [sorted_f[-1]]

# 计算各级概率（现在绝对没有 0%）
level_probs = []
for i in range(len(level_bounds) - 1):
    low, high = level_bounds[i], level_bounds[i+1]
    prob = np.sum((filtered >= low) & (filtered < high)) / len(filtered)
    level_probs.append(prob)

# 根据实际区间数动态生成等级名称
generic_names = ["轻微影响", "较低影响", "中等影响", "较高影响", "严重影响",
                 "极端影响1", "极端影响2", "极端影响3"]
level_names = generic_names[:len(level_probs)]

prob_low = np.sum(ratios < exclude_low) / NUM_SIMULATIONS
prob_high = np.sum(ratios >= exclude_high) / NUM_SIMULATIONS

# 各级概率（条件概率）
level_probs = []
for i in range(len(level_bounds)-1):
    low, high = level_bounds[i], level_bounds[i+1]
    prob = np.sum((filtered >= low) & (filtered < high)) / len(filtered)
    level_probs.append(prob)

prob_low = np.sum(ratios < exclude_low) / NUM_SIMULATIONS
prob_high = np.sum(ratios >= exclude_high) / NUM_SIMULATIONS

# ==================== 构建 2x2 子图 ====================
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "突发事件影响占比分布直方图（含剔除区和分级界线）",
        "累积概率曲线（CDF）：不超过某占比的可能性",
        "剔除极端值后的五级影响范围与概率",
        "全部模拟 vs 剔除极端值后的分布对比"
    ),
    vertical_spacing=0.13,
    horizontal_spacing=0.10,
)

# ---- 子图1：直方图（用5%宽的箱子） ----
# 将全数据画成直方图，但为了显示剔除区和分级区，我们用 go.Histogram 分别画三部分
# 更简单方法：画一个整体直方图，然后用 vrect 标记区域
fig.add_trace(
    go.Histogram(x=ratios, xbins=dict(start=0, end=1, size=0.05),
                 marker_color='steelblue', opacity=0.7, name='模拟次数'),
    row=1, col=1
)
fig.add_vrect(x0=0, x1=exclude_low, fillcolor="gray", opacity=0.2,
              line_width=0, annotation_text="剔除区", annotation_position="top left",
              row=1, col=1)
fig.add_vrect(x0=exclude_high, x1=1.0, fillcolor="gray", opacity=0.2,
              line_width=0, annotation_text="剔除区", annotation_position="top right",
              row=1, col=1)
# 加分级垂直线
for i, b in enumerate(level_bounds[1:-1], 1):
    fig.add_vline(x=b, line_dash="dash", line_color="darkorange", opacity=0.8, row=1, col=1)
    fig.add_annotation(x=b, y=0.9, yref="y domain", text=f"Q{i}",
                       showarrow=False, font=dict(color="darkorange", size=10), row=1, col=1)

fig.update_xaxes(tickformat=".0%", title_text="影响时间占比", row=1, col=1)
fig.update_yaxes(title_text="频数", row=1, col=1)

# ---- 子图2：CDF（降采样到500点） ----
sorted_r = np.sort(ratios)
indices = np.linspace(0, len(sorted_r)-1, 500, dtype=int)
cdf_x = sorted_r[indices]
cdf_y = (indices + 1) / len(sorted_r)

fig.add_trace(go.Scatter(x=cdf_x, y=cdf_y, mode='lines',
                         line=dict(color='steelblue', width=2), name='CDF'),
              row=1, col=2)
fig.add_hline(y=0.5, line_dash="dot", line_color="gray", opacity=0.6,
              annotation_text="50%可能", annotation_position="bottom right", row=1, col=2)
fig.add_hline(y=0.9, line_dash="dot", line_color="gray", opacity=0.6,
              annotation_text="90%可能", annotation_position="bottom right", row=1, col=2)
fig.add_vline(x=exclude_low, line_dash="dash", line_color="gray", opacity=0.4, row=1, col=2)
fig.add_vline(x=exclude_high, line_dash="dash", line_color="gray", opacity=0.4, row=1, col=2)

fig.update_xaxes(tickformat=".0%", title_text="影响占比", row=1, col=2)
fig.update_yaxes(tickformat=".0%", title_text="累积概率", range=[0, 1.02], row=1, col=2)

# ---- 子图3：水平条形图（保证无零概率） ----
widths = [level_bounds[i+1] - level_bounds[i] for i in range(len(level_bounds)-1)]
lefts = level_bounds[:-1]
bar_labels = [f"{level_names[i]} ({lefts[i]:.1%}~{lefts[i]+widths[i]:.1%})"
              for i in range(len(level_names))]

fig.add_trace(
    go.Bar(
        y=bar_labels,
        x=widths,
        base=lefts,
        orientation='h',
        marker=dict(color=level_probs, colorscale='YlOrRd', showscale=False),
        text=[f"{p:.0%}" for p in level_probs],
        textposition='inside',
        insidetextanchor='middle',
        textfont=dict(color='white', size=11),
        name='概率'
    ),
    row=2, col=1
)
fig.update_xaxes(tickformat=".0%", title_text="影响占比区间", range=[0.05, 1.0], row=2, col=1)
fig.update_yaxes(title_text="", row=2, col=1)

# ---- 子图4：分组直方图（全部 vs 剔除后，重叠显示） ----
fig.add_trace(
    go.Histogram(x=ratios, xbins=dict(start=0, end=1, size=0.05),
                 marker_color='steelblue', opacity=0.5, name='全部模拟',
                 histnorm='probability density'),
    row=2, col=2
)
fig.add_trace(
    go.Histogram(x=filtered, xbins=dict(start=0, end=1, size=0.05),
                 marker_color='salmon', opacity=0.6, name='剔除极端值后',
                 histnorm='probability density'),
    row=2, col=2
)
fig.update_xaxes(tickformat=".0%", title_text="影响占比", row=2, col=2)
fig.update_yaxes(title_text="概率密度", row=2, col=2)

# ---- 全局设置 ----
fig.update_layout(
    title_text="未来四天突发事件影响时间占比模拟分析（固定种子42，10万次模拟）",
    font=dict(family="Microsoft YaHei, SimHei, sans-serif", size=12),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    width=1200,
    height=900,
    margin=dict(l=60, r=30, t=90, b=60)
)

# 输出 HTML（CDN 模式，极小文件）
fig.write_html("impact_analysis.html", include_plotlyjs=True)   # 或 'inline'
print("图表已生成：impact_analysis.html（约50KB，需联网显示）")