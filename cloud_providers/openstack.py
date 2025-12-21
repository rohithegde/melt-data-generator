"""OpenStack cloud provider implementation."""

import random
import uuid
from typing import List, Dict, Any
from .base import BaseCloudProvider


class OpenStackProvider(BaseCloudProvider):
    """OpenStack cloud provider implementation."""
    
    OPENSTACK_REGIONS = [
        "region-one", "region-two", "region-three",
        "region-a", "region-b", "region-c"
    ]
    
    OPENSTACK_FLAVORS = [
        "m1.tiny", "m1.small", "m1.medium", "m1.large", "m1.xlarge",
        "m2.medium", "m2.large", "m2.xlarge",
        "c1.medium", "c1.large", "c1.xlarge"
    ]
    
    OPENSTACK_AVAILABILITY_ZONES = ["nova", "zone-a", "zone-b", "zone-c"]
    
    def get_provider_name(self) -> str:
        return "openstack"
    
    def get_regions(self) -> List[str]:
        return self.OPENSTACK_REGIONS.copy()
    
    def generate_host_id(self, service: str, index: int, region: str = None) -> str:
        """Generate OpenStack Nova instance UUID: server-abc123"""
        # OpenStack uses UUID format but we'll use a shorter format for readability
        uuid_part = uuid.uuid4().hex[:12]
        return f"server-{uuid_part}"
    
    def format_metric_name(self, metric_type: str) -> str:
        """Format metric name in OpenStack format: openstack.service.metric"""
        metric_mapping = {
            'system.cpu.util': 'openstack.instance.cpu.util',
            'system.mem.util': 'openstack.instance.memory.util',
            'net.latency.ms': 'openstack.lb.response_time',
            'app.error_rate': 'openstack.lb.http_5xx',
            'app.request_count': 'openstack.lb.request_count',
            'net.packet_loss.pct': 'openstack.instance.network.rx_packets',
            'db.connection_pool.util': 'openstack.database.connections',
            'resource.pool.util': 'openstack.cache.connections'
        }
        return metric_mapping.get(metric_type, f"openstack.instance.{metric_type}")
    
    def generate_metadata(self, host_id: str, service: str, region: str) -> Dict[str, Any]:
        """Generate OpenStack-specific metadata."""
        tenant_id = str(uuid.uuid4())
        availability_zone = random.choice(self.OPENSTACK_AVAILABILITY_ZONES)
        
        return {
            "cloud_provider": "openstack",
            "availability_zone": availability_zone,
            "flavor": random.choice(self.OPENSTACK_FLAVORS),
            "tenant_id": tenant_id,
            "instance_uuid": str(uuid.uuid4()),
            "image_id": f"image-{uuid.uuid4().hex[:8]}",
            "hypervisor_hostname": f"hypervisor-{uuid.uuid4().hex[:6]}"
        }

