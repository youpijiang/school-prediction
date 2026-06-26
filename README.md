# 学校事务预测工具

使用蒙特卡洛模拟方法，预测学校突发事务对时间占用的影响程度。

## 功能简介

本项目通过模拟日常突发事务（如临时会议、帮助同学等）的发生频率和耗时，估算在指定天数内这些事务会占用多少比例的时间，并将结果分为 5 个等级进行可视化展示。

## 环境要求

- Python 3.7 或更高版本
- 依赖库：numpy、plotly

## 快速开始

### 1. 安装依赖

```bash
pip install numpy plotly
2. 运行程序
cd core
python predictor.py
运行完成后，会在 core 目录下生成 impact_analysis.html 文件。

3. 查看结果
用浏览器打开 impact_analysis.html 即可查看交互式图表。

参数说明
在 core/predictor.py 文件开头可修改以下参数：

参数名	默认值	含义
DAYS	4	模拟的天数
MAX_HOURS_PER_DAY	8	每天可用时间（小时）
AVG_EVENTS_PER_DAY	1.2	平均每天突发事务数量
MEAN_IMPACT_HOURS	1.5	每件事务平均耗时（小时）
NUM_SIMULATIONS	100000	模拟次数（越大越精确）
输出说明
生成的 HTML 图表包含：

5 个影响等级（从低到高）
每个等级对应的出现概率
交互式悬停显示具体数值
常见问题
问题：提示找不到模块

解决方案：确保已执行 pip install numpy plotly 安装依赖。

问题：HTML 文件无法打开

解决方案：右键文件，选择用浏览器（Chrome、Edge、Firefox 等）打开。

问题：想模拟更长时间

解决方案：修改 DAYS 参数，例如改为 7 模拟一周，改为 30 模拟一个月。

项目结构
school-prediction/
├── core/
│   ├── predictor.py          # 主程序
│   ├── logger_module.py      # 日志模块
│   ├── visualize_final.py    # 可视化模块
│   └── impact_analysis.html  # 输出结果
├── Process/                   # 处理过程目录
└── Result/                    # 结果输出目录
注意事项
首次运行建议先使用默认参数，确认程序正常工作后再修改
模拟结果仅供参考，实际时间安排请灵活调整
增加模拟次数会提高精度，但运行时间也会增加