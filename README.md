# MELT Data Generator

A comprehensive data generator for creating realistic MELT (Metrics, Events, Logs, Traces) telemetry data for hybrid cloud systems. This tool generates year-long datasets with various incident types, cascading failures, and multi-service dependencies to train root cause analysis models.

## Features

- **Full Year Generation**: Generates 365 days of telemetry data with 15-minute granularity(configurable)
- **Multiple Incident Types**:
  - Memory leaks
  - Database contention
  - Network packet loss
  - CPU saturation
  - Cascading failures
  - Network partitions
  - Dependency degradation
  - Configuration mismatches
  - Resource exhaustion
- **Realistic Patterns**:
  - Cascading failures across service dependencies
  - Regional network issues affecting multiple services
  - Gradual degradations and recovery patterns
  - Partial outages (some hosts fail while others remain healthy)
  - Maintenance windows with reduced traffic
- **Multi-Service Support**: Service dependency graph with cascading incident propagation
- **Enhanced Ground Truth**: Complete incident catalog with relationships and metadata

## Installation

1. Ensure you have Python 3.8 or higher installed
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Execution

Simply run the generator:

```bash
python generate_melt_data.py
```

The generator will:

- Create a `melt_data/` directory structure
- Generate data for 365 days starting from June 1, 2024(configurable)
- Save data in daily JSON files organized by month
- Display progress as it generates data
- Create a ground truth catalog with all incidents

### Configuration

#### Cloud Provider Configuration

The generator supports multiple cloud providers. All configuration is done via `config.json`.

**Supported Cloud Providers:**

- **Public Clouds**: AWS, Azure, GCP
- **Private Clouds**: OpenStack, Nutanix, VMware
- **On-Premise**: On-premise datacenters

**Using config.json:**

Create or edit `config.json` to configure generation settings, enable/disable clouds, and configure regions:

**Using Command-Line Arguments:**

```bash
# Use default config.json
python generate_melt_data.py
```

All configuration comes from config.json. The only CLI argument is `--config` to specify a different config file.

**Configuration in config.json:**

The `generation` section in config.json controls:

- `start_date`: Starting date for data generation (format: YYYY-MM-DD, default: "2024-06-01")
- `days_to_generate`: Number of days to generate (default: 365)
- `granularity_minutes`: Time interval between data points (default: 15)

**Other Configuration:**

You can modify the following constants in `generate_melt_data.py`:

- `SERVICES`: List of services to simulate (default: web-frontend, auth-service, payment-gateway, inventory-db, recommendation-engine)
- `HOSTS_PER_SERVICE`: Number of hosts per service (default: 5)

### Output Structure

```
melt_data/
├── metrics/
│   └── YYYY-MM/
│       └── metrics_YYYY-MM-DD.json
├── events/
│   └── YYYY-MM/
│       └── events_YYYY-MM-DD.json
├── logs/
│   └── YYYY-MM/
│       └── logs_YYYY-MM-DD.json
├── traces/
│   └── YYYY-MM/
│       └── traces_YYYY-MM-DD.json
└── metadata/
    └── incident_catalog.json
```

## Performance

- Generates data day-by-day to minimize memory usage
- Progress tracking every 100 intervals
- Generation time: ~30-60 seconds for full year (365 days) with 15-minute granularity
- Output size: ~800 MB for full year (uncompressed JSON)
  - Metrics: ~300 MB
  - Traces: ~280 MB
  - Logs: ~195 MB
  - Events: ~10 MB
  - Metadata: <1 MB

## Use Cases

This data generator is designed for:

- Training root cause analysis models
- Testing observability platforms
- Simulating realistic hybrid cloud scenarios
- Research on incident detection and correlation
- Benchmarking anomaly detection algorithms

## License

This project is released into the public domain under the Unlicense - see the [LICENSE](LICENSE) file for details. You can use it however you want without any restrictions or attribution requirements.
