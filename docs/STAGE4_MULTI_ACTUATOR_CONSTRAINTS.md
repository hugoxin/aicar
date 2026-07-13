# 阶段4.3：多执行机构约束

## 1. 三个参考执行机构

`demo_multi_actuator_system.json` 定义：

- `top_actuator`：优先处理 roof，可处理 front/rear。
- `left_side_actuator`：处理 left_side、左侧 wheels，并可参与 front/rear。
- `right_side_actuator`：处理 right_side、右侧 wheels，并可参与 front/rear。

每个执行机构包含 home position、允许区域、末端半径、carriage half size 和可用资源。当前参数是通用参考值。

## 2. Task 分配

阶段4.2 segment 转换为 task，保留 state、zone、nozzle、点索引和估算持续时间。`roof/left_side/right_side` 使用确定映射；wheel segment 按 x 坐标拆为左右任务；front/rear 根据轨迹平均 x 选择可用执行器。无法确定分配时保留为 unassigned，不能静默删除。

## 3. 并行与同步

同一 state 内不同执行器可以并行，同一执行器任务严格串行。`side_clean` 与 `air_dry` 的左右 process task 形成同步组，状态为：

- `SYNCHRONIZED`
- `DEGRADED`
- `BLOCKED_BY_INTERLOCK`
- `NOT_APPLICABLE`

互锁优先于同步；因此同步被资源锁打断时保留 warning，而不是绕过安全锁。

## 4. 资源锁和冲突解决

左右/顶部轨道是各执行器固有资源。中心共享空间由任务的实际 swept AABB 相交触发；front/rear crossing 对应独占资源。不同执行器对同一资源的时间区间相交（包括边界接触）构成冲突。

调度器将后发生任务延迟到阻塞任务结束后，并记录 `DELAYED_BY_INTERLOCK`、delay reason 和总等待时间。冲突解决前后数量均保留在输出中，不通过删除任务换取 PASS。

## 5. 死锁与安全停机

非正持续时间、无法完成的资源安排或未解决共享空间冲突进入 violations。每个执行器还必须拥有至少一个合法安全停机点，供共享区等待或安全撤离使用。

## 6. 后续真实控制器映射

未来接入真实控制器前，需要替换执行器几何、轴限位、控制周期、互锁握手、急停链路和安全 PLC 规则，并经过真实 CAD 碰撞分析、离线仿真、低速试运行和设备安全认证。本阶段不生成 PLC 程序或真实设备 I/O。
