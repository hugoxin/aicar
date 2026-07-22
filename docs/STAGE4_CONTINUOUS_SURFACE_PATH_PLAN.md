# Stage4.5 Continuous Surface Path Plan

## 1. 定位

Stage4.5 从路径生成源头重构连续清洗面候选路径。它使用通用参考车辆解析表面，不修改阶段2原始 `abstract_nozzle_path_plan.json`，也不移动 `stage4-motion-safety-baseline`。

当前结果只能称为 continuous-surface candidate path。它不是实际车辆CAD/点云路径，不是PLC或伺服程序，也不能直接控制硬件。

## 2. 为什么Stage4.4无法明显缩短路径

Stage4.4保留阶段2的22个抽象源段，只能在已生成轨迹末端做删重、共线简化、transition候选和调度优化。原始路径没有真实连续表面、局部扫描线和相邻pass连接，因此无法从根本上消除区域跳转和安全平面往返。

Stage4.5保留旧路径作为基线，新增独立链路：

```text
reference surface model
  -> surface patches and local coordinates
  -> boustrophedon / wheel-ring scan passes
  -> local and adaptive-safe connections
  -> continuous_surface_path_plan.json
  -> continuous_machine_path_plan.json
  -> collision, interlock, schedule, safe-stop validation
  -> comparison JSON and single-file HTML
```

## 3. 参考表面patch

- `roof_main`：arched rectangle
- `left_side_main` / `right_side_main`：vertical rectangle
- `front_main` / `rear_main`：vertical rectangle
- 四个wheel patch：circular disk

所有尺寸和patch参数集中在 `aicar_sim/data/surface_models/demo_sedan_surface_model.json`。模型不包含后视镜、门把手、扰流板、轮拱和实际曲率细节。

## 4. 局部坐标与法向

矩形patch使用二维 `(u, v)` 局部坐标；轮面使用圆盘局部坐标。解析法向用于计算参考喷嘴点：

```text
nozzle_point = surface_point + normal * preferred_standoff_mm
```

进入机械验证前，再叠加Stage4硬安全距离。所有法向归一化，硬安全下限保持250 mm。

## 5. 连续扫描策略

- roof：longitudinal boustrophedon
- left/right side：longitudinal boustrophedon
- front/rear：horizontal boustrophedon
- wheels：concentric rings

相邻pass方向交替。局部pass优先使用U-turn连接，不返回统一最高安全平面。相邻patch先检查direct connection；不安全时使用adaptive safe connection。

## 6. 状态和喷嘴映射

状态和喷嘴语义读取现有 `wash_flow_run.json` 与 `nozzle_coverage_plan.json`。总体顺序固定为：

```text
pre_rinse -> foam -> dwell -> top_clean -> side_clean -> wheel_clean -> air_dry
```

`dwell` 保留状态和时长语义，但不生成运动路径。跨state重排被禁止。必要zone和四个wheel patch均保留。

## 7. Coverage近似

每个patch按50 mm二维局部栅格估算覆盖。scan pass按喷嘴effective width标记覆盖单元，输出patch、zone和total coverage以及uncovered cells。

Coverage只表示参考表面几何覆盖，不表示水流、污渍去除或实际清洗效果，不执行CFD。

## 8. 重新进入Stage4安全链路

新路径重新执行：

- workspace、速度、加速度、时间连续性
- vehicle hard clearance
- static obstacle与forbidden zone
- conservative AABB swept volume
- actuator task allocation
- shared-space interlock与冲突消解
- deadlock检查
- safe-stop验证

旧路径安全通过结果不能替代新路径验证。

## 9. 接受和拒绝规则

只有在motion/collision violations均为0、无碰撞、无禁入、无未分配任务、无未解冲突、无deadlock、safe-stop完整、clearance不低于250 mm、coverage达标、状态/zone不丢失、点数不超过5000时，才允许保留为安全候选。

结果状态包括：

- `ACCEPTED`
- `ACCEPTED_WITH_WARNINGS`
- `NO_MEANINGFUL_IMPROVEMENT`
- `REJECTED_SAFETY_REGRESSION`
- `FAILED`

未达到目标时必须输出 `TARGET_NOT_REACHED`。

## 10. 当前结果与原因

当前链路安全和coverage通过，但完整表面在多个必要wash state中重复扫描，使路径长度和周期高于冻结基线。transition从21降至5，但主路径目标没有达到，因此状态为 `NO_MEANINGFUL_IMPROVEMENT`。

这说明下一轮应调整源头任务复用、pass spacing、状态级扫描密度和表面分块策略，而不是降低安全要求或伪造改善。

## 11. 后续替换

后续可以将解析patch替换为CAD、点云或参数化曲面，并加入真实法向、曲率、自适应pass spacing、喷嘴姿态、车辆停放误差和真实设备参数。完成离线验证和安全评审前，不进入PLC或硬件控制。
