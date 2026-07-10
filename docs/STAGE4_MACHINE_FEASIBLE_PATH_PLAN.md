# Stage4 Machine-Feasible Path Plan

## 1. 输入数据

- `abstract_nozzle_path_plan.json`
- `space_model_report.json`
- `nozzle_coverage_plan.json`
- `demo_cartesian_gantry.json`

## 2. 路径插值

每个抽象 segment 使用线性插值补点，控制相邻采样点距离。插值点保留 `state_id`、`zone_id`、`nozzle_id`、`segment_id` 和源点关系。

## 3. transition处理

segment之间不直接跳跃。候选路径通过车辆安全包络上方的 transition 平面连接。左右轮切换也使用内部安全 transition，避免线性插值穿过车辆。

## 4. 时间参数化

插值后路径按照目标速度、轴速度上限、轴加速度上限、最小时间间隔和状态切换降速规则生成时间戳。

## 5. 速度和加速度限制

每轴速度不得超过 motion model 配置。加速度超限时增加时间。当前使用基础梯形速度思想，不实现复杂动力学优化。

## 6. validation流程

验证器检查工作空间、洗车房边界、车辆安全包络、喷嘴参考距离、速度、加速度、时间连续性、路径连续性和字段完整性。

安全距离与喷嘴距离使用轴对齐包络和 zone reference surface 近似，报告中会明确记录 warning。

## 7. 输出文件

```text
aicar_sim\outputs\machine_path\machine_path_plan.json
aicar_sim\outputs\motion_validation\motion_validation_report.json
aicar_sim\outputs\motion_validation\stage4_motion_validation_report.html
```

这些文件是运行输出，不进入 Git。

## 8. 状态含义

- `PASS`：没有 violations 或 warnings。
- `PASS_WITH_WARNINGS`：没有 violations，但存在近似模型、transition 或参考参数 warning。
- `FAIL`：存在至少一个 violation，不能为了显示通过而删除检查或随意放宽参数。

## 9. 当前限制

- 通用三轴参考模型，不代表真实洗车机。
- 无真实 CAD 碰撞模型。
- 无喷嘴姿态自由度和车身曲面法向。
- 无执行机构动力学、伺服控制和 PLC 输出。
- 候选轨迹不能直接用于真实设备。

## 10. 后续真实参数替换方法

优先替换 `demo_cartesian_gantry.json` 中的工作空间、轴速度、轴加速度、安全距离和采样周期，再接入真实机构几何、喷嘴安装位姿、设备标定数据和控制接口。每次替换后必须重新生成并验证候选轨迹。
