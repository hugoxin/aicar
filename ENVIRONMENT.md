# Environment

当前电脑建议使用 Python 3.10。

本阶段暂时不要强制创建虚拟环境，不修改 `PATH`，不自动安装依赖。依赖按子项目拆分，后续需要时再手动安装。

## aicar_sim

依赖文件：

```text
aicar_sim\requirements.txt
```

后续安装方式：

```powershell
python -m pip install -r aicar_sim\requirements.txt
```

当前预留依赖：

- `pygame`
- `pyyaml`

## vehicle_type_lab

依赖文件：

```text
vehicle_type_lab\requirements.txt
```

后续安装方式：

```powershell
python -m pip install -r vehicle_type_lab\requirements.txt
```

当前预留依赖：

- `ultralytics`
- `opencv-python`
- `pyyaml`
- `pillow`

## Notes

本阶段的验收脚本和 scaffold 入口不依赖第三方库，方便先确认目录和基础代码结构。

