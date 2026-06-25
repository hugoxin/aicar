# 项目目录策略

## 1. 根目录定位

`F:\aicar` 是 AI 智能无人洗车项目的总项目根目录。

以后所有与本项目相关的研发代码、文档、检查脚本、模型说明、数据占位、外部参考、演示材料、实验记录和商业材料，都应统一放在 `F:\aicar` 下面。

不要在 F 盘同级创建 `F:\aicar_stage1_demo` 或其他松散目录。这样可以避免阶段成果分散、备份遗漏、路径引用混乱和后续交接困难。

## 2. 当前目录结构

```text
F:\aicar
├── vehicle_type_lab        # 阶段1车辆识别模块
├── aicar_sim               # 仿真主模块
├── docs                    # 总文档
├── tools                   # 总工具与检查脚本
├── datasets                # 顶层共享数据占位
├── models                  # 顶层共享模型占位
├── external_repos          # 外部开源参考
├── demos                   # 后续对外展示 Demo，当前暂未创建
├── experiments             # 后续实验验证，当前暂未创建
└── business_docs           # 后续商业方案、汇报材料、客户材料，当前暂未创建
```

说明：`demos`、`experiments`、`business_docs` 是后续规划目录，当前暂未创建，不属于阶段1冻结缺陷。

## 3. 当前阶段

- 阶段1已完成车辆识别小闭环。
- 当前暂不创建 Demo。
- Demo 会在阶段1最终修补完成后单独创建。
- 阶段2暂不开始。

阶段1冻结目标是保留一个稳定的识别闭环基线：

```text
test_car.jpg
  -> YOLO 检测
  -> crop
  -> best.pt 分类
  -> vehicle_type_result.json
  -> aicar_sim 车辆模型选择
  -> wash_profile
```

## 4. 目录原则

- 主研发代码放在 `vehicle_type_lab` 和 `aicar_sim`。
- 总文档放在 `docs`。
- 总检查工具放在 `tools`。
- 对外展示材料后续放在 `demos`。
- 临时实验验证后续放在 `experiments`。
- 商业方案、汇报材料和客户材料后续放在 `business_docs`。
- 不在 `F:\aicar` 外面创建散落项目目录。

## 5. 冻结前边界

本目录策略只定义阶段1冻结前的工程组织边界。

当前不执行：

- 不创建 `demos\stage1_visual_demo`。
- 不进入阶段2。
- 不训练模型。
- 不移动或复制 `best.pt`。
- 不初始化 Git。
