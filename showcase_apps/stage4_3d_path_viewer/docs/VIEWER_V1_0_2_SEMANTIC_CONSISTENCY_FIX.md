# Viewer V1.0.2 轨迹角色与状态语义一致性修复

## 定位

V1.0.2 只修复 Stage4 三维离线 Viewer 的展示语义。它不修改 2503 个正式路径点、坐标、时间戳、`viewer_scene.json` 数据合同或 Stage4.5-R 路径规划结果，也不构成新的运动安全基线。

## 第二次视觉评审问题

V1.0.1 在约 34.8% 进度显示“正在对车轮进行泡沫喷涂”，但扫描点位于车身上方。审计结果如下：

- 播放时间：`894.674115 s`
- 活动段：`844 -> 845`
- 插值系数：`0.352223437`
- 原始两端状态：`foam -> foam`
- 原始两端区域：`wheels -> wheels`
- `surface_task_id`：`repair_state_transition_pre_rinse_to_foam`
- `critical_point_type`：`STATE_BOUNDARY`
- `is_transition`：`true`
- 前一个正式扫描：预冲洗 / 车轮
- 后一个正式扫描：泡沫喷涂 / 车头

该段是高位安全工艺转场。源点保存了目标工艺附近的原始字段，V1.0.1 又把状态转场并入辅助线，并由不同 UI 模块直接读取当前点字段，导致位置、高亮、标签和执行说明语义不一致。坐标和时间戳本身没有错误，无需重写源数据。

## 活动段定义

当播放位置处于 `point[i]` 与 `point[i+1]` 之间时：

- `fromIndex = i`
- `toIndex = i + 1`
- `0 <= alpha < 1`
- 当前语义始终属于该活动段，不在 `alpha >= 0.5` 时提前切换到目标点
- 到达最终时刻后，最终点用于点号和原始字段展示

当前高亮、扫描点、侧栏、执行说明和技术详情都使用同一个活动段。

## 路径角色

`pathRoleClassifier.js` 综合使用 `is_transition`、`scan_pass_id`、`segment_id`、`surface_task_id`、`critical_point_type`、状态变化和区域变化，派生四类角色：

- `MAIN_SCAN`：同一有效 scan pass、状态和区域稳定、不是转场或连接。
- `AUXILIARY_CONNECTION`：scan pass 之间的 patch/local/route connection 或区域定位移动。
- `STATE_TRANSITION`：明确状态切换任务、状态边界或跨工艺转场。
- `UNKNOWN_PATH_ROLE`：证据不足时显式告警，不伪装成正式扫描。

角色只在浏览器运行时派生，不写回正式数据。

## 统一展示上下文

`presentationContext.js` 为每个活动段统一派生：

- 当前角色及置信度
- 工艺状态、区域和动作
- 前后最近正式扫描上下文
- 扫描点两行标签
- 中文执行说明
- 原始字段告警

扫描点、当前段颜色、右侧演示信息和技术详情均消费该对象，不再各自推断。

## 展示规则

### 正式扫描

只有 `MAIN_SCAN` 可以显示“正在对【区域】进行【工艺】”。当前动作为“正式扫描”，扫描点标签显示工艺和区域。

### 辅助移动

`AUXILIARY_CONNECTION` 显示起始与目标区域，或同一区域内的定位移动，并明确“当前不执行持续喷洗”。它不会提前显示目标任务正在清洗。

### 状态切换

`STATE_TRANSITION` 显示“状态切换 / 工艺切换”，说明上一工艺、下一工艺和目标区域，并明确当前不执行持续喷洗。

### 未知角色

`UNKNOWN_PATH_ROLE` 显示“语义待确认 / 路径连接”，技术详情保留 `UNKNOWN_PATH_ROLE` 告警。

## 34.8% 修复结果

- 角色：`STATE_TRANSITION`
- 当前状态：状态切换
- 当前区域：车轮 → 车头
- 当前动作：工艺切换
- 扫描点：状态切换 / 预冲洗 → 泡沫喷涂
- 中文说明：正在完成从预冲洗到泡沫喷涂的切换，并移动至车头，当前不执行持续喷洗
- 高亮段：`844 -> 845`

旧版“正在对车轮进行泡沫喷涂”的正式清洗描述已移除。

## 全路径检查

V1.0.2 对全部 2502 个相邻段执行角色、索引、时间、中文标签、执行说明、状态边界和轻量空间合理性检查：

| 指标 | 结果 |
| --- | ---: |
| total segments | 2502 |
| main scan segments | 1320 |
| auxiliary connection segments | 942 |
| state transition segments | 240 |
| unknown segments | 0 |
| semantic mismatch | 0 |
| spatial warnings | 0 |
| state transition runs | 5 |

空间检查只用于发现 `MAIN_SCAN` 元数据与通用 MPV 包络的明显冲突，不用于改写角色或源数据。

## 其他专项场景

- 0%：预冲洗 / 车顶 / 正式扫描。
- 84%：车轮清洗到风干的状态切换，不提前显示风干正在喷洗。
- 91.3%：正式源数据处于风干工艺、车头区域内的 `PATCH_CONNECTION`，因此显示“辅助移动 / 保持车头”，而不是伪装成正式扫描。
- 五个状态切换区间：切换前保持原工艺，切换中显示状态切换，进入下一正式 scan pass 后才显示新工艺正在执行。

## 数据回归与边界

- source points：2503
- viewer points：2503
- states：7
- zones：6
- path length：328.502099 m
- duration：2570.902629 s
- export warnings：0
- 正式 `viewer_scene.json` 数据未改写

Viewer 仍采用品牌无关的通用 MPV 展示映射，不是真实车型 CAD、标定路径、控制指令或硬件联调界面。
