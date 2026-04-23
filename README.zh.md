# ARM & CloudNet 数据自动获取工具

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个开源 Python 工具包，用于自动下载全球 **ARM**（大气辐射测量）和 **CloudNet** 云雷达、激光雷达、微波辐射计及其他垂直观测数据。

[English Documentation](README.md)

---

## 功能特性

- **ARM 数据中心** — 从 ARM 全球固定和移动站点下载云雷达（Ka 波段）、激光雷达、微波辐射计、云高仪等产品。
- **CloudNet 数据门户** — 从欧洲及全球的 ACTRIS CloudNet 站点获取标准化的云雷达、激光雷达和分类产品。
- **批量 & 日期范围下载** — 自动遍历日期范围，并在遇到临时故障时自动重试。
- **命令行 & Python API** — 支持命令行调用或在脚本中导入使用。
- **可配置** — 支持 YAML 配置文件 + 环境变量覆盖。

---

## 支持的数据产品

| 数据源      | 仪器 / 产品                                                      |
|-------------|------------------------------------------------------------------|
| **ARM**     | KAZR、MWRLOS、云高仪、多普勒激光雷达、HSRL、拉曼激光雷达、ARSCL |
| **CloudNet**| 雷达、激光雷达、MWR、分类产品、综合分类、模型、冰水含量、液态水含量 |

---

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/arm-cloudnet-data-fetcher.git
cd arm-cloudnet-data-fetcher
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

或作为包安装：

```bash
pip install -e .
```

---

## 配置

复制示例配置文件并填写你的 **ARM Token**：

```bash
cp config.yaml.example config.yaml
```

编辑 `config.yaml`：

```yaml
arm:
  token: "YOUR_ARM_TOKEN_HERE"   # 获取 ARM 数据必需
  output_dir: "./data/arm"

cloudnet:
  output_dir: "./data/cloudnet"
```

> **ARM Token**：免费申请地址 [https://adc.arm.gov/armlive/livedata/home](https://adc.arm.gov/armlive/livedata/home)。  
> CloudNet 数据为开放获取，不需要 Token。

你也可以通过环境变量设置 Token：

```bash
export ARM_TOKEN="your_token_here"
```

---

## 快速开始

### Python API

```python
from arm_cloudnet_fetcher import ARMFetcher, CloudNetFetcher

# ----- ARM 示例 -----
arm = ARMFetcher(token="YOUR_ARM_TOKEN")
files = arm.fetch(
    datastream="nsakazr2C1.a0",   # NSA Ka 波段雷达
    start_date="2023-01-01",
    end_date="2023-01-03",
)
print(f"下载了 {len(files)} 个文件")

# ----- CloudNet 示例 -----
cn = CloudNetFetcher()
files = cn.fetch(
    site="hyytiala",
    start_date="2023-06-01",
    end_date="2023-06-03",
    product="radar",
)
print(f"下载了 {len(files)} 个文件")
```

### 命令行

执行 `pip install -e .` 后：

```bash
# ARM
arm-fetch --datastream nsakazr2C1.a0 --start 2023-01-01 --end 2023-01-03 --token YOUR_TOKEN

# CloudNet
cloudnet-fetch --site hyytiala --start 2023-06-01 --end 2023-06-03 --product radar
```

更多示例请见 [`examples/`](examples/) 目录。

---

## 项目结构

```
arm-cloudnet-data-fetcher/
├── arm_cloudnet_fetcher/     # 核心库
│   ├── __init__.py
│   ├── arm_fetcher.py        # ARM 数据获取器
│   ├── cloudnet_fetcher.py   # CloudNet 数据获取器
│   ├── config.py             # 配置管理
│   ├── utils.py              # 工具函数（日志、重试、校验）
│   └── cli.py                # 命令行入口
├── examples/                 # 示例脚本
│   ├── fetch_arm_data.py
│   └── fetch_cloudnet_data.py
├── config.yaml.example       # 示例配置文件
├── requirements.txt
├── setup.py
├── LICENSE
├── README.md                 # 英文文档
└── README.zh.md              # 本文档（中文）
```

---

## 支持的 ARM 站点

| 代码 | 名称                        |
|------|-----------------------------|
| nsa  | 阿拉斯加北坡                |
| sgp  | 美国南部大平原              |
| ena  | 北大西洋东部                |
| twpc1| 热带西太平洋（马努斯岛）    |
| twpc2| 热带西太平洋（瑙鲁）        |
| twpc3| 热带西太平洋（达尔文）      |
| oliktok | 奥里克托克角             |

完整列表请查看 `ARMFetcher.COMMON_SITES`。

## 支持的 CloudNet 站点

| 代码 | 名称                        |
|------|-----------------------------|
| hyytiala | 芬兰 海于蒂奥拉           |
| juelich  | 德国 于利希               |
| limassol | 塞浦路斯 利马索尔         |
| mace-head| 爱尔兰 梅斯角             |
| norunda  | 瑞典 诺伦达               |
| ny-alesund | 斯瓦尔巴 新奥勒松       |
| palaiseau | 法国 帕莱索              |

完整列表请查看 `CloudNetFetcher.COMMON_SITES`。

---

## 数据使用与引用

- **ARM 数据**：请引用 ARM 项目，并遵循 [ARM 数据政策](https://www.arm.gov/data/data-policies)。
- **CloudNet 数据**：属于 ACTRIS 项目。请引用 [Illingworth et al., 2007](https://doi.org/10.1175/BAMS-88-6-883) 并查看各站点的具体要求。

---

## 贡献指南

欢迎提交 Pull Request！请先开启 Issue 讨论重大变更。

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

---

## 许可证

本项目采用 MIT 许可证。详情见 [LICENSE](LICENSE)。

---

## 致谢

- [ARM 项目](https://www.arm.gov/) — 美国能源部
- [CloudNet](https://cloudnet.fmi.fi/) — ACTRIS / 芬兰气象研究所
