from __future__ import annotations

from typing import Any

from aicar_sim.visualization_2d import esc, text, value


def display(value_item: Any, missing: str = "未提供") -> str:
    if value_item is None or value_item == "":
        return missing
    if isinstance(value_item, bool):
        return "true" if value_item else "false"
    if isinstance(value_item, float):
        return f"{value_item:.4f}".rstrip("0").rstrip(".")
    return str(value_item)


def build_summary(
    vehicle_type_result: dict[str, Any],
    wash_strategy_plan: dict[str, Any],
    wash_flow_run: dict[str, Any],
    abstract_nozzle_path_plan: dict[str, Any],
    coverage_report: dict[str, Any],
) -> dict[str, Any]:
    return {
        "report_version": "stage3.3",
        "vehicle_type": value(
            coverage_report,
            ["vehicle", "vehicle_type"],
            vehicle_type_result.get("vehicle_type", "unknown"),
        ),
        "detection_confidence": vehicle_type_result.get("detection_confidence"),
        "classification_confidence": vehicle_type_result.get("classification_confidence"),
        "wash_profile": value(
            coverage_report,
            ["wash_profile"],
            value(wash_strategy_plan, ["vehicle", "wash_profile"]),
        ),
        "estimated_total_seconds": value(wash_flow_run, ["summary", "estimated_total_seconds"]),
        "state_count": len(wash_flow_run.get("timeline", [])),
        "segment_count": value(abstract_nozzle_path_plan, ["summary", "segment_count"]),
        "point_count": value(abstract_nozzle_path_plan, ["summary", "point_count"]),
        "estimated_actual_coverage_percent": value(
            coverage_report,
            ["coverage_summary", "estimated_actual_coverage_percent"],
        ),
        "coverage_pass": value(coverage_report, ["coverage_summary", "coverage_pass"]),
    }


def metric_card(label: str, item: Any, subtext: str = "") -> str:
    subtitle = f"<span>{esc(subtext)}</span>" if subtext else ""
    return (
        '<div class="metric-card">'
        f'<small>{esc(label)}</small>'
        f'<strong>{esc(display(item))}</strong>'
        f"{subtitle}"
        "</div>"
    )


def capability_cards() -> str:
    items = [
        ("AI 车辆识别", "从图片输出 sedan / suv / mpv / unknown 的标准 JSON。"),
        ("车辆尺寸模型", "把车型映射到 mock 车辆尺寸、wash_profile 和展示参数。"),
        ("洗车策略计划", "按车型生成预冲洗、泡沫、清洗、轮毂和风干策略。"),
        ("洗车房空间模型", "展示车辆 bounding_box、safe_envelope 和 wash bay 边界。"),
        ("喷嘴覆盖参数", "说明每个区域分配哪些喷嘴、建议距离和覆盖目标。"),
        ("洗车流程状态机", "把清洗流程串成可检查的 timeline。"),
        ("抽象喷嘴路径", "为每个状态生成车辆坐标系下的参考路径点。"),
        ("覆盖率评估", "估算各区域覆盖率并输出 pass/fail 结果。"),
        ("2D 可视化与时间轴动画", "把仿真结果包装成可演示的 HTML 页面。"),
    ]
    return "\n".join(
        (
            '<article class="card capability-card">'
            f"<h3>{esc(title)}</h3>"
            f"<p>{esc(desc)}</p>"
            "</article>"
        )
        for title, desc in items
    )


def pipeline_steps() -> str:
    steps = [
        "输入车辆图片",
        "车辆识别",
        "车型 JSON",
        "洗车策略",
        "车辆包络 / 洗车房",
        "喷嘴模型",
        "流程状态机",
        "抽象路径点",
        "覆盖率报告",
        "2D / 时间轴展示",
    ]
    return "\n".join(
        f'<div class="pipeline-step"><span>{index:02d}</span><strong>{esc(step)}</strong></div>'
        for index, step in enumerate(steps, start=1)
    )


def demo_summary_table(summary: dict[str, Any]) -> str:
    rows = [
        ("vehicle_type", summary["vehicle_type"]),
        ("detection_confidence", summary.get("detection_confidence")),
        ("classification_confidence", summary.get("classification_confidence")),
        ("wash_profile", summary["wash_profile"]),
        ("estimated_total_seconds", summary["estimated_total_seconds"]),
        ("state_count", summary["state_count"]),
        ("segment_count", summary["segment_count"]),
        ("point_count", summary["point_count"]),
        ("estimated_actual_coverage_percent", summary["estimated_actual_coverage_percent"]),
        ("coverage_pass", summary["coverage_pass"]),
    ]
    return (
        "<table><tbody>"
        + "".join(
            f"<tr><th>{esc(label)}</th><td>{esc(display(item))}</td></tr>" for label, item in rows
        )
        + "</tbody></table>"
    )


def stage_progress() -> str:
    stages = [
        ("Stage1 Vehicle Recognition", "完成", "车辆检测、裁切、三分类推理和车型 JSON 输出。"),
        ("Stage2 Simulation Pipeline", "完成并冻结", "策略、空间、喷嘴、流程、抽象路径和覆盖率链路。"),
        ("Stage3 Visual Presentation", "完成并冻结", "2D 报告和时间轴动画展示。"),
        ("Stage3.3 Customer Showcase", "当前页面", "把工程 Demo 包装成客户/项目展示页。"),
        ("Stage4 Real Path Planning", "后续", "真实路径规划、运动约束和机构可达性。"),
        ("Stage5 PLC / Hardware", "后续", "PLC、传感器和硬件联调。"),
        ("Stage6 Commercial Platform", "后续", "商业后台、设备管理和运维系统。"),
    ]
    return "\n".join(
        (
            '<article class="stage-card">'
            f"<small>{esc(status)}</small>"
            f"<h3>{esc(title)}</h3>"
            f"<p>{esc(desc)}</p>"
            "</article>"
        )
        for title, status, desc in stages
    )


def bullet_list(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def demo_links() -> str:
    demos = [
        ("Stage1 Visual Demo", r"demos\stage1_visual_demo"),
        ("Stage2 Pipeline Demo", r"demos\stage2_pipeline_demo"),
        ("Stage3 2D Visual Demo", r"demos\stage3_2d_visual_demo"),
        ("Stage3 Timeline Animation Demo", r"demos\stage3_timeline_animation_demo"),
    ]
    return "\n".join(
        f'<div class="demo-entry"><strong>{esc(title)}</strong><code>{esc(path)}</code></div>'
        for title, path in demos
    )


def progress_bar(percent: Any) -> str:
    try:
        pct = max(0, min(100, int(float(percent))))
    except Exception:
        pct = 0
    return (
        '<div class="progress-bar" aria-label="coverage progress">'
        f'<span style="width:{pct}%"></span>'
        f"<em>{pct}%</em>"
        "</div>"
    )


def build_customer_showcase_report(
    vehicle_type_result: dict[str, Any],
    wash_strategy_plan: dict[str, Any],
    space_model_report: dict[str, Any],
    nozzle_coverage_plan: dict[str, Any],
    wash_flow_run: dict[str, Any],
    abstract_nozzle_path_plan: dict[str, Any],
    coverage_report: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    summary = build_summary(
        vehicle_type_result,
        wash_strategy_plan,
        wash_flow_run,
        abstract_nozzle_path_plan,
        coverage_report,
    )
    zone_count = value(coverage_report, ["coverage_summary", "zone_count"])
    nozzle_count = value(nozzle_coverage_plan, ["coverage_summary", "nozzle_count"])
    wash_bay_id = value(space_model_report, ["wash_bay", "wash_bay_id"])

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI 智能无人洗车仿真系统 Demo</title>
  <style>
    :root {{
      --ink: #17202a;
      --muted: #5e6b7a;
      --line: #d9e0ea;
      --panel: #f6f8fb;
      --dark: #10202f;
      --accent: #127c72;
      --accent-2: #315bdc;
      --warm: #d8642a;
      --soft: #eef6f5;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: #ffffff;
      font-family: Arial, "Microsoft YaHei", sans-serif;
      line-height: 1.6;
    }}
    header.hero {{
      min-height: 82vh;
      padding: 42px 48px;
      display: grid;
      align-content: center;
      gap: 28px;
      background:
        linear-gradient(135deg, rgba(16,32,47,.92), rgba(18,124,114,.84)),
        radial-gradient(circle at 72% 22%, rgba(255,255,255,.28), transparent 30%),
        linear-gradient(90deg, #10202f, #174b58);
      color: #fff;
    }}
    .hero h1 {{
      margin: 0;
      font-size: clamp(34px, 5vw, 68px);
      line-height: 1.08;
      max-width: 1100px;
    }}
    .hero p {{
      max-width: 900px;
      margin: 0;
      color: rgba(255,255,255,.84);
      font-size: 19px;
    }}
    .hero-metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 14px;
      max-width: 1100px;
    }}
    .metric-card {{
      border: 1px solid rgba(255,255,255,.22);
      border-radius: 8px;
      background: rgba(255,255,255,.12);
      padding: 16px;
      backdrop-filter: blur(8px);
    }}
    .metric-card small, .metric-card span {{
      display: block;
      color: rgba(255,255,255,.72);
      font-size: 12px;
    }}
    .metric-card strong {{
      display: block;
      margin: 7px 0;
      font-size: 26px;
    }}
    main {{ padding: 36px 48px 58px; }}
    section {{ margin: 0 auto 44px; max-width: 1180px; }}
    h2 {{ margin: 0 0 14px; font-size: 28px; }}
    h3 {{ margin: 0 0 8px; font-size: 17px; }}
    p {{ color: var(--muted); margin-top: 0; }}
    .section-lead {{ max-width: 860px; font-size: 17px; }}
    .card-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 14px;
    }}
    .card, .stage-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 17px;
      box-shadow: 0 10px 26px rgba(16,32,47,.06);
    }}
    .capability-card h3 {{ color: var(--accent); }}
    .pipeline {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 10px;
    }}
    .pipeline-step {{
      min-height: 112px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 14px;
      position: relative;
    }}
    .pipeline-step span {{
      display: inline-grid;
      place-items: center;
      width: 34px;
      height: 34px;
      border-radius: 50%;
      background: var(--accent-2);
      color: #fff;
      font-weight: 700;
      margin-bottom: 12px;
    }}
    .pipeline-step strong {{ display: block; }}
    .two-col {{
      display: grid;
      grid-template-columns: minmax(320px, .9fr) minmax(360px, 1.1fr);
      gap: 18px;
      align-items: start;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 10px;
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: var(--panel); width: 42%; }}
    .progress-bar {{
      height: 34px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      overflow: hidden;
      position: relative;
    }}
    .progress-bar span {{
      display: block;
      height: 100%;
      background: linear-gradient(90deg, var(--accent), #45b49e);
    }}
    .progress-bar em {{
      position: absolute;
      inset: 0;
      display: grid;
      place-items: center;
      font-style: normal;
      font-weight: 700;
    }}
    .stage-card small {{
      display: inline-block;
      margin-bottom: 10px;
      color: #fff;
      background: var(--accent);
      border-radius: 999px;
      padding: 3px 9px;
      font-size: 12px;
    }}
    .value-panels {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }}
    .value-panels .card ul {{ margin-bottom: 0; }}
    li {{ margin: 7px 0; }}
    .boundary {{
      border: 1px solid #efd2be;
      background: #fff8f3;
    }}
    .demo-list {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 12px;
    }}
    .demo-entry {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      background: var(--panel);
    }}
    code {{
      display: block;
      margin-top: 8px;
      color: var(--accent-2);
      word-break: break-all;
    }}
    footer {{
      max-width: 1180px;
      margin: 44px auto 0;
      color: var(--muted);
      font-size: 13px;
    }}
    @media (max-width: 860px) {{
      header.hero, main {{ padding-left: 22px; padding-right: 22px; }}
      .two-col {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header class="hero">
    <div>
      <h1>AI 智能无人洗车仿真系统 Demo</h1>
      <p>从车辆识别到洗车策略、空间建模、喷嘴覆盖、流程状态机、抽象路径和可视化演示的完整软件闭环。</p>
    </div>
    <div class="hero-metrics">
      {metric_card("vehicle_type", summary["vehicle_type"], "AI识别输出")}
      {metric_card("wash_profile", summary["wash_profile"], "洗车策略配置")}
      {metric_card("estimated_total_seconds", summary["estimated_total_seconds"], "流程估算时长")}
      {metric_card("coverage_pass", summary["coverage_pass"], f"estimated coverage {display(summary['estimated_actual_coverage_percent'])}%")}
    </div>
  </header>

  <main>
    <section>
      <h2>当前能力总览</h2>
      <p class="section-lead">这个 Demo 展示的是一个可解释的软件仿真闭环：先识别车辆，再把车型传给洗车仿真链路，最后生成可视化和客户汇报页面。</p>
      <div class="card-grid">{capability_cards()}</div>
    </section>

    <section>
      <h2>完整链路图</h2>
      <p class="section-lead">从一张车图到洗车策略、空间模型、喷嘴、流程、路径、覆盖率，再到 2D 和时间轴展示。</p>
      <div class="pipeline">{pipeline_steps()}</div>
    </section>

    <section class="two-col">
      <div>
        <h2>当前 Demo 数据摘要</h2>
        <p>当前样例基于阶段1识别结果和阶段2仿真输出生成。</p>
        {demo_summary_table(summary)}
      </div>
      <div class="card">
        <h2>覆盖率概览</h2>
        <p>当前覆盖率为规则估算结果，用于展示软件链路是否贯通，不代表真实清洗效果。</p>
        {progress_bar(summary["estimated_actual_coverage_percent"])}
        <p>zone_count: {esc(zone_count)} | nozzle_count: {esc(nozzle_count)} | wash_bay_id: {esc(wash_bay_id)}</p>
      </div>
    </section>

    <section>
      <h2>项目阶段进度</h2>
      <div class="card-grid">{stage_progress()}</div>
    </section>

    <section>
      <h2>业务价值说明</h2>
      <div class="value-panels">
        <article class="card">
          <h3>为什么有价值</h3>
          {bullet_list([
              "提前验证洗车逻辑，减少直接上硬件试错。",
              "让喷嘴布局、流程和覆盖率在软件中可解释。",
              "为机械设计、PLC、真实路径规划和商业系统预留接口。",
              "方便项目汇报、申报、演示和合作沟通。",
          ])}
        </article>
        <article class="card">
          <h3>AI 在哪里发挥作用</h3>
          {bullet_list([
              "通过车辆图片识别车型大类。",
              "将车型结果转成标准 JSON 给仿真链路消费。",
              "让后续策略和模型选择可以按车型差异化执行。",
          ])}
        </article>
      </div>
    </section>

    <section>
      <h2>技术边界说明</h2>
      <div class="value-panels">
        <article class="card">
          <h3>当前已经完成</h3>
          {bullet_list(["软件仿真闭环", "可视化展示", "时间轴演示"])}
        </article>
        <article class="card boundary">
          <h3>当前没有做</h3>
          {bullet_list([
              "真实清洗效果验证",
              "流体仿真",
              "真实机械轨迹",
              "PLC 控制",
              "硬件联调",
              "3D 引擎",
          ])}
        </article>
      </div>
    </section>

    <section>
      <h2>展示入口提示</h2>
      <p class="section-lead">以下 Demo 已在项目中保留，可按需要分别运行。这里仅列出相对路径，不嵌入其它报告。</p>
      <div class="demo-list">{demo_links()}</div>
    </section>

    <section>
      <h2>下一步建议</h2>
      <div class="value-panels">
        <article class="card">
          <h3>A. 客户演示优化</h3>
          {bullet_list(["UI 美化", "中文话术", "图片/视频素材", "演示脚本"])}
        </article>
        <article class="card">
          <h3>B. 技术深化</h3>
          {bullet_list(["Stage4 真实路径规划与运动约束", "Stage5 PLC/硬件联调", "Stage6 商业后台与设备管理"])}
        </article>
      </div>
    </section>

    <footer>
      report_version: stage3.3 | customer showcase layer | generated from Stage1/Stage2/Stage3 local outputs
    </footer>
  </main>
</body>
</html>
"""
    return html_text, summary
