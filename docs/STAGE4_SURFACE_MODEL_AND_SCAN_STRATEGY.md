# Stage4.5 Surface Model and Scan Strategy

## Surface模型

### Roof

车顶使用 `arched_rectangle`。局部u轴跨车宽，v轴沿车长；抛物线拱高只用于参考表面点和法向近似。

### Left / Right Side

左右侧面使用 `vertical_rectangle`。局部u轴沿车长，v轴沿高度，法向分别指向车辆左侧和右侧。

### Front / Rear

前后区域使用 `vertical_rectangle`。局部u轴横向，v轴竖向，法向沿车辆长度方向向外。

### Wheels

四个车轮使用独立 `circular_disk`。每个wheel patch保留独立patch ID、中心、半径和侧向法向。

这些解析面不是CAD、点云或真实车身重建。

## Surface Normal与Standoff

固定平面使用单位法向，arched roof根据解析曲线导数计算近似法向。参考standoff为350 mm，Stage4硬安全距离为250 mm；机械候选点仍需经过workspace、safe envelope和碰撞验证。

当前没有roll、pitch、yaw或真实喷嘴姿态控制。

## Pass Spacing、Overlap和Overscan

- roof pass spacing：220 mm
- side pass spacing：200 mm
- front/rear pass spacing：180 mm
- wheel ring spacing：90 mm

覆盖估算使用现有喷嘴effective width。`overlap = effective_width - pass_spacing`；负值表示潜在gap。Overscan只扩展扫描端点，不改变patch coverage网格边界。

## Boustrophedon与Wheel Rings

矩形patch使用方向交替的往复式扫描。轮面使用同心环，环方向交替。相邻采样点不超过120 mm，最终输出不超过5000点。

## U-turn连接

相邻pass使用局部折线近似U-turn。连接保持在当前参考表面外侧，不回到统一最高安全平面。局部连接仍进入机械和碰撞验证。

## Adaptive Safe Connection

patch间先尝试direct connection。若车辆hard clearance、workspace或静态障碍检查不通过，则根据safe envelope最高点、250 mm硬距离和50 mm connector margin生成adaptive safe connection。无法安全连接时必须记录violation，不能伪造路径。

## Coverage Grid

每个patch建立50 mm二维局部网格。scan path按effective width覆盖格点，生成patch、zone和total coverage及uncovered cell count。

100%栅格覆盖只说明当前离散几何模型被喷幅覆盖，不代表真实清洗效果、流体覆盖、污渍去除或商业质量。

## 当前结果解释

连续扫描减少了required state transition，但重复扫描所有必要surface/state导致总长度和周期退化。下一轮应该从状态级扫描密度和路径任务复用入手，不降低250 mm安全下限、不移除zone、不跳过碰撞或互锁验证。
