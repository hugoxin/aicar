# 阶段4.3：碰撞与安全约束仿真

## 1. 阶段定位

阶段4.1/4.2把抽象喷嘴路径转换为满足参考工作空间、速度和加速度约束的候选机械轨迹。阶段4.3继续回答：候选轨迹是否进入车辆或洗车房障碍，多个执行机构能否在共享空间内安全调度，以及发生等待或中止时是否存在合格停机点。

本阶段输出是 `collision-safe candidate plan` 和 `safety-constrained simulation result`，不是实际设备碰撞认证，也不能直接下发 PLC。

## 2. 输入与输出

输入包括阶段4.2 `machine_path_plan.json`、参考运动模型、阶段2空间模型与喷嘴覆盖计划，以及：

- `aicar_sim/data/safety_models/demo_wash_bay_safety_layout.json`
- `aicar_sim/data/actuator_systems/demo_multi_actuator_system.json`

主要输出：

- `collision_safety_plan.json`
- `multi_actuator_schedule.json`
- `collision_safety_validation_report.json`
- `stage4_collision_safety_report.html`

这些文件是可重建运行产物，由 `.gitignore` 排除。

## 3. 静态障碍与安全区

参考布局用 AABB 描述左右墙和前后服务立柱。安全区分为：

- `forbidden`：车辆安全包络，轨迹点或扫掠体进入即为 CRITICAL。
- `slow`：车辆包络外侧预警带，速度比例不高于 0.5。
- `shared_interlock`：多个执行机构需要独占资源锁的共享空间。
- `safe_stop`：优先选择的安全停机区域。

所有参数集中在 JSON 中。AABB 边界接触按碰撞或区间重叠处理，并使用小 epsilon 抵御浮点误差。

## 4. 车辆安全余量

当前距离基于车辆 `safe_envelope`，不是实际车身曲面：

| 距离 | 结果 |
| --- | --- |
| `< 250 mm` | CRITICAL violation，整体 FAIL |
| `250-300 mm` | critical warning，整体至少 PASS_WITH_WARNINGS |
| `300-350 mm` | 普通 warning |
| `>= 350 mm` | 通过距离检查 |

该近似不含传感器误差、停车偏差、结构变形和真实执行误差。

## 5. 扫掠区域与碰撞检查

每两个相邻轨迹点结合喷嘴半径、执行机构 carriage half size 和额外 margin，生成保守 `conservative_aabb`。检查包括轨迹点/扫掠 AABB 与静态障碍、车辆禁入包络的相交，以及减速区速度策略。当前不生成 3D mesh，也不依赖外部碰撞引擎。

## 6. 多执行机构、同步与互锁

任务按照 `roof/left_side/right_side/front/rear/wheels` 分配给 top、left、right 三个参考执行机构。左右侧清洗和风干任务形成同步组；资源锁根据实际扫掠区域是否进入共享区触发。冲突通过延后任务解决，不删除任务，也不伪造冲突数。未解决冲突、同执行器重叠、未分配任务或明确死锁均导致 FAIL。

## 7. 安全停机点

候选点来自 home position 和配置的 safe-stop zone。每个执行机构至少选择一个位于工作空间内、避开静态障碍和车辆禁入包络的点，优先选择配置安全区内的点。找不到合格点时记录 CRITICAL violation。

## 8. Validation 状态

- `PASS`：无 violations，且只剩允许归类为说明性的限制或没有 warnings。
- `PASS_WITH_WARNINGS`：无 violations，但存在安全余量预警、同步退化、互锁等待或模型近似。
- `FAIL`：出现明确碰撞、禁入、非法停机点、未解决冲突、死锁或关键任务未分配。

## 9. 当前限制与替换路径

当前洗车房、执行机构尺寸和控制时序均为参考数据；静态几何和扫掠体均为 AABB；尚无真实 CAD、传感器不确定性、控制器响应、PLC、伺服、动力学、逆运动学或硬件联调。后续必须用实测尺寸、真实设备包络和安全认证流程替换参考参数。
