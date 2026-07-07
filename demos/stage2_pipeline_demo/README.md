# Stage2 Pipeline Demo

这是阶段2完整链路可视化 Demo，用于展示：

- 车型结果如何进入洗车策略。
- 洗车策略如何进入空间模型。
- 空间模型如何进入喷嘴覆盖。
- 喷嘴覆盖如何进入流程状态机。
- 流程状态机如何进入抽象路径点。
- 抽象路径点如何进入覆盖率报告。

## 运行方式

```powershell
Set-Location F:\aicar\demos\stage2_pipeline_demo
python scripts\check_stage2_pipeline_demo.py
python scripts\run_stage2_pipeline_demo.py --open-report
```

生成结果：

```text
demo_outputs\reports\stage2_pipeline_report.html
demo_outputs\json\wash_strategy_plan.json
demo_outputs\json\space_model_report.json
demo_outputs\json\nozzle_coverage_plan.json
demo_outputs\json\wash_flow_run.json
demo_outputs\json\abstract_nozzle_path_plan.json
demo_outputs\json\coverage_report.json
```

## 说明

- 当前是本地 Demo。
- 当前不代表真实硬件控制。
- 当前不代表真实清洗效果。
- 当前不包含 PLC。
- 当前不包含动画引擎。
- 当前不包含真实轨迹规划。
- `demo_outputs` 中的 HTML 和 JSON 默认不进入 Git。
