# ARM & CloudNet Data Fetcher

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An open-source Python toolkit for automatically downloading global **ARM** (Atmospheric Radiation Measurement) and **CloudNet** cloud radar, lidar, microwave radiometer, and other vertical observation data.

[中文文档](README.zh.md)

---

## Features

- **ARM Data Center** — Download cloud radar (Ka-band), lidar, microwave radiometer, ceilometer, and other products from ARM's global fixed and mobile sites.
- **CloudNet Data Portal** — Fetch standardized cloud radar, lidar, and classification products from ACTRIS CloudNet sites across Europe and beyond.
- **Batch & Date-Range Downloads** — Automatically iterate over date ranges and retry on transient failures.
- **CLI & Python API** — Use from the command line or import into your own scripts.
- **Configurable** — YAML configuration + environment variable overrides.

---

## Supported Data Products

| Source      | Instruments / Products                                           |
|-------------|------------------------------------------------------------------|
| **ARM**     | KAZR, MWRLOS, Ceilometer, Doppler Lidar, HSRL, Raman Lidar, ARSCL |
| **CloudNet**| Radar, Lidar, MWR, Classification, Categorize, Model, IWC, LWC    |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/arm-cloudnet-data-fetcher.git
cd arm-cloudnet-data-fetcher
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install -e .
```

---

## Configuration

Copy the example config and fill in your **ARM token**:

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml`:

```yaml
arm:
  token: "YOUR_ARM_TOKEN_HERE"   # Required for ARM data
  output_dir: "./data/arm"

cloudnet:
  output_dir: "./data/cloudnet"
```

> **ARM Token**: Apply for free at [https://adc.arm.gov/armlive/livedata/home](https://adc.arm.gov/armlive/livedata/home).  
> CloudNet data is open access and does not require a token.

You can also set the token via environment variable:

```bash
export ARM_TOKEN="your_token_here"
```

---

## Quick Start

### Python API

```python
from arm_cloudnet_fetcher import ARMFetcher, CloudNetFetcher

# ----- ARM Example -----
arm = ARMFetcher(token="YOUR_ARM_TOKEN")
files = arm.fetch(
    datastream="nsakazr2C1.a0",   # NSA Ka-band radar
    start_date="2023-01-01",
    end_date="2023-01-03",
)
print(f"Downloaded {len(files)} files")

# ----- CloudNet Example -----
cn = CloudNetFetcher()
files = cn.fetch(
    site="hyytiala",
    start_date="2023-06-01",
    end_date="2023-06-03",
    product="radar",
)
print(f"Downloaded {len(files)} files")
```

### Command Line

After `pip install -e .`:

```bash
# ARM
arm-fetch --datastream nsakazr2C1.a0 --start 2023-01-01 --end 2023-01-03 --token YOUR_TOKEN

# CloudNet
cloudnet-fetch --site hyytiala --start 2023-06-01 --end 2023-06-03 --product radar
```

More examples are in the [`examples/`](examples/) directory.

---

## Project Structure

```
arm-cloudnet-data-fetcher/
├── arm_cloudnet_fetcher/     # Core library
│   ├── __init__.py
│   ├── arm_fetcher.py        # ARM data fetcher
│   ├── cloudnet_fetcher.py   # CloudNet data fetcher
│   ├── config.py             # Configuration manager
│   ├── utils.py              # Utilities (logging, retry, validation)
│   └── cli.py                # Command-line entry points
├── examples/                 # Example scripts
│   ├── fetch_arm_data.py
│   └── fetch_cloudnet_data.py
├── config.yaml.example       # Example configuration
├── requirements.txt
├── setup.py
├── LICENSE
├── README.md                 # This file (English)
└── README.zh.md              # Chinese documentation
```

---

## Supported ARM Sites

| Code | Name                        |
|------|-----------------------------|
| nsa  | North Slope Alaska          |
| sgp  | Southern Great Plains       |
| ena  | Eastern North Atlantic      |
| twpc1| Tropical Western Pacific (Manus) |
| twpc2| Tropical Western Pacific (Nauru) |
| twpc3| Tropical Western Pacific (Darwin) |
| oliktok | Oliktok Point            |

See `ARMFetcher.COMMON_SITES` for the full list.

## Supported CloudNet Sites

| Code | Name                        |
|------|-----------------------------|
| hyytiala | Hyytiala, Finland       |
| juelich  | Julich, Germany         |
| limassol | Limassol, Cyprus        |
| mace-head| Mace Head, Ireland      |
| norunda  | Norunda, Sweden         |
| ny-alesund | Ny-Alesund, Svalbard  |
| palaiseau | Palaiseau, France      |

See `CloudNetFetcher.COMMON_SITES` for the full list.

---

## Data Usage & Citation

- **ARM data**: Please cite the ARM program and follow the [ARM Data Policy](https://www.arm.gov/data/data-policies).
- **CloudNet data**: Part of ACTRIS. Please cite [Illingworth et al., 2007](https://doi.org/10.1175/BAMS-88-6-883) and check individual site requirements.

---

## Contributing

Pull requests are welcome! Please open an issue first to discuss major changes.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Acknowledgements

- [ARM Program](https://www.arm.gov/) — U.S. Department of Energy
- [CloudNet](https://cloudnet.fmi.fi/) — ACTRIS / FMI
