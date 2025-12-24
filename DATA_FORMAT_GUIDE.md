# MELT Data Format Guide

## Overview

The MELT data generator produces **cloud-specific formats** that reflect the actual variety of formats from different cloud providers. This is intentional to simulate real-world hybrid cloud scenarios where different providers use different naming conventions and metadata structures.

## Format Variations by Data Type

### 1. Metrics - Cloud-Specific Formats

**Metrics use cloud-provider-specific naming conventions:**

#### AWS (CloudWatch Format)
```json
{
  "metrics": {
    "AWS/EC2.CPUUtilization": 45.2,
    "CWAgent.MemoryUtilization": 38.5,
    "AWS/ApplicationELB.TargetResponseTime": 25.3,
    "AWS/ApplicationELB.HTTPCode_Target_5XX_Count": 0.1,
    "AWS/ApplicationELB.RequestCount": 250,
    "AWS/EC2.NetworkPacketsOut": 0.0,
    "AWS/RDS.DatabaseConnections": 22.1,
    "AWS/ElastiCache.CurrConnections": 15.8
  }
}
```

#### GCP (Google Cloud Monitoring Format)
```json
{
  "metrics": {
    "compute.googleapis.com/instance/cpu/utilization": 45.2,
    "compute.googleapis.com/instance/memory/utilization": 38.5,
    "loadbalancing.googleapis.com/https/backend_latencies": 25.3,
    "loadbalancing.googleapis.com/https/backend_request_count": 0.1,
    "compute.googleapis.com/instance/network/received_bytes_count": 250,
    "compute.googleapis.com/instance/network/received_packets_count": 0.0,
    "cloudsql.googleapis.com/database/postgresql/database/num_backends": 22.1,
    "redis.googleapis.com/stats/connected_clients": 15.8
  }
}
```

#### Azure (Azure Monitor Format)
```json
{
  "metrics": {
    "Azure/VM.Percentage CPU": 45.2,
    "Azure/VM.Available Memory Bytes": 38.5,
    "Azure/ApplicationGateway.ResponseTime": 25.3,
    "Azure/ApplicationGateway.Http5xx": 0.1,
    "Azure/ApplicationGateway.RequestCount": 250,
    "Azure/VM.Network In": 0.0,
    "Azure/SQL.DatabaseConnections": 22.1,
    "Azure/Redis.CacheConnections": 15.8
  }
}
```

#### On-Premise (Standardized Format)
```json
{
  "metrics": {
    "system.cpu.util": 45.2,
    "system.mem.util": 38.5,
    "net.latency.ms": 25.3,
    "app.error_rate": 0.1,
    "app.request_count": 250,
    "net.packet_loss.pct": 0.0,
    "db.connection_pool.util": 22.1,
    "resource.pool.util": 15.8
  }
}
```

**Key Point**: The same semantic metric (e.g., CPU utilization) has different names across providers:
- AWS: `AWS/EC2.CPUUtilization`
- GCP: `compute.googleapis.com/instance/cpu/utilization`
- Azure: `Azure/VM.Percentage CPU`
- On-premise: `system.cpu.util`

---

### 2. Metadata - Cloud-Specific Fields

Each cloud provider includes different metadata fields:

#### AWS Metadata
```json
{
  "metadata": {
    "availability_zone": "us-east-1b",
    "instance_type": "c5.2xlarge",
    "vpc_id": "vpc-9555d984",
    "subnet_id": "subnet-b354c8b7",
    "instance_id": "i-2af7364b4d91415",
    "ami_id": "ami-bc028ded"
  }
}
```

#### GCP Metadata
```json
{
  "metadata": {
    "zone": "europe-west1-b",
    "machine_type": "e2-medium",
    "project_id": "project-08be26cb",
    "instance_name": "web-frontend-7762fc",
    "network": "network-9550be07"
  }
}
```

#### Azure Metadata
```json
{
  "metadata": {
    "resource_group": "rg-web-frontend-eastus",
    "vm_size": "Standard_D2s_v3",
    "subscription_id": "12345678-1234-1234-1234-123456789012",
    "resource_id": "/subscriptions/.../virtualMachines/vm-abc123def456",
    "availability_set": "aset-12345678"
  }
}
```

#### On-Premise Metadata
```json
{
  "metadata": {
    "rack": "rack-04",
    "datacenter": "on-prem-dc1",
    "physical_server": "server-c260df7a",
    "switch_port": "port-45",
    "power_supply_unit": "psu-A"
  }
}
```

---

### 3. Host IDs - Cloud-Specific Formats

Host IDs follow cloud provider conventions:

- **AWS**: `i-1234567890abcdef0` (EC2 instance ID format)
- **GCP**: `instance-123456789` (numeric instance ID)
- **Azure**: `vm-abc123def456` (VM resource ID format)
- **On-premise**: `host-abc123` (simple host identifier)

---

### 4. Logs - Mostly Standardized with Cloud Metadata

Logs use a **standardized structure** but include cloud-specific metadata:

```json
{
  "timestamp": "2024-06-01T00:00:00",
  "level": "INFO",
  "service": "web-frontend",
  "host": "i-2af7364b4d91415",  // Cloud-specific format
  "cloud_provider": "aws",
  "region": "eu-west-1",
  "trace_id": "7eeaf3ffe0e749358b2a55bd16baec73",
  "message": "Processed request 7eeaf3ffe0e749358b2a55bd16baec73",
  "metadata": {  // Cloud-specific metadata
    "availability_zone": "eu-west-1b",
    "instance_type": "c5.2xlarge",
    // ... cloud-specific fields
  }
}
```

**Standard Fields**: `timestamp`, `level`, `service`, `host`, `cloud_provider`, `region`, `trace_id`, `message`  
**Cloud-Specific**: `metadata` object contains provider-specific fields

---

### 5. Traces - Standardized Structure with Cloud Attributes

Traces follow a **standardized structure** (OpenTelemetry-like) but include cloud-specific attributes:

```json
{
  "trace_id": "7eeaf3ffe0e749358b2a55bd16baec73",
  "span_id": "f2d97324e8f242b482fa398624c41b4a",
  "timestamp": "2024-06-01T00:00:00",
  "service_name": "web-frontend",
  "operation": "GET /api/v1/resource",
  "duration_ms": 39.06,
  "status_code": 200,
  "cloud_provider": "aws",
  "region": "eu-west-1",
  "attributes": {
    "http.method": "GET",
    "host.name": "i-2af7364b4d91415",
    // Cloud-specific attributes prefixed with "cloud."
    "cloud.availability_zone": "eu-west-1b",
    "cloud.instance_type": "c5.2xlarge",
    "cloud.vpc_id": "vpc-9555d984",
    // ... more cloud-specific attributes
  }
}
```

**Standard Fields**: `trace_id`, `span_id`, `timestamp`, `service_name`, `operation`, `duration_ms`, `status_code`  
**Cloud-Specific**: Attributes prefixed with `cloud.*` contain provider-specific metadata

---

### 6. Events - Standardized Format

Events use a **standardized format** across all cloud providers:

```json
{
  "timestamp": "2024-06-01T08:00:00",
  "type": "ALERT_TRIGGER",
  "severity": "CRITICAL",
  "source": "i-2af7364b4d91415",
  "service": "payment-gateway",
  "region": "eu-west-1",
  "incident_id": "819f3dbd-5dc3-4e65-bf83-de33df269e7d",
  "incident_type": "NETWORK_PACKET_LOSS",
  "metric": "packet_loss",
  "message": "Threshold breach: packet_loss exceeded limit"
}
```

**Note**: Events are standardized because they represent application-level events rather than infrastructure metrics.

---

## Summary Table

| Data Type | Format Type | Cloud-Specific Elements |
|-----------|-------------|------------------------|
| **Metrics** | **Cloud-Specific** | Metric names, namespaces, formats |
| **Metadata** | **Cloud-Specific** | All fields are provider-specific |
| **Host IDs** | **Cloud-Specific** | Format varies by provider |
| **Logs** | **Mostly Standardized** | Structure is standard, `metadata` field is cloud-specific |
| **Traces** | **Mostly Standardized** | Structure is standard, `attributes.cloud.*` are cloud-specific |
| **Events** | **Standardized** | Same format across all providers |

---

## Implications for Data Analysis

### When Querying Metrics:

You need to handle different metric names for the same semantic metric:

```python
# Example: Getting CPU utilization across all clouds
def get_cpu_utilization(metric_entry):
    metrics = metric_entry['metrics']
    provider = metric_entry['cloud_provider']
    
    if provider == 'aws':
        return metrics.get('AWS/EC2.CPUUtilization')
    elif provider == 'gcp':
        return metrics.get('compute.googleapis.com/instance/cpu/utilization')
    elif provider == 'azure':
        return metrics.get('Azure/VM.Percentage CPU')
    elif provider == 'onpremise':
        return metrics.get('system.cpu.util')
    return None
```

### When Mapping Metrics:

The generator uses a base metric type internally (e.g., `system.cpu.util`) and converts it to cloud-specific names via `format_metric_name()`. The mapping is:

| Base Metric | AWS | GCP | Azure | On-Premise |
|-------------|-----|-----|-------|------------|
| `system.cpu.util` | `AWS/EC2.CPUUtilization` | `compute.googleapis.com/instance/cpu/utilization` | `Azure/VM.Percentage CPU` | `system.cpu.util` |
| `system.mem.util` | `CWAgent.MemoryUtilization` | `compute.googleapis.com/instance/memory/utilization` | `Azure/VM.Available Memory Bytes` | `system.mem.util` |
| `net.latency.ms` | `AWS/ApplicationELB.TargetResponseTime` | `loadbalancing.googleapis.com/https/backend_latencies` | `Azure/ApplicationGateway.ResponseTime` | `net.latency.ms` |
| `app.error_rate` | `AWS/ApplicationELB.HTTPCode_Target_5XX_Count` | `loadbalancing.googleapis.com/https/backend_request_count` | `Azure/ApplicationGateway.Http5xx` | `app.error_rate` |

---

## Why This Design?

This design reflects **real-world hybrid cloud scenarios** where:

1. **Different providers use different naming conventions** - AWS CloudWatch, GCP Monitoring, and Azure Monitor all have different metric naming schemes
2. **Metadata structures vary** - Each provider tracks different infrastructure metadata
3. **Standardization exists at higher levels** - Logs and traces are more standardized because they represent application-level telemetry
4. **Training realistic models** - Models need to handle this variety to work in real hybrid cloud environments

This makes the dataset more realistic for training root cause analysis models that must work across multiple cloud providers with different formats.

