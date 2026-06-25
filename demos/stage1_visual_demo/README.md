# Stage1 Visual Demo

这是 AI 智能无人洗车阶段1车辆识别可视化 Demo，用于给项目组、客户或合作方展示当前阶段1成果。

## 当前能力

- 输入任意车辆图片
- 自动检测车辆位置
- 裁切车辆区域
- 判断 `sedan` / `suv` / `mpv` / `unknown`
- 输出 `detection_confidence`
- 输出 `classification_confidence`
- 读取车辆模型尺寸
- 显示 `wash_profile`
- 生成 HTML 可视化报告

## 运行方式

```powershell
Set-Location F:\aicar\demos\stage1_visual_demo
python scripts\check_demo.py
```

把车辆图片放入：

```text
demo_inputs\car_demo.jpg
```

运行 Demo：

```powershell
python scripts\run_stage1_demo.py --image demo_inputs\car_demo.jpg --open-report
```

生成结果：

```text
demo_outputs\reports\stage1_demo_report.html
demo_outputs\json\vehicle_type_result.json
demo_outputs\visualized\input.jpg
demo_outputs\visualized\classified.jpg
demo_outputs\crops\vehicle_crop.jpg
```

## 说明

- 当前是本地 Demo。
- 当前模型是小样本 demo。
- 当前结果用于展示阶段1识别链路已跑通，不代表最终商业精度。
- 阶段2 才会进入洗车路径和喷嘴策略。
- `demo_inputs` 和 `demo_outputs` 中的真实图片、报告和 JSON 默认不进入 Git。

