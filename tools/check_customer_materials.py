from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
MATERIAL_ROOT = WORKSPACE_ROOT / "business_docs" / "stage3_customer_materials"

REQUIRED_PATHS = [
    MATERIAL_ROOT / "README.md",
    MATERIAL_ROOT / "CUSTOMER_ONE_PAGER.md",
    MATERIAL_ROOT / "CUSTOMER_DEMO_SCRIPT.md",
    MATERIAL_ROOT / "CUSTOMER_PRESENTATION_OUTLINE.md",
    MATERIAL_ROOT / "CUSTOMER_FAQ.md",
    MATERIAL_ROOT / "CUSTOMER_VALUE_PROPOSITION.md",
    MATERIAL_ROOT / "TECHNICAL_BOUNDARY_STATEMENT.md",
    MATERIAL_ROOT / "NEXT_STAGE_ROADMAP.md",
    MATERIAL_ROOT / "PPT_GENERATION_PLAN.md",
    WORKSPACE_ROOT / "docs" / "STAGE3_CUSTOMER_MATERIALS_PLAN.md",
]

REQUIRED_CONTENT = {
    MATERIAL_ROOT / "CUSTOMER_ONE_PAGER.md": [
        "vehicle_type",
        "sedan",
        "wash_profile",
        "standard_sedan",
        "coverage_pass",
        "true",
    ],
    MATERIAL_ROOT / "TECHNICAL_BOUNDARY_STATEMENT.md": [
        "当前可以说",
        "当前不能说",
    ],
    MATERIAL_ROOT / "NEXT_STAGE_ROADMAP.md": [
        "阶段4",
        "阶段5",
        "阶段6",
    ],
    MATERIAL_ROOT / "PPT_GENERATION_PLAN.md": [
        "AI智能无人洗车仿真系统阶段性成果汇报",
        "建议 12 页",
        "本轮不生成 PPTX",
    ],
}


def main() -> None:
    missing = [path for path in REQUIRED_PATHS if not path.exists()]
    if missing:
        print("Missing customer materials paths:")
        for path in missing:
            print(f"- {path}")
        raise SystemExit(1)

    for path, tokens in REQUIRED_CONTENT.items():
        text = path.read_text(encoding="utf-8")
        missing_tokens = [token for token in tokens if token not in text]
        if missing_tokens:
            raise SystemExit(f"{path} missing required content: {', '.join(missing_tokens)}")

    print("AI car customer materials check OK")


if __name__ == "__main__":
    main()
