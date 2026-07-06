# 阶段2.4：洗车流程状态机

阶段2.4 的目标是把前面已经建立的策略、空间和喷嘴覆盖参数串成一个可检查的洗车流程状态机：

```text
wash_strategy_plan.json
  -> space_model_report.json
  -> nozzle_coverage_plan.json
  -> demo_wash_flow.json
  -> wash_flow_run.json
```

本阶段不是路径规划，不生成真实喷嘴轨迹，不做动画，不做 PLC，也不连接真实硬件。

## demo_wash_flow

`aicar_sim\data\wash_flows\demo_wash_flow.json` 定义阶段2.4的状态机配置。当前包含：

- `idle`
- `load_vehicle_context`
- `pre_rinse`
- `foam`
- `dwell`
- `top_clean`
- `side_clean`
- `wheel_clean`
- `air_dry`
- `completed`
- `aborted`
- `error`

主流程从 `idle` 开始，按第一条 `next_states` 串行执行，最终到达 `completed`。`aborted` 和 `error` 是保留的终止状态，用于后续人工中止和故障处理。

## 与洗车策略的关系

状态机中的洗车状态通过 `strategy_stage_id` 绑定阶段2.1生成的策略阶段：

- `pre_rinse`
- `foam`
- `dwell`
- `top_clean`
- `side_clean`
- `wheel_clean`
- `air_dry`

持续时间来自 `wash_strategy_plan.json`，因此当前 demo 的 `estimated_total_seconds` 与策略层保持一致。

## 与空间模型和喷嘴覆盖的关系

阶段2.4会读取 `space_model_report.json` 和 `nozzle_coverage_plan.json`，为每个洗车状态填充：

- `target_zone_ids`
- `assigned_nozzles`

这只是状态级别的喷嘴分配。它不代表真实喷嘴运动路径，也不代表真实设备控制逻辑。

## 输出

阶段2.4输出：

```text
aicar_sim\outputs\wash_flow\wash_flow_run.json
```

该文件是运行输出，不进入 Git。它包含：

- `run_version`
- `flow_id`
- `vehicle`
- `wash_profile`
- `wash_bay_id`
- `summary`
- `timeline`
- `limitations`

## 当前限制

- 不生成真实喷嘴路径。
- 不生成动画。
- 不控制 PLC。
- 不连接真实硬件。
- `aborted` 和 `error` 目前只作为状态机终止状态保留。

## 后续阶段

阶段2.5可以在 `wash_flow_run.json` 的基础上，为每个洗车状态生成抽象喷嘴路径点和覆盖顺序。

## 验收命令

```powershell
python aicar_sim\scripts\check_wash_flow_config.py
python aicar_sim\scripts\check_wash_state_machine.py
python aicar_sim\scripts\check_wash_flow_run.py
python aicar_sim\scripts\generate_wash_flow_run.py --vehicle-type-result vehicle_type_lab\outputs\predictions\vehicle_type_result.json
```
