# Naming Rules

Recommended file name format:

```text
class_source_index.jpg
```

Examples:

```text
sedan_local_0001.jpg
suv_local_0001.jpg
mpv_local_0001.jpg
```

Rules:

- Use English letters, numbers, and underscores only.
- Do not use Chinese characters.
- Do not use spaces.
- Original `incoming` images may use `jpg`, `jpeg`, `png`, `webp`, or `bmp`.
- Standardized `raw` output uses `jpg`.
- Standardized output size defaults to `640x640`.
- Standardized output names use `class_local_0001.jpg`, `class_local_0002.jpg`, and so on.
- Do not commit very large original images to git.

Do not rename or overwrite the original files in `incoming`. The preprocessing script writes new standardized files into `raw`.
