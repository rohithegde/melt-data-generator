"""Azure cloud provider implementation."""

import random
import uuid
from typing import List, Dict, Any
from .base import BaseCloudProvider


class AzureProvider(BaseCloudProvider):
    """Azure cloud provider implementation."""
    
    AZURE_REGIONS = [
        "eastus", "eastus2", "westus", "westus2",
        "westeurope", "northeurope", "southeastasia",
        "japaneast", "japanwest", "australiaeast",
        "brazilsouth", "canadacentral", "centralus"
    ]
    
    AZURE_VM_SIZES = [
        "Standard_B1s", "Standard_B2s", "Standard_B2ms",
        "Standard_D2s_v3", "Standard_D4s_v3", "Standard_D8s_v3",
        "Standard_F2s_v2", "Standard_F4s_v2",
        "Standard_E2s_v3", "Standard_E4s_v3"
    ]
    
    def get_provider_name(self) -> str:
        return "azure"
    
    def get_regions(self) -> List[str]:
        return self.AZURE_REGIONS.copy()
    
    def generate_host_id(self, service: str, index: int, region: str = None) -> str:
        """Generate Azure VM resource ID: vm-abc123def456"""
        # Azure resource IDs use lowercase hex
        hex_part = uuid.uuid4().hex[:12]
        return f"vm-{hex_part}"
    
    def format_metric_name(self, metric_type: str) -> str:
        """Format metric name in Azure Monitor format: Azure/Service.MetricName"""
        metric_mapping = {
            'system.cpu.util': 'Azure/VM.Percentage CPU',
            'system.mem.util': 'Azure/VM.Available Memory Bytes',
            'net.latency.ms': 'Azure/ApplicationGateway.ResponseTime',
            'app.error_rate': 'Azure/ApplicationGateway.Http5xx',
            'app.request_count': 'Azure/ApplicationGateway.RequestCount',
            'net.packet_loss.pct': 'Azure/VM.Network In',
            'db.connection_pool.util': 'Azure/SQL.DatabaseConnections',
            'resource.pool.util': 'Azure/Redis.CacheConnections'
        }
        return metric_mapping.get(metric_type, f"Azure/VM.{metric_type}")
    
    def generate_metadata(self, host_id: str, service: str, region: str) -> Dict[str, Any]:
        """Generate Azure-specific metadata."""
        resource_group = f"rg-{service}-{region}"
        subscription_id = str(uuid.uuid4())
        
        return {
            "cloud_provider": "azure",
            "resource_group": resource_group,
            "vm_size": random.choice(self.AZURE_VM_SIZES),
            "subscription_id": subscription_id,
            "resource_id": f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Compute/virtualMachines/{host_id}",
            "availability_set": f"aset-{uuid.uuid4().hex[:8]}" if random.random() < 0.5 else None
        }

