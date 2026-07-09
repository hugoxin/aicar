# PPT Generation Plan

## 1. PPT标题

AI智能无人洗车仿真系统阶段性成果汇报

## 2. 目标受众

- 客户
- 领导
- 合作方
- 项目组

## 3. 建议页数

建议 12 页。

本轮只准备正式生成前方案，不生成 PPTX。

## 4. 页面结构

### 页1：封面

- 页面标题：AI智能无人洗车仿真系统阶段性成果汇报
- 核心观点：项目已经完成从车辆识别到洗车仿真和可视化展示的软件闭环。
- 推荐图示：Stage3.3 客户展示页首屏截图，或项目链路简图。
- 讲解要点：说明本汇报是阶段性成果，不是最终商用设备发布。

### 页2：行业痛点

- 页面标题：无人洗车研发的核心挑战
- 核心观点：车辆差异、喷嘴布局、流程控制、路径规划和硬件联调都会带来试错成本。
- 推荐图示：痛点卡片，或“直接上硬件”和“先软件仿真”的对比图。
- 讲解要点：强调先做软件闭环可以提前暴露流程和策略问题。

### 页3：项目思路：先软件仿真，再硬件联调

- 页面标题：先把逻辑跑通，再接真实设备
- 核心观点：先用软件验证识别、策略、空间、喷嘴、流程、路径和覆盖，再进入机械/PLC。
- 推荐图示：Stage1 -> Stage2 -> Stage3 -> Stage4/5/6 的路线图。
- 讲解要点：说明当前路线降低硬件试错风险，也方便团队和客户统一认知。

### 页4：系统总体架构

- 页面标题：从车辆图片到洗车仿真的完整链路
- 核心观点：车辆识别结果以 JSON 形式驱动后续洗车策略和仿真模块。
- 推荐图示：输入图片 -> vehicle_type_result.json -> Stage2 六个 JSON -> Stage3 展示页。
- 讲解要点：强调模块边界清楚，后续可以逐步替换成更真实的算法或硬件接口。

### 页5：阶段1：车辆识别

- 页面标题：AI车辆识别小闭环
- 核心观点：系统可以从车辆图片输出车型大类，并传给 aicar_sim 使用。
- 推荐图示：车辆检测框、车辆裁切图、识别结果 JSON 摘要。
- 讲解要点：当前模型是小样本 demo，不代表商业级识别精度。

### 页6：阶段2：洗车仿真主链路

- 页面标题：洗车策略、空间模型、喷嘴覆盖、流程状态机和抽象路径
- 核心观点：阶段2把车型结果转成一组可检查的仿真输出。
- 推荐图示：Stage2 Pipeline Demo 报告截图，或六个 JSON 输出关系图。
- 讲解要点：说明当前是抽象仿真，不是真实机械轨迹，不控制硬件。

### 页7：阶段3：可视化与动画演示

- 页面标题：让仿真结果可看、可讲、可复盘
- 核心观点：阶段3把 JSON 结果变成 2D 可视化、时间轴动画和客户展示页。
- 推荐图示：Stage3 2D 报告、Timeline Animation、Customer Showcase 页面截图。
- 讲解要点：展示层帮助客户理解系统链路，但不改变底层仿真逻辑。

### 页8：当前Demo指标

- 页面标题：当前样例运行结果
- 核心观点：当前样例已完成识别、策略、路径和覆盖率估算闭环。
- 推荐图示：指标卡片。
- 讲解要点：
  - `vehicle_type`: `sedan`
  - `wash_profile`: `standard_sedan`
  - `estimated_total_seconds`: `141`
  - `segment_count`: `22`
  - `point_count`: `112`
  - `estimated_actual_coverage_percent`: `92`
  - `coverage_pass`: `true`

### 页9：客户价值

- 页面标题：从概念到可运行软件原型
- 核心观点：该原型可以降低试错成本，提前验证洗车逻辑，并提高项目表达能力。
- 推荐图示：设备厂商、运营方、研发团队、客户演示四类价值卡片。
- 讲解要点：结合 `CUSTOMER_VALUE_PROPOSITION.md` 说明不同角色的收益。

### 页10：技术边界

- 页面标题：当前能说什么，不能说什么
- 核心观点：当前是软件仿真闭环，不是商用硬件控制系统。
- 推荐图示：“当前可以说 / 当前不能说”双列表格。
- 讲解要点：引用 `TECHNICAL_BOUNDARY_STATEMENT.md`，避免对外夸大。

### 页11：后续路线：阶段4/5/6

- 页面标题：从软件闭环走向真实系统
- 核心观点：后续可进入真实路径规划、PLC/硬件联调和商业化后台。
- 推荐图示：Stage4、Stage5、Stage6 三段路线图。
- 讲解要点：
  - Stage4：真实路径规划与运动约束
  - Stage5：PLC/硬件联调
  - Stage6：商业化后台

### 页12：总结与合作方向

- 页面标题：阶段性成果与后续合作
- 核心观点：当前项目已经具备可运行、可展示、可讲解的软件原型基础。
- 推荐图示：项目成果清单和合作方向清单。
- 讲解要点：建议客户或合作方围绕路径规划、机械联调、PLC接口、商业后台或正式演示材料继续推进。

## 5. 素材来源

- `business_docs\stage3_customer_materials\CUSTOMER_ONE_PAGER.md`
- `business_docs\stage3_customer_materials\CUSTOMER_DEMO_SCRIPT.md`
- `business_docs\stage3_customer_materials\CUSTOMER_PRESENTATION_OUTLINE.md`
- `business_docs\stage3_customer_materials\CUSTOMER_FAQ.md`
- `business_docs\stage3_customer_materials\CUSTOMER_VALUE_PROPOSITION.md`
- `business_docs\stage3_customer_materials\TECHNICAL_BOUNDARY_STATEMENT.md`
- `business_docs\stage3_customer_materials\NEXT_STAGE_ROADMAP.md`
- Stage1 Demo HTML 报告：`demos\stage1_visual_demo\demo_outputs\reports\stage1_demo_report.html`
- Stage2 Demo HTML 报告：`demos\stage2_pipeline_demo\demo_outputs\reports\stage2_pipeline_report.html`
- Stage3 2D Demo HTML 报告：`demos\stage3_2d_visual_demo\demo_outputs\reports\stage3_2d_visual_report.html`
- Stage3 Timeline Demo HTML 报告：`demos\stage3_timeline_animation_demo\demo_outputs\reports\stage3_timeline_animation_report.html`
- Stage3 Customer Showcase HTML 报告：`demos\stage3_customer_showcase_demo\demo_outputs\reports\stage3_customer_showcase_report.html`

## 6. 下一步生成指令建议

下一步如果要正式生成 PPTX，建议先确认：

- 是否需要中文正式商务风格
- 是否需要加入真实截图
- 是否需要公司 Logo、项目 Logo 或客户 Logo
- 是否需要 16:9 宽屏格式
- 是否需要同时导出 PDF

建议下一步命令目标可以定义为：

```text
基于 business_docs\stage3_customer_materials\PPT_GENERATION_PLAN.md 生成 12 页 PPTX，
使用当前 demo HTML 报告作为截图素材来源，
输出到 business_docs\stage3_customer_materials\outputs。
```

## 7. 本轮边界

本轮不生成 PPTX，只准备正式生成前方案。

本轮不新增图片、不下载素材、不修改核心代码、不训练模型、不进入硬件控制。
