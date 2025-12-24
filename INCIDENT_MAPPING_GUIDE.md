# Incident Mapping Guide

This guide explains how to map incidents from `incident_catalog.json` to entries in metrics, events, logs, and traces.

## Overview

Each incident in `incident_catalog.json` has the following key fields:

- `id`: Unique incident identifier
- `type`: Incident type (e.g., "CPU_SATURATION", "MEMORY_LEAK", "NETWORK_PACKET_LOSS")
- `target_host`: Primary host affected
- `target_service`: Primary service affected
- `start_time`: When the incident started
- `end_time`: When the incident ended
- `affected_hosts`: List of all affected host IDs
- `affected_services`: List of all affected service names

## Mapping Strategies

### 1. Events → Incidents (Direct Link)

**Best Method**: Events have direct `incident_id` and `incident_type` fields for incident-related events.

**Event Types with Incident Links:**

- `ALERT_TRIGGER`: Triggered when incident starts
- `CASCADE_TRIGGER`: Triggered when cascading incident starts
- `INCIDENT_UPDATE`: Periodic updates during active incidents
- `INCIDENT_RESOLVED`: When incident ends
- `HEALTH_CHECK`: Health checks during incidents (if service is affected)
- `AUTOSCALE`: Auto-scaling events triggered by incidents
- `SERVICE_RESTART`: Service restarts related to incidents
- `USER_ACTION`: Manual interventions during incidents

**Example Query:**

```python
import json
from datetime import datetime

# Load incident catalog
with open('melt_data/metadata/incident_catalog.json') as f:
    catalog = json.load(f)

incident_id = "819f3dbd-5dc3-4e65-bf83-de33df269e7d"

# Load events for the date range
incident = next(i for i in catalog['incidents'] if i['id'] == incident_id)
start_date = datetime.fromisoformat(incident['start_time'].replace(' ', 'T'))
end_date = datetime.fromisoformat(incident['end_time'].replace(' ', 'T'))

# Find all events linked to this incident
events_file = f"melt_data/events/{start_date.strftime('%Y-%m')}/events_{start_date.strftime('%Y-%m-%d')}.json"
with open(events_file) as f:
    events = json.load(f)

linked_events = [e for e in events if e.get('incident_id') == incident_id]
```

**Fields to Match:**

- `incident_id`: Direct match to incident `id`
- `incident_type`: Matches incident `type`
- `service`: Matches incident `target_service` or `affected_services`
- `timestamp`: Between incident `start_time` and `end_time`

---

### 2. Metrics → Incidents (Time + Host/Service Match)

**Method**: Match by timestamp range, host_id, and service name.

**Key Fields:**

- `timestamp`: Must be between incident `start_time` and `end_time`
- `host_id`: Must be in incident `affected_hosts` list
- `service`: Must be in incident `affected_services` list

**Metric Patterns During Incidents:**

- `CPU_SATURATION`: High CPU utilization (>95%)
- `MEMORY_LEAK`: Increasing memory usage over time
- `DB_CONTENTION`: High database connection pool usage
- `NETWORK_PACKET_LOSS`: Non-zero packet loss percentage
- `DEPENDENCY_DEGRADATION`: High latency, increased error rates
- `NETWORK_PARTITION`: Very high packet loss (>50%), high latency
- `RESOURCE_EXHAUSTION`: High resource pool utilization (>95%)

**Example Query:**

```python
import json
from datetime import datetime

incident_id = "819f3dbd-5dc3-4e65-bf83-de33df269e7d"
incident = next(i for i in catalog['incidents'] if i['id'] == incident_id)

start_time = datetime.fromisoformat(incident['start_time'].replace(' ', 'T'))
end_time = datetime.fromisoformat(incident['end_time'].replace(' ', 'T'))

# Load metrics for the date
metrics_file = f"melt_data/metrics/{start_time.strftime('%Y-%m')}/metrics_{start_time.strftime('%Y-%m-%d')}.json"
with open(metrics_file) as f:
    metrics = json.load(f)

# Filter metrics by time range and affected hosts/services
linked_metrics = [
    m for m in metrics
    if (start_time <= datetime.fromisoformat(m['timestamp']) <= end_time
        and m['host_id'] in incident['affected_hosts']
        and m['service'] in incident['affected_services'])
]
```

**Metric Names to Check:**
The metric names are cloud-provider specific. Check the `metrics` object for:

- CPU: `system.cpu.util` or cloud-specific names (e.g., `AWS/EC2.CPUUtilization`)
- Memory: `system.mem.util` or cloud-specific names
- Latency: `net.latency.ms` or cloud-specific names
- Error Rate: `app.error_rate` or cloud-specific names
- Packet Loss: `net.packet_loss.pct` or cloud-specific names

---

### 3. Logs → Incidents (Time + Host/Service + Trace ID)

**Method**: Match by timestamp, host/service, and optionally trace_id.

**Key Fields:**

- `timestamp`: Between incident `start_time` and `end_time`
- `host`: Matches incident `affected_hosts`
- `service`: Matches incident `affected_services`
- `trace_id`: Can be used to link to traces
- `level`: During incidents, expect more "ERROR" and "WARNING" logs

**Log Patterns During Incidents:**

- `DB_CONTENTION`: "ConnectionPoolTimeoutException: Unable to acquire connection from pool"
- `MEMORY_LEAK`: "java.lang.OutOfMemoryError: Java heap space"
- `NETWORK_PARTITION`: "NetworkException: Connection timeout to upstream service"
- `DEPENDENCY_DEGRADATION`: "UpstreamTimeoutException: Service X did not respond"
- `CASCADING_FAILURE`: "CascadingFailureException: Multiple downstream services unavailable"
- `RESOURCE_EXHAUSTION`: "ResourceExhaustedException: Shared resource pool exhausted"
- `CONFIG_MISMATCH`: "ConfigurationError: Service configuration mismatch detected"
- `CPU_SATURATION`: "CpuSaturationException: CPU utilization exceeded threshold"

**Example Query:**

```python
# Load logs for the date
logs_file = f"melt_data/logs/{start_time.strftime('%Y-%m')}/logs_{start_time.strftime('%Y-%m-%d')}.json"
with open(logs_file) as f:
    logs = json.load(f)

# Filter logs by time range and affected hosts/services
linked_logs = [
    l for l in logs
    if (start_time <= datetime.fromisoformat(l['timestamp']) <= end_time
        and l['host'] in incident['affected_hosts']
        and l['service'] in incident['affected_services'])
]

# Filter for error logs during incident
error_logs = [l for l in linked_logs if l['level'] in ['ERROR', 'WARNING']]
```

---

### 4. Traces → Incidents (Time + Service + Status Code)

**Method**: Match by timestamp, service name, and status codes.

**Key Fields:**

- `timestamp`: Between incident `start_time` and `end_time`
- `service_name`: Matches incident `affected_services`
- `status_code`: During incidents, expect more 500 status codes
- `duration_ms`: Higher durations during incidents
- `attributes.host.name`: Matches incident `affected_hosts`

**Trace Patterns During Incidents:**

- Higher `duration_ms` values (especially for `DEPENDENCY_DEGRADATION`)
- More `status_code: 500` entries
- `trace_id` can link to logs (logs have matching `trace_id`)

**Example Query:**

```python
# Load traces for the date
traces_file = f"melt_data/traces/{start_time.strftime('%Y-%m')}/traces_{start_time.strftime('%Y-%m-%d')}.json"
with open(traces_file) as f:
    traces = json.load(f)

# Filter traces by time range and affected services
linked_traces = [
    t for t in traces
    if (start_time <= datetime.fromisoformat(t['timestamp']) <= end_time
        and t['service_name'] in incident['affected_services'])
]

# Filter for failed traces during incident
failed_traces = [t for t in linked_traces if t['status_code'] == 500]
```

---

## Complete Mapping Example

Here's a complete Python script to map an incident to all related data:

```python
import json
from datetime import datetime
from pathlib import Path

def map_incident_to_data(incident_id, melt_data_dir="melt_data"):
    """Map an incident to all related metrics, events, logs, and traces."""

    # Load incident catalog
    catalog_path = Path(melt_data_dir) / "metadata" / "incident_catalog.json"
    with open(catalog_path) as f:
        catalog = json.load(f)

    # Find the incident
    incident = next(i for i in catalog['incidents'] if i['id'] == incident_id)

    # Parse incident times
    start_time = datetime.fromisoformat(incident['start_time'].replace(' ', 'T'))
    end_time = datetime.fromisoformat(incident['end_time'].replace(' ', 'T'))
    date_str = start_time.strftime('%Y-%m-%d')
    month_str = start_time.strftime('%Y-%m')

    result = {
        'incident': incident,
        'events': [],
        'metrics': [],
        'logs': [],
        'traces': []
    }

    # Load and filter events
    events_path = Path(melt_data_dir) / "events" / month_str / f"events_{date_str}.json"
    if events_path.exists():
        with open(events_path) as f:
            events = json.load(f)
        result['events'] = [
            e for e in events
            if e.get('incident_id') == incident_id
            or (start_time <= datetime.fromisoformat(e['timestamp']) <= end_time
                and e.get('service') in incident['affected_services'])
        ]

    # Load and filter metrics
    metrics_path = Path(melt_data_dir) / "metrics" / month_str / f"metrics_{date_str}.json"
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)
        result['metrics'] = [
            m for m in metrics
            if (start_time <= datetime.fromisoformat(m['timestamp']) <= end_time
                and m['host_id'] in incident['affected_hosts']
                and m['service'] in incident['affected_services'])
        ]

    # Load and filter logs
    logs_path = Path(melt_data_dir) / "logs" / month_str / f"logs_{date_str}.json"
    if logs_path.exists():
        with open(logs_path) as f:
            logs = json.load(f)
        result['logs'] = [
            l for l in logs
            if (start_time <= datetime.fromisoformat(l['timestamp']) <= end_time
                and l['host'] in incident['affected_hosts']
                and l['service'] in incident['affected_services'])
        ]

    # Load and filter traces
    traces_path = Path(melt_data_dir) / "traces" / month_str / f"traces_{date_str}.json"
    if traces_path.exists():
        with open(traces_path) as f:
            traces = json.load(f)
        result['traces'] = [
            t for t in traces
            if (start_time <= datetime.fromisoformat(t['timestamp']) <= end_time
                and t['service_name'] in incident['affected_services'])
        ]

    return result

# Usage
incident_id = "819f3dbd-5dc3-4e65-bf83-de33df269e7d"
mapped_data = map_incident_to_data(incident_id)

print(f"Incident: {mapped_data['incident']['type']}")
print(f"Events: {len(mapped_data['events'])}")
print(f"Metrics: {len(mapped_data['metrics'])}")
print(f"Logs: {len(mapped_data['logs'])}")
print(f"Traces: {len(mapped_data['traces'])}")
```

---

## Summary Table

| Data Type   | Primary Matching Fields           | Secondary Matching Fields                                  |
| ----------- | --------------------------------- | ---------------------------------------------------------- |
| **Events**  | `incident_id` (direct link)       | `timestamp`, `service`, `incident_type`                    |
| **Metrics** | `timestamp`, `host_id`, `service` | Metric values (CPU, memory, latency, errors)               |
| **Logs**    | `timestamp`, `host`, `service`    | `trace_id`, `level` (ERROR/WARNING)                        |
| **Traces**  | `timestamp`, `service_name`       | `status_code` (500), `duration_ms`, `attributes.host.name` |

---

## Tips

1. **Start with Events**: Events have the most direct links via `incident_id`. Use them as the primary correlation mechanism.

2. **Time Windows**: Always filter by the incident's `start_time` and `end_time` range.

3. **Cascading Incidents**: Check `primary_incident_id` in cascading incidents to find related events.

4. **Trace ID Correlation**: Use `trace_id` from logs to find related traces, and vice versa.

5. **Multi-Day Incidents**: If an incident spans multiple days, check all relevant date files.

6. **Service Dependencies**: Check `SERVICE_DEPENDENCIES` in the code to understand which services might be affected by cascading failures.
