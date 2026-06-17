import random
import matplotlib

# 强制使用非界面渲染模式，适配网页
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import datetime, timedelta


# ====================== 1. 基础配置（完全不变） ======================
class WorkConfig:
    def __init__(self):
        self.daily_max_time = 8
        self.predict_days = 4
        self.start_date = datetime.now().date()

        self.event_list = [
            {"name": "临时会议", "type": "工作", "prob": 0.40, "loss": 1.5},
            {"name": "设备故障", "type": "工作", "prob": 0.25, "loss": 1.0},
            {"name": "紧急沟通", "type": "工作", "prob": 0.30, "loss": 0.7},
            {"name": "系统宕机", "type": "工作", "prob": 0.15, "loss": 1.2},
            {"name": "上级临时任务", "type": "工作", "prob": 0.35, "loss": 1.0},
            {"name": "身体不适", "type": "个人", "prob": 0.10, "loss": 0.8},
            {"name": "家庭临时事务", "type": "个人", "prob": 0.08, "loss": 1.0},
            {"name": "私人预约", "type": "个人", "prob": 0.07, "loss": 0.5},
            {"name": "通勤延误", "type": "个人", "prob": 0.12, "loss": 0.6},
        ]


# ====================== 2. 核心预测（完全不变） ======================
class WorkForecast:
    _FIXED_RANDOM_SEED = 10086

    def __init__(self):
        self.config = WorkConfig()
        self.forecast_data = []
        self.rng = random.Random(self._FIXED_RANDOM_SEED)

    def calc_one_day(self):
        while True:
            happen_events = []
            total_loss = 0.0

            for event in self.config.event_list:
                if self.rng.random() <= event["prob"]:
                    happen_events.append(f"[{event['type']}] {event['name']}")
                    total_loss += event["loss"]

            real_time = max(0, self.config.daily_max_time - total_loss)
            loss_rate = (total_loss / self.config.daily_max_time) * 100

            if 10 <= loss_rate <= 89.9:
                break

        if 10.0 <= loss_rate < 16.4:
            level = "🟢 Q1 轻微影响"
        elif 16.4 <= loss_rate < 23.1:
            level = "🟡 Q2 较低影响"
        elif 23.1 <= loss_rate < 30.8:
            level = "🟠 Q3 中等影响"
        elif 30.8 <= loss_rate < 43.7:
            level = "🔴 Q4 较高影响"
        elif 43.7 <= loss_rate <= 89.9:
            level = "⚫ Q5 严重影响"
        else:
            level = "未知等级"

        return happen_events, round(total_loss, 2), round(real_time, 2), round(loss_rate, 1), level

    def run_4days_forecast(self):
        self.rng.seed(self._FIXED_RANDOM_SEED)
        self.forecast_data = []

        for i in range(self.config.predict_days):
            date = self.config.start_date + timedelta(days=i)
            events, loss, real, rate, level = self.calc_one_day()

            self.forecast_data.append({
                "日期": str(date),
                "基准工时": self.config.daily_max_time,
                "发生事件": events if events else ["无突发情况"],
                "总损耗": loss,
                "实际可用": real,
                "损耗占比": rate,
                "影响等级": level
            })
        return self.forecast_data


# ====================== 3. 生成网页可用的 Base64 图表 ======================
def get_chart_base64(data):
    days = [f"第{i + 1}天" for i in range(4)]
    loss_rates = [day["损耗占比"] for day in data]
    real_times = [day["实际可用"] for day in data]

    # Windows11 字体（保持不变）
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei UI"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.bar(days, loss_rates, color="#4472C4", alpha=0.7)
    ax1.set_title("未来4天工作时间损耗占比（%）")
    ax1.set_ylabel("损耗占比(%)")
    for i, v in enumerate(loss_rates):
        ax1.text(i, v + 1, f"{v}%", ha="center")

    ax2.plot(days, real_times, marker="o", color="red", linewidth=2)
    ax2.set_title("未来4天实际可用工作时间（小时）")
    ax2.set_ylabel("可用时间(h)")
    for i, v in enumerate(real_times):
        ax2.text(i, v + 0.1, f"{v}h", ha="center")

    plt.tight_layout()

    # 转为网页能直接显示的 base64 编码
    buffer = BytesIO()
    plt.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    buffer.close()
    plt.close()
    return image_base64


# ====================== 4. 输出 HTML 格式 ======================
if __name__ == "__main__":
    forecast = WorkForecast()
    result = forecast.run_4days_forecast()
    chart_base64 = get_chart_base64(result)

    # 输出可直接在浏览器打开的 HTML
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>未来4天工作突发影响预测</title>
        <style>
            body{{font-family: "Microsoft YaHei UI"; margin: 30px;}}
            .day{{border:1px solid #ddd; padding:15px; margin:10px 0; border-radius:8px;}}
            .level{{font-weight:bold;}}
            img{{width:100%; max-width:800px;}}
        </style>
    </head>
    <body>
        <h2>未来4天工作突发影响预测（网页可视化版）</h2>
        <img src="data:image/png;base64,{chart_base64}" />
        <br><br>
        <h3>详细数据</h3>
    """

    for idx, day in enumerate(result, 1):
        html += f"""
        <div class="day">
            <h4>📅 第{idx}天 | {day['日期']}</h4>
            <p>基准工时：{day['基准工时']}h</p>
            <p>实际可用：{day['实际可用']}h | 总损耗：{day['总损耗']}h | 损耗占比：{day['损耗占比']}%</p>
            <p class="level">影响等级：{day['影响等级']}</p>
            <p>发生事件：{"；".join(day['发生事件'])}</p>
        </div>
        """

    html += """
    </body>
    </html>
    """

    # 保存为 HTML 文件，双击直接在浏览器打开
    with open("../Result/预测报告.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("✅ 已生成：预测报告.html")
    print("✅ 可直接用浏览器打开，完美适配网页前端")