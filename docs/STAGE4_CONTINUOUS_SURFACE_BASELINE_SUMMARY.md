# Stage4.5 连续清洗面路径基线冻结说明

## 1. 阶段定位

Stage4.5 在 Stage4 运动与安全基线之上，对清洗路径生成源头进行连续表面重构。它解决原抽象路径区域跳转过多、transition 数量高、scan pass 与调度 task 粒度混乱、多个 state 使用相似高密度扫描、patch 连接过于保守，以及整任务共享资源锁造成调度等待传播的问题。

本阶段输出仍是参考解析车辆表面下的离线候选路径和安全约束仿真，不是真实设备控制轨迹。

## 2. 分支与提交历史

Stage4.5 首版：

- branch：`stage4-continuous-surface-path`
- commit：`c6d8d5d`
- 结果：`NO_MEANINGFUL_IMPROVEMENT`

Stage4.5-R：

- branch：`stage4-continuous-surface-path-r`
- repair commit：`dc81d6d`
- baseline comparison fix：`97087e2`
- pre-freeze review fix：`79a833f`
- 最终结果：`ACCEPTED`

首版和修正版分支及提交历史均保留，最终通过 no-ff merge 纳入 `main`。

## 3. 首版失败结果

| 指标 | Stage4.5 首版 |
| --- | ---: |
| scan pass | 140 |
| source path | 524964.237 mm |
| machine path | 529270.070 mm |
| motion duration | 3731.714 s |
| schedule duration | 3880.588 s |
| total delay | 38484.791 s |
| transition | 5 |
| coverage | 100% |

首版虽然明显减少了 transition，但表面扫描、patch connection、任务粒度和共享锁造成总路径及调度退化，因此不能作为冻结基线。

## 4. 根因诊断

首版路径拆分如下：

| 路径组成 | 长度 |
| --- | ---: |
| surface scan | 328697.091 mm |
| local connection | 27974.328 mm |
| patch connection | 148258.583 mm |
| state transition | 24340.068 mm |

诊断结论：

- transition 不是主要长度来源。
- 不同 state 重复使用高密度扫描。
- 140 条 scan pass 造成细粒度任务。
- 45 个下游任务和 97 个资源锁造成等待传播。
- parallel groups 降至 6。
- total delay 增至 38484.791 s。

## 5. 修正版主要方法

Stage4.5-R 对生成链路进行联合修复：

- state-specific pass spacing
- nozzle effective width 读取
- 自适应覆盖率扫描
- scan pass 聚合为 surface route task
- patch 访问顺序和方向优化
- direct patch connection 安全验证
- adaptive safe fallback
- actual shared zone interval
- source span 到 schedule window 比例映射
- 首版 clearance 指标从 validation JSON 读取

## 6. 修正版最终结构

- state：7
- zone：6
- surface patch：9
- wheel patch：4
- scan pass：68
- surface route task：18
- downstream schedule task：23
- transition：5
- resource lock：44

## 7. 三方指标对比

| 指标 | Stage4 冻结基线 | Stage4.5 首版 | Stage4.5-R 最终修正版 |
| --- | ---: | ---: | ---: |
| machine path | 361236.112 mm | 529270.070 mm | 328502.099 mm |
| motion duration | 2870.414 s | 3731.714 s | 2571.102629 s |
| schedule duration | 2339.304 s | 3880.588 s | 2036.403 s |
| total delay | 16920.251 s | 38484.791 s | 10202.551 s |
| transition | 21 | 5 | 5 |
| downstream task | 45 | 45 | 23 |
| resource lock | 91 | 97 | 44 |
| parallel groups | 23 | 6 | 10 |
| minimum clearance | 250 mm | 300 mm | 300 mm |
| clearance warnings | 59 | 45 | 35 |
| violations | 0 | 0 | 0 |

Stage4.5-R 相对 Stage4 冻结基线：machine path 改善 9.062%，motion duration 改善 10.427%，schedule duration 改善约 12.948%，total delay 改善约 39.702%，transition 改善 76.190%，task 改善 48.889%，resource lock 改善 51.648%。

最终冻结数据采用共享资源区间比例映射修复后的 `2036.403 s` schedule duration、`10202.551 s` total delay、10 个 parallel groups 和 `14 -> 0` conflict；预冻结的 `1920.251 s`、`8836.672 s`、11 和 13 不再作为最终指标。

## 8. 安全结果

- motion validation：`PASS_WITH_WARNINGS`
- collision validation：`PASS_WITH_WARNINGS`
- violations：0
- static collision：0
- vehicle collision：0
- forbidden entry：0
- unassigned task：0
- conflict after resolution：0
- unresolved conflict：0
- deadlock：0
- safe-stop：3
- minimum clearance：300 mm
- clearance warnings：35

安全下限仍为 250 mm；本阶段没有删除碰撞检查、车辆禁入区、共享空间互锁或安全停机点。

## 9. 共享区时间映射修复

原实现将源轨迹相对秒数直接加到压缩后的调度窗口，可能把源轨迹后半段共享区间挤压成窗口末端约 1 ms，导致资源锁过短。

最终映射链路为：

```text
source relative interval
        / source span
              |
              v
     normalized interval
              |
              v
adjusted schedule window
```

例如，源区间 `80-90 / 100` 映射到长度为 10 的调度窗口时得到 `8-9 / 10`。无效 source span 使用 `FULL_WINDOW_FALLBACK` 保守锁定完整任务窗口；无效 schedule window 明确抛出 `ValueError`。

最终结果：resource locks 44，反向 lock 0，窗口外 lock 0，conflict `14 -> 0`。

## 10. Direct candidate 统计

- safety rejected：21
- distance policy rejected：4
- total rejected：25
- direct connection：2
- adaptive connection：20
- required state transition：5

25 个 direct candidate rejection 不能全部称为安全拒绝；其中 4 个仅因距离策略被拒绝，adaptive safe fallback 继续保留。

## 11. 覆盖率边界

- unique geometric coverage：100%
- total coverage：100%
- mean surface visits：4.49
- maximum surface visits：6
- overcovered cells：17.88%
- repeated surface scan length：127773.3 mm
- coverage efficiency：约 23.975%

该覆盖率是 50 mm 局部二维解析表面栅格近似，不代表真实清洗效果、真实水流覆盖、真实车辆曲面覆盖或 CFD 结果，也不应把不同工艺 state 的重复访问全部视为无效路径。

## 12. 当前能力边界

当前可以称为：

- 参考解析车辆表面下的连续路径候选
- state-aware continuous-surface candidate path
- 多执行机构离线调度候选
- 完整安全约束仿真结果

当前不能称为：

- 真实车辆 CAD 路径
- 真实点云重建路径
- 真实喷嘴姿态轨迹
- 真实机器人运动轨迹
- 可直接下发 PLC
- 可直接控制真实硬件
- 已达到商业洗车周期
- 已完成真实设备安全认证

## 13. 最终冻结结论

- Stage4.5 首版：`NO_MEANINGFUL_IMPROVEMENT`
- Stage4.5-R：`ACCEPTED`
- Stage4.5 最终基线：`READY_TO_FREEZE`

Stage4.5 连续清洗面路径基线可在完整回归通过后冻结为 `stage4-continuous-surface-baseline`。

## 14. 下一阶段边界

Stage4.6 才能进入 CAD 接口、点云接口、曲面法向、喷嘴姿态、喷嘴角度约束、曲率自适应和真实车辆尺寸替换。本轮不执行 Stage4.6。
