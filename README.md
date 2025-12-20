# MELT Data Generator

A comprehensive data generator for creating realistic MELT (Metrics, Events, Logs, Traces) telemetry data for hybrid cloud systems. This tool generates year-long datasets with various incident types, cascading failures, and multi-service dependencies to train root cause analysis models.

## Features

- **Full Year Generation**: Generates 365 days of telemetry data with 15-minute granularity
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
- Generate data for 365 days starting from June 1, 2024
- Save data in daily JSON files organized by month
- Display progress as it generates data
- Create a ground truth catalog with all incidents

### Configuration

You can modify the following constants in `generate_melt_data.py`:

- `DAYS_TO_GENERATE`: Number of days to generate (default: 365)
- `GRANULARITY_MINUTES`: Time interval between data points (default: 15)
- `START_DATE`: Starting date for data generation (default: June 1, 2024)
- `REGIONS`: List of regions in your hybrid cloud (default: us-east-1, eu-west-1, on-prem-dc1)
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

### Data Format

#### Metrics

Each metric entry contains:

- `timestamp`: ISO format timestamp
- `host_id`: Unique host identifier
- `service`: Service name
- `region`: Region name
- `metrics`: Dictionary with system and application metrics
  - `system.cpu.util`: CPU utilization percentage
  - `system.mem.util`: Memory utilization percentage
  - `net.latency.ms`: Network latency in milliseconds
  - `app.error_rate`: Application error rate percentage
  - `app.request_count`: Request count
  - `net.packet_loss.pct`: Packet loss percentage
  - `db.connection_pool.util`: Database connection pool utilization
  - `resource.pool.util`: Shared resource pool utilization

#### Events

Events include:

- Deployment events
- Alert triggers
- Cascade triggers
- Incident resolutions
- Maintenance window notifications

#### Logs

Log entries contain:

- `timestamp`: ISO format timestamp
- `level`: Log level (INFO, WARNING, ERROR)
- `service`: Service name
- `host`: Host identifier
- `trace_id`: Correlated trace ID
- `message`: Log message

#### Traces

Trace entries include:

- `trace_id`: Unique trace identifier
- `span_id`: Span identifier
- `timestamp`: ISO format timestamp
- `service_name`: Service name
- `operation`: API operation
- `duration_ms`: Request duration in milliseconds
- `status_code`: HTTP status code
- `attributes`: Additional trace attributes

#### Ground Truth Catalog

The `incident_catalog.json` file contains:

- Generation configuration
- Complete list of all incidents with:
  - Incident ID and type
  - Affected hosts and services
  - Start and end times
  - Root cause information
  - Cascading relationships
  - Severity levels
- Summary statistics

## Example Output

After running the generator, you'll see progress output like:

```
Starting generation for 365 days...
Granularity: 15 minutes
Total data points per day: 96
Total hosts: 25
------------------------------------------------------------
Completed 2024-06-01 (0.3%) - 1 primary incident(s)
Completed 2024-06-02 (0.5%) - 0 primary incident(s)
...
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
