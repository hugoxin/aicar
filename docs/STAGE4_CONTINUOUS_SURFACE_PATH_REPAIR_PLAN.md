# Stage4.5-R 连续清洗面路径修复计划与结果

## 1. 阶段定位

Stage4.5 第一次实验把 transition 从 21 降到 5，但机械路径从 `361236.112 mm` 增至 `529270.070 mm`，结论为 `NO_MEANINGFUL_IMPROVEMENT`。Stage4.5-R 在独立修复分支中修正路径源头与调度输入，Stage4.1 至 4.4 冻结安全基线不变。

当前结果只能称为 state-aware continuous-surface candidate path。它不是 CAD 或点云路径，不是实际喷嘴姿态控制，不可下发 PLC、伺服或真实硬件。

## 2. 修复链路

```text
wash states + nozzle effective width + analytic surface patches
  -> state-specific pass spacing
  -> adaptive per-state/per-patch coverage
  -> patch order and direction optimization
  -> safe direct or adaptive patch connections
  -> aggregated surface route tasks
  -> frozen Stage4 motion/collision/safe-stop checks
  -> actual shared-zone interval schedule adapter
  -> three-way JSON and standalone HTML report
```

## 3. State-specific pass spacing

初始间距按 `effective_width_mm * spacing_factor` 计算。有效宽度优先来自 `nozzle_coverage_plan.json`，仅在字段缺失时使用 repair profile 中的 state fallback，并记录 warning。`dwell` 保留状态与时长语义，但不生成运动路径。

| State | Spacing factor | 实际 effective width mm | 初始 spacing mm | 最终 spacing mm | 初始 pass | 最终 pass |
| --- | ---: | --- | --- | --- | ---: | ---: |
| pre_rinse | 0.88 | 250 / 420 / 500 | 220 / 369.6 / 440 | 250 / 420 / 500 | 24 | 23 |
| foam | 0.92 | 700 | 644 | 700 | 11 | 11 |
| top_clean | 0.72 | 500 | 360 | 500 | 5 | 3 |
| side_clean | 0.72 | 420 | 302.4 | 420 | 14 | 12 |
| wheel_clean | 0.68 | 250 | 170 | 250 | 8 | 8 |
| air_dry | 0.88 | 600 | 528 | 600 | 11 | 11 |

## 4. 自适应覆盖

每个 state-patch 从初始 spacing 生成 pass，并在 50 mm 二维局部栅格上估算覆盖。低于最低阈值时 spacing 缩小 5%；高于偏好上限时尝试扩大 5%，只有新方案仍满足最低阈值才接受。最多迭代 20 次，spacing 不超过喷嘴有效宽度。

当前有限解析矩形和圆盘在喷嘴宽度限制下仍得到 100% unique geometric coverage。这是离散栅格和规则几何造成的 `COVERAGE_EXACT_LIMIT`，不是算法追求 100%，也不代表真实清洗效果。

不同状态经过同一表面代表预冲、泡沫、清洗和吹干等不同工艺；修复只降低 state 内部过密覆盖，不删除必要状态。

## 5. Surface route 与连接

同一 state 和 actuator 内为每个 patch 生成正向/反向候选，并以安全优先、距离次优的成本选择访问顺序。不跨 actuator，不跨 state 重排。

连接候选依次检查直线、两段安全高度和局部安全高度。候选必须满足 workspace、250 mm 硬间隙、车辆禁入区、静态障碍和后续冻结 swept AABB 碰撞校验。安全候选记为 `DIRECT_PATCH_CONNECTION`，否则使用 `ADAPTIVE_SAFE_CONNECTION`。

修正版得到 40 条 local U-turn、2 条安全 direct connection、20 条 adaptive connection、5 条必要 state transition，0 条 rejected connection。

## 6. Scan pass 与 surface task

Scan pass 是 task 内部轨迹语义，不应等同于调度 task。修正版按 `state_id + surface_route_id + actuator_id + nozzle_id` 聚合 68 条 scan pass 为 18 个 surface route task。pass ID、state、zone、patch、nozzle 和 actuator 语义均被保留。

冻结碰撞链路仍会产生连接与 transition 安全任务；Stage4.5-R schedule adapter 将同 actuator、同 state 的 connector task 折叠回 route task，最终调度输入为 23 个 task。

## 7. 实际共享资源区间

原 Stage4.5 对进入共享区的任务按整任务加锁。修正版根据 swept volume 首次进入和最后离开共享区的 trajectory point，计算 `actual_shared_zone_swept_interval`；执行器独占 rail 仍按完整占用区间锁定。冲突检测、冲突消解和 deadlock 检查复用冻结 Stage4 模块。

## 8. 三方结果

| 指标 | Stage4 冻结 | Stage4.5 首版 | Stage4.5-R |
| --- | ---: | ---: | ---: |
| trajectory point | 2575 | 4631 | 2503 |
| transition | 21 | 5 | 5 |
| machine path mm | 361236.112 | 529270.070 | 328502.099 |
| motion duration s | 2870.414 | 3731.714 | 2571.103 |
| schedule duration s | 2339.304 | 3880.588 | 1920.251 |
| total delay s | 16920.251 | 38484.791 | 8836.672 |
| parallel groups | 18 | 6 | 11 |

相对首版，路径缩短 37.933%，运动时长缩短 31.101%，调度时长缩短 50.516%，累计延迟缩短 77.039%。相对 Stage4 冻结基线，四个核心时间/距离指标也均降低。

## 9. 接受与拒绝规则

- `REJECTED_SAFETY_REGRESSION`：任一运动、碰撞、禁区、互锁、覆盖或任务完整性硬条件失败。
- `NO_MEANINGFUL_IMPROVEMENT`：安全未退化，但相对首版没有足够改善。
- `ACCEPTED_WITH_WARNINGS`：安全通过且相对首版明显改善，但未全面优于 Stage4 基线。
- `ACCEPTED`：安全通过、transition 不超过 5，且路径、运动、调度和累计延迟均低于 Stage4 基线。

本次结果为 `ACCEPTED`。配置偏好中的“相对 Stage4 路径降幅至少 10%”实际为 9.062%，报告如实标记 `TARGET_NOT_REACHED`；这不是硬安全或硬接受条件。

## 10. 当前局限

1. 车身是参考解析表面，不是 CAD 或点云。
2. Coverage 是二维几何估算，不是水流、污渍或真实清洗效果。
3. 路由和 spacing 是启发式优化，不保证全局最优。
4. 喷嘴姿态、软管、真实机械动力学和控制器时序未建模。
5. 当前不连接 PLC、伺服、SDK 或真实硬件，不能生成设备控制指令。
6. Stage4.5 首版和 Stage4.5-R 当前均未合并 `main`，Stage4 冻结 tag 不变。
