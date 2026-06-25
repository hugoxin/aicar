# Dataset Plan

## Step 1

第一步不用数据集，先用现成 YOLO 检测 `car`，验证输入图片到输出 JSON 的闭环。

## Step 2

做 sedan / SUV / MPV 三分类小样本，重点验证类别定义、标注规则、输出格式和人工复核流程。

## Step 3

研究 Stanford Cars、CompCars、Car-1000 等数据集，评估数据质量、类别粒度、授权方式和是否适合洗车场景。

## Step 4

最终需要采集洗车场景自己的数据，包括不同角度、光照、雨水、污渍、遮挡和车辆停放偏差。

## Current Scope

当前不下载大数据集，只预留 `datasets` 和 `vehicle_type_lab\data` 目录。

