"""VMware cloud provider implementation."""

import random
import uuid
from typing import List, Dict, Any
from .base import BaseCloudProvider


class VMwareProvider(BaseCloudProvider):
    """VMware vSphere provider implementation."""
    
    VMWARE_REGIONS = [
        "datacenter-1", "datacenter-2", "datacenter-3",
        "dc-east", "dc-west", "dc-central"
    ]
    
    VMWARE_CLUSTERS = [
        "cluster-1", "cluster-2", "cluster-3",
        "compute-cluster", "storage-cluster"
    ]
    
    RESOURCE_POOLS = [
        "pool-1", "pool-2", "production", "development",
        "staging", "qa"
    ]
    
    def get_provider_name(self) -> str:
        return "vmware"
    
    def get_regions(self) -> List[str]:
        return self.VMWARE_REGIONS.copy()
    
    def generate_host_id(self, service: str, index: int, region: str = None) -> str:
        """Generate VMware vSphere VM ID: vm-123"""
        # VMware uses numeric IDs
        vm_id = random.randint(1, 9999)
        return f"vm-{vm_id}"
    
    def format_metric_name(self, metric_type: str) -> str:
        """Format metric name in VMware format: vmware.service.metric"""
        metric_mapping = {
            'system.cpu.util': 'vmware.vm.cpu.usage',
            'system.mem.util': 'vmware.vm.memory.usage',
            'net.latency.ms': 'vmware.vm.network.latency',
            'app.error_rate': 'vmware.vm.application.errors',
            'app.request_count': 'vmware.vm.application.requests',
            'net.packet_loss.pct': 'vmware.vm.network.packet_loss',
            'db.connection_pool.util': 'vmware.database.connections',
            'resource.pool.util': 'vmware.resource.pool.usage'
        }
        return metric_mapping.get(metric_type, f"vmware.vm.{metric_type}")
    
    def generate_metadata(self, host_id: str, service: str, region: str) -> Dict[str, Any]:
        """Generate VMware-specific metadata."""
        datacenter = region
        cluster = random.choice(self.VMWARE_CLUSTERS)
        resource_pool = random.choice(self.RESOURCE_POOLS)
        
        return {
            "cloud_provider": "vmware",
            "datacenter": datacenter,
            "cluster": cluster,
            "resource_pool": resource_pool,
            "vm_moid": f"vm-{uuid.uuid4()}",
            "host_moid": f"host-{uuid.uuid4()}",
            "datastore": f"datastore-{uuid.uuid4().hex[:8]}"
        }

