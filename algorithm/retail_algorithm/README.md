# 智能零售用户行为分析系统 - 算法模块

本项目实现毕业设计中“算法部分”的主路线：

- RFM 用户价值分析
- K-Means 用户分群
- Apriori 商品关联规则
- 热门商品推荐
- 多行为序列增强推荐器（MBA-inspired，PyTorch 可复现实现）

当前实现不依赖 `mlxtend`，Apriori 关联规则为项目内置实现，适合在已有 `rtdetr` conda 环境中直接运行。

## 1. 项目结构

```text
retail_algorithm/
├── configs/
│   └── default.json
├── data/
│   └── sample/
│       ├── behaviors.csv
│       └── orders.csv
├── outputs/
├── src/
│   └── retail_algo/
│       ├── association.py
│       ├── cli.py
│       ├── clustering.py
│       ├── data_io.py
│       ├── multibehavior.py
│       ├── pipeline.py
│       ├── popularity.py
│       └── rfm.py
└── requirements.txt
```

## 2. 运行方式

在项目根目录的上一级执行：

```powershell
conda run -n rtdetr python -m retail_algorithm.src.retail_algo.cli --config retail_algorithm/configs/default.json
```

运行成功后会在 `retail_algorithm/outputs/` 下生成：

- `rfm_segments.csv`
- `cluster_segments.csv`
- `association_rules.csv`
- `popular_recommendations.csv`
- `association_recommendations.csv`
- `multibehavior_recommendations.csv`
- `evaluation_metrics.json`
- `metrics_summary.json`

运行标准库测试：

```powershell
conda run -n rtdetr python -m unittest discover retail_algorithm/tests
```

## 3. 输入数据格式

### behaviors.csv

标准字段：

| 字段 | 说明 |
|---|---|
| customer_id | 用户 ID |
| product_id | 商品 ID |
| behavior_type | 行为类型：view、cart、favorite、purchase |
| behavior_time | 行为时间 |

兼容 RetailRocket 字段：

- `visitorid` -> `customer_id`
- `itemid` -> `product_id`
- `event` -> `behavior_type`
- `timestamp` -> `behavior_time`
- `addtocart` 会自动转换为 `cart`
- `transaction` 会自动转换为 `purchase`

### orders.csv

标准字段：

| 字段 | 说明 |
|---|---|
| order_id | 订单 ID |
| customer_id | 用户 ID |
| product_id | 商品 ID |
| quantity | 商品数量 |
| price | 商品单价 |
| order_time | 下单时间 |

兼容 UCI Online Retail 常见字段：

- `InvoiceNo` / `Invoice` -> `order_id`
- `CustomerID` / `Customer ID` -> `customer_id`
- `StockCode` -> `product_id`
- `InvoiceDate` -> `order_time`
- `UnitPrice` -> `price`

## 4. 真实数据建议

你后续需要准备至少一个真实数据集：

1. RetailRocket E-commerce Dataset  
   https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset

2. UCI Online Retail II  
   https://archive.ics.uci.edu/dataset/502/online+retail+ii

如果只选一个，优先 RetailRocket，因为它最贴合浏览、加购、购买等用户行为分析。

### 使用本地 UCI Online Retail II

你当前的本地文件路径：

```text
E:\EdgeDownload\online+retail+ii\online_retail_II.xlsx
```

由于 `rtdetr` 环境暂时没有 `openpyxl`，建议先用系统默认 Python 转成 CSV：

```powershell
python retail_algorithm/scripts/prepare_uci_online_retail_ii.py
```

转换后会生成：

```text
retail_algorithm/data/uci_online_retail_ii/orders.csv
```

然后使用 `rtdetr` 环境运行算法：

```powershell
conda run -n rtdetr python -m retail_algorithm.src.retail_algo.cli --config retail_algorithm/configs/uci_online_retail_ii.json
```

说明：UCI 配置默认按完整订单抽样约 `5000` 条订单明细用于快速调试，并关闭重复评估训练。论文实验时可将
`configs/uci_online_retail_ii.json` 中的 `sampling.max_order_lines` 调大，并把 `evaluation.enabled`
改为 `true`。

本项目已提供一份论文实验配置：

```powershell
conda run -n rtdetr python -m retail_algorithm.src.retail_algo.cli --config retail_algorithm/configs/uci_online_retail_ii_experiment.json
```

该配置默认按完整订单抽样约 `20000` 条订单明细，并启用推荐评估。输出目录：

```text
retail_algorithm/outputs_uci_experiment
```

### 使用 kagglehub 下载 RetailRocket

如果环境中已经安装 `kagglehub`，可以直接运行：

```powershell
conda run -n rtdetr python retail_algorithm/scripts/download_retailrocket.py
```

脚本内部使用：

```python
import kagglehub

path = kagglehub.dataset_download("retailrocket/ecommerce-dataset")
print("Path to dataset files:", path)
```

如果 `kagglehub 1.0.1` 出现 `get_web_endpoint` 导入错误，本项目下载脚本已做兼容补丁。若下载时出现代理拒绝连接，可在当前 PowerShell 会话临时清空代理：

```powershell
$env:HTTP_PROXY=''
$env:HTTPS_PROXY=''
$env:ALL_PROXY=''
```

如果默认缓存目录没有权限，可把缓存设置到项目目录：

```powershell
$env:KAGGLEHUB_CACHE='C:\Users\a\Documents\Codex\2026-05-28\1-2-3-4\retail_algorithm\.kagglehub_cache'
```

脚本会自动复制 `events.csv` 到：

```text
retail_algorithm/data/retailrocket/events.csv
```

并生成配置文件：

```text
retail_algorithm/configs/retailrocket.json
```

然后运行真实数据版本：

```powershell
conda run -n rtdetr python -m retail_algorithm.src.retail_algo.cli --config retail_algorithm/configs/retailrocket.json
```

当前 RetailRocket 配置默认选取行为次数不少于 10 的前 1000 个活跃用户，并抽样 80000 条行为事件，适合毕业设计实验与答辩演示。

如果 `rtdetr` 环境没有安装 `kagglehub`，先安装：

```powershell
conda run -n rtdetr python -m pip install kagglehub
```

## 5. 关于多行为推荐模块

`multibehavior.py` 不是直接复制 MBA 论文代码，而是为毕业设计系统实现的可复现工程版本：

- 将 view、favorite、cart、purchase 设置为不同强度的兴趣信号
- 使用时间衰减提升近期行为权重
- 使用 PyTorch 训练隐式反馈矩阵分解模型
- 加入用户近期行为产生的 item-to-item 序列增强分数
- 输出 Top-N 推荐商品

如果后续需要严格复现 MBA 论文，请使用官方代码：

https://github.com/snudatalab/MBA

## 6. 评估指标

项目内置时间留一法评估：

- 每个用户最新一次 `purchase` 作为测试目标
- 其余行为作为训练数据
- 对热门推荐和多行为推荐计算 `HitRate@K`、`Recall@K`、`Precision@K`、`Coverage@K`

评估结果保存在：

```text
retail_algorithm/outputs/evaluation_metrics.json
```

## 7. 当前正式实验结果摘要

### UCI Online Retail II

实验配置：

```text
retail_algorithm/configs/uci_online_retail_ii_experiment.json
```

输出目录：

```text
retail_algorithm/outputs_uci_experiment
```

| 算法 | HitRate@10 | HitRate@50 | Coverage@10 | Coverage@50 |
|---|---:|---:|---:|---:|
| 热门推荐 | 0.017287 | 0.081117 | 0.003198 | 0.015990 |
| 多行为推荐 | 0.045213 | 0.125000 | 0.263511 | 0.467541 |

### RetailRocket

实验配置：

```text
retail_algorithm/configs/retailrocket.json
```

输出目录：

```text
retail_algorithm/outputs_retailrocket
```

| 算法 | HitRate@10 | HitRate@50 | Coverage@10 | Coverage@50 |
|---|---:|---:|---:|---:|
| 热门推荐 | 0.018809 | 0.040752 | 0.000351 | 0.001755 |
| 多行为推荐 | 0.213166 | 0.407524 | 0.056736 | 0.180037 |

论文表述建议：在两个公开数据集上，多行为推荐相较热门推荐均取得更高的命中率和推荐覆盖率，说明融合用户历史行为权重和序列转移信息能够提升个性化推荐效果。
