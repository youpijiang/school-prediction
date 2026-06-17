import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==================== 1. 固定种子与模拟 ====================
np.random.seed(42)

DAYS = 4
MAX_HOURS_PER_DAY = 8
TOTAL_MAX_HOURS = DAYS * MAX_HOURS_PER_DAY
AVG_EVENTS_PER_DAY = 1.2
MEAN_IMPACT_HOURS = 1.5
NUM_SIMULATIONS = 100_000

def simulate_one_run():
    total_impact = 0.0
    for _ in range(DAYS):
        n = np.random.poisson(AVG_EVENTS_PER_DAY)
        for _ in range(n):
            impact = np.random.exponential(MEAN_IMPACT_HOURS)
            total_impact += impact
    ratio = total_impact / TOTAL_MAX_HOURS
    return min(ratio, 1.0)

ratios = np.array([simulate_one_run() for _ in range(NUM_SIMULATIONS)])

# ==================== 2. 剔除与分级 ====================
exclude_low, exclude_high = 0.10, 0.90
filtered = ratios[(ratios >= exclude_low) & (ratios < exclude_high)]

quantiles = np.linspace(0, 1, 6)          # 5 等分
boundaries = np.quantile(filtered, quantiles)
level_bounds = [exclude_low] + list(boundaries[1:-1]) + [boundaries[-1]]

# 各级别条件概率
level_probs = []
for i in range(len(level_bounds)-1):
    low, high = level_bounds[i], level_bounds[i+1]
    prob = np.sum((filtered >= low) & (filtered < high)) / len(filtered)
    level_probs.append(prob)

prob_low = np.sum(ratios < exclude_low) / NUM_SIMULATIONS
prob_high = np.sum(ratios >= exclude_high) / NUM_SIMULATIONS

# ==================== 3. KDE 计算（需要 scipy，若没有则回退为密度直方图） ====================
try:
    from scipy.stats import gaussian_kde
    kde = gaussian_kde(filtered)
    x_kde = np.linspace(exclude_low, filtered.max(), 300)
    y_kde = kde(x_kde)
    use_kde = True
except ImportError:
    use_kde = False
    print("未安装 scipy，将使用直方图代替 KDE。建议执行 pip install scipy 获取更平滑曲线。")

# ==================== 4. CDF 数据 ====================
sorted_ratios = np.sort(ratios)
cdf_y = np.arange(1, len(sorted_ratios)+1) / len(sorted_ratios)

# ==================== 5. 创建 2x2 子图布局 ====================
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

# ==================== 6. 子图 1：KDE + 剔除阴影 + 分级线 ====================
if use_kde:
    fig.add_trace(
        go.Scatter(x=x_kde, y=y_kde, mode='lines', fill='tozeroy',
                   name='KDE 密度', line=dict(color='steelblue', width=2)),
        row=1, col=1
    )
else:
    fig.add_trace(
        go.Histogram(x=filtered, histnorm='probability density',
                     nbinsx=100, marker_color='steelblue', opacity=0.5,
                     name='密度直方图'),
        row=1, col=1
    )

# 剔除区灰色阴影
fig.add_vrect(x0=0, x1=exclude_low, fillcolor="gray", opacity=0.15,
              layer="below", line_width=0, row=1, col=1)
fig.add_vrect(x0=exclude_high, x1=1.0, fillcolor="gray", opacity=0.15,
              layer="below", line_width=0, row=1, col=1)

# 分级垂直线
for i, b in enumerate(level_bounds[1:-1], 1):
    fig.add_vline(x=b, line_dash="dash", line_color="darkorange",
                  opacity=0.8, row=1, col=1)
    fig.add_annotation(x=b, y=0.95, yref="y domain", text=f"Q{i}",
                       showarrow=False, font=dict(color="darkorange", size=10),
                       row=1, col=1)

fig.update_xaxes(tickformat=".0%", title_text="影响占比", row=1, col=1)
fig.update_yaxes(title_text="概率密度", row=1, col=1)

# ==================== 7. 子图 2：CDF ====================
fig.add_trace(
    go.Scatter(x=sorted_ratios, y=cdf_y, mode='lines',
               line=dict(color='steelblue', width=2),
               name='CDF'),
    row=1, col=2
)
# 关键参考线
fig.add_hline(y=0.5, line_dash="dot", line_color="gray", opacity=0.6, row=1, col=2)
fig.add_hline(y=0.9, line_dash="dot", line_color="gray", opacity=0.6, row=1, col=2)
fig.add_vline(x=exclude_low, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=2)
fig.add_vline(x=exclude_high, line_dash="dash", line_color="gray", opacity=0.5, row=1, col=2)

fig.update_xaxes(tickformat=".0%", title_text="影响占比", row=1, col=2)
fig.update_yaxes(tickformat=".0%", title_text="累积概率", range=[0,1.05], row=1, col=2)

# ==================== 8. 子图 3：水平条形图（分级） ====================
widths = [level_bounds[i+1] - level_bounds[i] for i in range(len(level_bounds)-1)]
lefts = level_bounds[:-1]
labels = [f"Q{i+1} ({lefts[i]:.1%}–{lefts[i]+widths[i]:.1%})" for i in range(len(widths))]

fig.add_trace(
    go.Bar(
        y=labels,
        x=widths,
        base=lefts,
        orientation='h',
        marker=dict(color=level_probs, colorscale='Viridis', showscale=False),
        text=[f"{p:.0%}" for p in level_probs],
        textposition='inside',
        insidetextanchor='middle',
        textfont=dict(color='white', size=12),
        name='等级概率'
    ),
    row=2, col=1
)
fig.update_xaxes(tickformat=".0%", title_text="影响占比区间", range=[0.05, 1.0], row=2, col=1)
fig.update_yaxes(title_text="", row=2, col=1)

# ==================== 9. 子图 4：小提琴图对比 ====================
fig.add_trace(
    go.Violin(x=['全部模拟']*len(ratios),
              y=ratios,
              name='全部模拟',
              box_visible=True,
              meanline_visible=True,
              line_color='steelblue',
              fillcolor='lightsteelblue',
              opacity=0.6,
              points=False),
    row=2, col=2
)
fig.add_trace(
    go.Violin(x=['剔除后']*len(filtered),
              y=filtered,
              name='剔除极端值后',
              box_visible=True,
              meanline_visible=True,
              line_color='salmon',
              fillcolor='salmon',
              opacity=0.6,
              points=False),
    row=2, col=2
)
fig.update_yaxes(tickformat=".0%", title_text="影响占比", row=2, col=2)

# ==================== 10. 全局布局与字体 ====================
fig.update_layout(
    title_text="未来四天突发事件影响占比模拟分析（固定种子 = 42）",
    font=dict(family="Microsoft YaHei, SimHei, sans-serif", size=12),
    showlegend=False,
    width=1200,
    height=900,
    margin=dict(l=60, r=30, t=80, b=60)
)

# ==================== 11. 导出 HTML ====================
fig.write_html("impact_analysis.html")
print("分析报告已生成：impact_analysis.html，请用浏览器打开。")