"""Nutanix cloud provider implementation."""

import random
import uuid
from typing import List, Dict, Any
from .base import BaseCloudProvider


class NutanixProvider(BaseCloudProvider):
    """Nutanix private cloud provider implementation."""
    
    NUTANIX_REGIONS = [
        "cluster-1", "cluster-2", "cluster-3",
        "datacenter-a", "datacenter-b", "datacenter-c"
    ]
    
    NUTANIX_VM_SIZES = [
        "small", "medium", "large", "xlarge",
        "2xlarge", "4xlarge"
    ]
    
    STORAGE_CONTAINERS = [
        "container-1", "container-2", "container-3",
        "ssd-pool", "hdd-pool", "hybrid-pool"
    ]
    
    def get_provider_name(self) -> str:
        return "nutanix"
    
    def get_regions(self) -> List[str]:
        return self.NUTANIX_REGIONS.copy()
    
    def generate_host_id(self, service: str, index: int, region: str = None) -> str:
        """Generate Nutanix VM UUID: vm-12345"""
        # Nutanix uses numeric UUIDs
        vm_id = random.randint(10000, 99999)
        return f"vm-{vm_id}"
    
    def format_metric_name(self, metric_type: str) -> str:
        """Format metric name in Nutanix format: nutanix.service.metric"""
        metric_mapping = {
            'system.cpu.util': 'nutanix.vm.cpu.usage',
            'system.mem.util': 'nutanix.vm.memory.usage',
            'net.latency.ms': 'nutanix.vm.network.latency',
            'app.error_rate': 'nutanix.vm.application.errors',
            'app.request_count': 'nutanix.vm.application.requests',
            'net.packet_loss.pct': 'nutanix.vm.network.packet_loss',
            'db.connection_pool.util': 'nutanix.database.connections',
            'resource.pool.util': 'nutanix.resource.pool.usage'
        }
        return metric_mapping.get(metric_type, f"nutanix.vm.{metric_type}")
    
    def generate_metadata(self, host_id: str, service: str, region: str) -> Dict[str, Any]:
        """Generate Nutanix-specific metadata."""
        cluster_name = region
        storage_container = random.choice(self.STORAGE_CONTAINERS)
        
        return {
            "cloud_provider": "nutanix",
            "cluster_name": cluster_name,
            "vm_size": random.choice(self.NUTANIX_VM_SIZES),
            "storage_container": storage_container,
            "vm_uuid": str(uuid.uuid4()),
            "host_uuid": str(uuid.uuid4()),
            "vdisk_uuid": str(uuid.uuid4())
        }

