"""Google Cloud Platform provider implementation."""

import random
import uuid
from typing import List, Dict, Any
from .base import BaseCloudProvider


class GCPProvider(BaseCloudProvider):
    """Google Cloud Platform provider implementation."""
    
    GCP_REGIONS = [
        "us-east1", "us-east4", "us-west1", "us-west2", "us-west3", "us-west4",
        "europe-west1", "europe-west2", "europe-west3", "europe-west4",
        "asia-southeast1", "asia-east1", "asia-northeast1",
        "southamerica-east1", "australia-southeast1"
    ]
    
    GCP_MACHINE_TYPES = [
        "n1-standard-1", "n1-standard-2", "n1-standard-4",
        "e2-small", "e2-medium", "e2-standard-2", "e2-standard-4",
        "n2-standard-2", "n2-standard-4",
        "c2-standard-4", "c2-standard-8"
    ]
    
    GCP_ZONES = ["a", "b", "c", "d", "e", "f"]
    
    def get_provider_name(self) -> str:
        return "gcp"
    
    def get_regions(self) -> List[str]:
        return self.GCP_REGIONS.copy()
    
    def generate_host_id(self, service: str, index: int, region: str = None) -> str:
        """Generate GCP instance ID: instance-123456789"""
        # GCP instance IDs are numeric
        instance_num = random.randint(100000000, 999999999)
        return f"instance-{instance_num}"
    
    def format_metric_name(self, metric_type: str) -> str:
        """Format metric name in GCP format: service/metric/path"""
        metric_mapping = {
            'system.cpu.util': 'compute.googleapis.com/instance/cpu/utilization',
            'system.mem.util': 'compute.googleapis.com/instance/memory/utilization',
            'net.latency.ms': 'loadbalancing.googleapis.com/https/backend_latencies',
            'app.error_rate': 'loadbalancing.googleapis.com/https/backend_request_count',
            'app.request_count': 'compute.googleapis.com/instance/network/received_bytes_count',
            'net.packet_loss.pct': 'compute.googleapis.com/instance/network/received_packets_count',
            'db.connection_pool.util': 'cloudsql.googleapis.com/database/postgresql/database/num_backends',
            'resource.pool.util': 'redis.googleapis.com/stats/connected_clients'
        }
        return metric_mapping.get(metric_type, f"compute.googleapis.com/instance/{metric_type}")
    
    def generate_metadata(self, host_id: str, service: str, region: str) -> Dict[str, Any]:
        """Generate GCP-specific metadata."""
        zone_suffix = random.choice(self.GCP_ZONES)
        zone = f"{region}-{zone_suffix}"
        project_id = f"project-{uuid.uuid4().hex[:8]}"
        
        return {
            "cloud_provider": "gcp",
            "zone": zone,
            "machine_type": random.choice(self.GCP_MACHINE_TYPES),
            "project_id": project_id,
            "instance_name": f"{service}-{uuid.uuid4().hex[:6]}",
            "network": f"network-{uuid.uuid4().hex[:8]}"
        }

