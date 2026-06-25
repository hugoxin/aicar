import argparse
import html
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


DEMO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AICAR_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_IMAGE = DEMO_ROOT / "demo_inputs" / "car_demo.jpg"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".jfif"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the AI car stage1 visual demo.")
    parser.add_argument(
        "--image",
        default=str(DEFAULT_IMAGE.relative_to(DEMO_ROOT)),
        help="Input vehicle image path. Relative paths are resolved from the demo root.",
    )
    parser.add_argument(
        "--aicar-root",
        default=str(DEFAULT_AICAR_ROOT),
        help="AI car workspace root. Defaults to the parent F:\\aicar workspace.",
    )
    parser.add_argument(
        "--output-root",
        default="demo_outputs",
        help="Demo output root. Relative paths are resolved from the demo root.",
    )
    parser.add_argument(
        "--open-report",
        action="store_true",
        help="Open the generated HTML report after completion.",
    )
    return parser


def resolve_path(path_text: str, base: Path) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def ensure_output_dirs(output_root: Path) -> dict[str, Path]:
    dirs = {
        "reports": output_root / "reports",
        "visualized": output_root / "visualized",
        "crops": output_root / "crops",
        "json": output_root / "json",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def copy_image_as_jpg(source: Path, target: Path) -> Path:
    try:
        from PIL import Image, ImageOps

        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.save(target, quality=92)
        return target
    except Exception:
        fallback = target.with_suffix(source.suffix.lower() if source.suffix else ".jpg")
        shutil.copy2(source, fallback)
        return fallback


def copy_if_exists(source: Path, target: Path) -> bool:
    if source.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        return True
    return False


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_vehicle_model(aicar_root: Path, result: dict) -> tuple[Path, dict]:
    vehicle_type = str(result.get("vehicle_type", "unknown")).lower()
    if not result.get("vehicle_detected", False) or vehicle_type not in {"sedan", "suv", "mpv"}:
        vehicle_type = "suv"
    model_path = aicar_root / "aicar_sim" / "data" / "vehicles" / f"{vehicle_type}.json"
    return model_path, load_json(model_path)


def run_classifier(aicar_root: Path, image_path: Path) -> None:
    main_py = aicar_root / "vehicle_type_lab" / "src" / "vehicle_type_lab" / "main.py"
    command = [
        sys.executable,
        str(main_py),
        "--mode",
        "classify",
        "--image",
        str(image_path),
        "--save-history",
    ]
    completed = subprocess.run(
        command,
        cwd=str(aicar_root),
        text=True,
        capture_output=True,
    )
    if completed.stdout.strip():
        print(completed.stdout.strip())
    if completed.stderr.strip():
        print(completed.stderr.strip(), file=sys.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def metric_card(label: str, value: object) -> str:
    return (
        '<div class="metric">'
        f'<div class="metric-label">{html.escape(label)}</div>'
        f'<div class="metric-value">{html.escape(format_value(value))}</div>'
        "</div>"
    )


def image_card(title: str, relative_path: Optional[str], exists: bool) -> str:
    if exists and relative_path:
        body = f'<img src="{html.escape(relative_path)}" alt="{html.escape(title)}">'
    else:
        body = '<div class="missing">未生成</div>'
    return f'<div class="image-card"><h3>{html.escape(title)}</h3>{body}</div>'


def format_value(value: object) -> str:
    if value is None or value == "":
        return "-"
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def table(rows: list[tuple[str, object]]) -> str:
    lines = ["<table>"]
    for key, value in rows:
        lines.append(
            "<tr>"
            f"<th>{html.escape(key)}</th>"
            f"<td>{html.escape(format_value(value))}</td>"
            "</tr>"
        )
    lines.append("</table>")
    return "\n".join(lines)


def render_report(
    template_path: Path,
    report_path: Path,
    result: dict,
    vehicle_model_path: Path,
    vehicle_model: dict,
    copied_images: dict[str, tuple[str | None, bool]],
    input_image: Path,
) -> None:
    template = template_path.read_text(encoding="utf-8")
    generated_at = datetime.now().isoformat(timespec="seconds")

    summary_cards = "\n".join(
        [
            metric_card("运行时间", generated_at),
            metric_card("输入图片", input_image.name),
            metric_card("是否检测到车辆", result.get("vehicle_detected")),
            metric_card("识别车型", result.get("vehicle_type")),
            metric_card("detection_confidence", result.get("detection_confidence")),
            metric_card("classification_confidence", result.get("classification_confidence")),
            metric_card("wash_profile", vehicle_model.get("wash_profile")),
        ]
    )

    image_cards = "\n".join(
        [
            image_card("原始输入图片", *copied_images["input"]),
            image_card("检测 + 分类可视化图", *copied_images["classified"]),
            image_card("车辆裁切图", *copied_images["crop"]),
        ]
    )

    result_table = table(
        [
            ("vehicle_detected", result.get("vehicle_detected")),
            ("vehicle_type", result.get("vehicle_type")),
            ("bbox", result.get("bbox")),
            ("detection_confidence", result.get("detection_confidence")),
            ("classification_confidence", result.get("classification_confidence")),
            ("pipeline_mode", result.get("pipeline_mode")),
            ("model_name", result.get("model_name")),
            ("source_image", result.get("source_image")),
        ]
    )

    model_table = table(
        [
            ("resolved_vehicle_model", vehicle_model_path),
            ("length_mm", vehicle_model.get("length_mm")),
            ("width_mm", vehicle_model.get("width_mm")),
            ("height_mm", vehicle_model.get("height_mm")),
            ("wash_profile", vehicle_model.get("wash_profile")),
        ]
    )

    html_text = (
        template.replace("{{SUMMARY_CARDS}}", summary_cards)
        .replace("{{IMAGE_CARDS}}", image_cards)
        .replace("{{RESULT_TABLE}}", result_table)
        .replace("{{MODEL_TABLE}}", model_table)
    )
    report_path.write_text(html_text, encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    aicar_root = resolve_path(args.aicar_root, Path.cwd())
    output_root = resolve_path(args.output_root, DEMO_ROOT)
    image_path = resolve_path(args.image, DEMO_ROOT)

    if not image_path.exists() or image_path.suffix.lower() not in IMAGE_SUFFIXES:
        print(f"Demo image not found or unsupported: {image_path}")
        print("Put a vehicle image into demo_inputs, for example car_demo.jpg.")
        raise SystemExit(1)

    dirs = ensure_output_dirs(output_root)
    run_classifier(aicar_root, image_path)

    project_result_path = (
        aicar_root / "vehicle_type_lab" / "outputs" / "predictions" / "vehicle_type_result.json"
    )
    if not project_result_path.exists():
        raise SystemExit(f"Missing vehicle type result: {project_result_path}")

    result = load_json(project_result_path)
    demo_result_path = dirs["json"] / "vehicle_type_result.json"
    shutil.copy2(project_result_path, demo_result_path)

    stem = image_path.stem
    project_visualized_path = (
        aicar_root / "vehicle_type_lab" / "outputs" / "predictions" / "visualized" / f"{stem}_classified.jpg"
    )
    crop_path_text = result.get("crop_path") or ""
    project_crop_path = Path(crop_path_text) if crop_path_text else (
        aicar_root / "vehicle_type_lab" / "outputs" / "predictions" / "crops" / f"{stem}_crop.jpg"
    )

    input_target = copy_image_as_jpg(image_path, dirs["visualized"] / "input.jpg")
    classified_ok = copy_if_exists(project_visualized_path, dirs["visualized"] / "classified.jpg")
    crop_ok = copy_if_exists(project_crop_path, dirs["crops"] / "vehicle_crop.jpg")

    vehicle_model_path, vehicle_model = load_vehicle_model(aicar_root, result)
    report_path = dirs["reports"] / "stage1_demo_report.html"
    template_path = DEMO_ROOT / "templates" / "stage1_report_template.html"

    copied_images = {
        "input": (f"../visualized/{input_target.name}", input_target.exists()),
        "classified": ("../visualized/classified.jpg", classified_ok),
        "crop": ("../crops/vehicle_crop.jpg", crop_ok),
    }
    render_report(
        template_path=template_path,
        report_path=report_path,
        result=result,
        vehicle_model_path=vehicle_model_path,
        vehicle_model=vehicle_model,
        copied_images=copied_images,
        input_image=image_path,
    )

    print(f"stage1 demo report saved: {report_path.resolve()}")
    print(f"demo vehicle_type_result saved: {demo_result_path.resolve()}")
    print(f"vehicle_type: {result.get('vehicle_type')}")
    print(f"detection_confidence: {result.get('detection_confidence', '-')}")
    print(f"classification_confidence: {result.get('classification_confidence', '-')}")
    print(f"resolved vehicle model: {vehicle_model_path.resolve()}")
    print(f"wash_profile: {vehicle_model.get('wash_profile')}")

    if args.open_report:
        if os.name == "nt":
            os.startfile(report_path)  # type: ignore[attr-defined]
        else:
            print(f"Open this report manually: {report_path.resolve()}")


if __name__ == "__main__":
    main()
