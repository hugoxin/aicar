# AI无人洗车三维轨迹可视化网页 V1.0.2

这是独立于底层路径算法的离线 Three.js 展示应用。它读取冻结的 Stage4.5-R 连续机器路径，通过 Python 导出统一 `viewer_scene.json`，再显示通用 MPV、完整轨迹、发光扫描点和时间轴动画。

V1.0.1 强化了扫描点、当前执行段、状态聚焦和尾迹，并把辅助连接线降噪。V1.0.2 进一步统一活动段、路径角色和展示上下文，明确区分正式扫描、辅助移动、状态切换和未知角色。语义修复说明见 [docs/VIEWER_V1_0_2_SEMANTIC_CONSISTENCY_FIX.md](docs/VIEWER_V1_0_2_SEMANTIC_CONSISTENCY_FIX.md)。

## 最简启动

双击：

```text
start_viewer.bat
```

脚本会检查 Node/npm、在首次运行时安装本地依赖、导出正式 Stage4.5-R 数据，然后启动：

```text
http://127.0.0.1:4173
```

## 命令行启动

```powershell
cd F:\aicar\showcase_apps\stage4_3d_path_viewer
python tools\export_viewer_scene.py
npm.cmd install
npm.cmd run dev
```

## 检查与构建

```powershell
python tools\check_stage4_3d_viewer.py
npm.cmd run check
npm.cmd run check:semantics
npm.cmd run build
```

## 数据边界

- 正式 V1 数据源是冻结的 Stage4.5-R machine/surface path。
- `viewer_scene.json` 是生成文件，不进入 Git。
- MPV 是品牌无关的通用展示外形，不是 CAD 或实测车型。
- display transform 只用于把冻结路径映射到 MPV 展示包络，不是重新规划或安全验证。
- 页面不连接 PLC、伺服、机器人或真实硬件，也不生成设备控制指令。
- `generate_demo_mpv_scene.py` 仅是开发兜底，数据会明确标记为 `DEMO_SYNTHETIC`。
