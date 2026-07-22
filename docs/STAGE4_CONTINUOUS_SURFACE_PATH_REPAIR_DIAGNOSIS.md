# Stage4.5-R 连续清洗面路径修复诊断

## 1. 诊断对象

本诊断针对 Stage4.5 第一次实验分支 `stage4-continuous-surface-path`、commit `c6d8d5d371ce7665fc3007f6b5f4a1cc5aac29e8`。该实验安全校验通过，但重构结论为 `NO_MEANINGFUL_IMPROVEMENT`。

Stage4 冻结基线保持不变。Stage4.5 与 Stage4.5-R 均未合并到 `main`。

## 2. 529270.070 mm 路径构成

| 路径类型 | 长度 mm | 占比 |
| --- | ---: | ---: |
| 真正表面扫描 | 328697.091 | 62.10% |
| local U-turn / pass 连接 | 27974.328 | 5.29% |
| patch / zone 连接 | 148258.583 | 28.01% |
| 必要 state transition | 24340.068 | 4.60% |
| 合计 | 529270.070 | 100.00% |

首版的主要问题不仅是 transition，而是表面扫描密度和 patch 连接成本。即使 transition 从 Stage4 的 21 条降到 5 条，扫描与 patch 连接仍使总路径增加。

## 3. 各 state 诊断

| State | Pass | Point | Scan mm | Local mm | Patch mm | Transition mm | Total mm | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pre_rinse | 43 | 1016 | 97303.528 | 5395.164 | 53886.109 | 0 | 156584.801 | 100% |
| foam | 27 | 712 | 80800.000 | 4405.164 | 26588.395 | 3903.139 | 115696.698 | 100% |
| dwell | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0% |
| top_clean | 7 | 182 | 21000.000 | 1445.164 | 0 | 2917.606 | 25362.770 | 100% |
| side_clean | 20 | 530 | 59800.000 | 2960.000 | 20770.730 | 5817.665 | 89348.395 | 100% |
| wheel_clean | 16 | 304 | 16503.528 | 990.000 | 19889.195 | 7408.519 | 44791.242 | 100% |
| air_dry | 27 | 712 | 80800.000 | 4405.164 | 26588.395 | 3903.139 | 115696.698 | 100% |

路径最长的五个状态依次是 `pre_rinse`、`foam`、`air_dry`、`side_clean`、`wheel_clean`。其中 `foam` 与 `air_dry` 使用接近相同的固定扫描密度，未利用喷嘴有效宽度差异。

## 4. 各 patch 重复覆盖

| Patch | 扫描 state 数 | Pass | Scan mm | 平均 spacing mm | Coverage | 平均深度 | 重复次数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| roof_main | 4 | 28 | 84000.000 | 220 | 100% | 4 | 3 |
| left_side_main | 4 | 20 | 87200.000 | 200 | 100% | 4 | 3 |
| right_side_main | 4 | 20 | 87200.000 | 200 | 100% | 4 | 3 |
| front_main | 4 | 20 | 32400.000 | 180 | 100% | 4 | 3 |
| rear_main | 4 | 20 | 32400.000 | 180 | 100% | 4 | 3 |
| left_front_wheel | 2 | 8 | 8251.764 | 90 | 100% | 2 | 1 |
| left_rear_wheel | 2 | 8 | 8251.764 | 90 | 100% | 2 | 1 |
| right_front_wheel | 2 | 8 | 8251.764 | 90 | 100% | 2 | 1 |
| right_rear_wheel | 2 | 8 | 8251.764 | 90 | 100% | 2 | 1 |

重复覆盖最多的五个 patch 是左右侧面、车顶、前部和后部。不同 state 重复经过同一表面具有工艺语义，不能直接删除；真正应降低的是每个 state 内部过密的 pass。

## 5. 调度粒度

| 指标 | 首版 |
| --- | ---: |
| path segment | 43 |
| downstream task | 45 |
| top actuator task | 23 |
| left actuator task | 10 |
| right actuator task | 12 |
| 平均 task duration | 82.018 s |
| resource lock | 97 |
| shared resource 占用总时长 | 7412.196 s |
| parallel groups | 6 |
| total delay | 38484.791 s |

首版把细粒度路径段继续映射为独立调度任务，并按整段任务持有共享区资源。一个冲突产生的等待会传播到同执行器后续任务，45 个任务和 97 个锁将延迟反复放大，parallel groups 因保守整段互锁从 Stage4 的并行水平降到 6。

## 6. 根因结论

1. 多个 state 复用了固定且过密的 zone spacing，没有优先读取喷嘴 `effective_width_mm`。
2. 所有 patch 都达到 100% 覆盖，有限解析几何与密集通道共同造成 state 内部过度覆盖。
3. 22 条 adaptive safe connection 和 0 条 direct connection，使非扫描路径过长。
4. scan pass、路径段和调度 task 概念未充分分离，调度输入过细。
5. 共享资源按整任务持有，扩大了冲突区间和累计延迟。

Stage4.5-R 因此必须同时修复扫描密度、patch 顺序与方向、连接候选、surface task 聚合和实际共享区间，不能只继续压缩 transition。
