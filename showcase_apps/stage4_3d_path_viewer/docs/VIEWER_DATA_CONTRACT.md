# Viewer Scene 数据合同

生成文件：

```text
public/data/viewer_scene.json
```

## 顶层字段

- `scene_version`: 当前为 `viewer-v1`。
- `generated_at`: UTC ISO 时间。
- `source`: 来源模式、machine/surface 文件、冻结 tag 与 display transform 标记。
- `vehicle`: 通用 MPV 标识、尺寸、比例、`display_only` 与限制。
- `coordinate_system`: 毫米单位及轴语义。
- `display_transform`: 原参考尺寸、三轴缩放、平移与展示用途。
- `display_profile`: 播放、路径、尾迹、相机与显示默认值。
- `path_summary`: 点数、状态、区域、段、时长、路径长度、包络和下采样信息。
- `states` / `zones`: 技术 ID、中文标签和状态颜色。
- `camera_presets`: 斜视、顶视、左右、前后视角。
- `path_points`: 时间排序后的展示轨迹。
- `warnings` / `limitations`: 缺失字段和边界说明。

## Path Point

每个点包含：

- `point_index`
- `source_sequence_index`
- `source_point_index`
- `timestamp_s`
- `relative_time_s`
- `source_position_mm`
- `display_position_mm`
- `state_id` / `state_label_zh`
- `zone_id` / `zone_label_zh`
- `segment_id`
- `scan_pass_id`
- `surface_task_id`
- `critical_point_type`
- `speed_mm_s`
- `is_transition`

源数据没有的字段使用 `null`，不会伪造。时间戳必须单调不下降，显示坐标必须是有限数字。

## Source Mode

- `STAGE4_5_MACHINE_PATH`: V1 正式默认。
- `STAGE4_6_GEOMETRY_POSE`: 仅预留，当前未接入。
- `DEMO_SYNTHETIC`: 开发兜底，页面必须明显提示。

## 下采样

超过上限时必须保留状态边界、transition 和 scan pass 首尾，再对普通中间点均匀抽样；不允许直接截断尾部。
