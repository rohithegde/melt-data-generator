"""On-premise datacenter provider implementation."""

import random
import uuid
from typing import List, Dict, Any
from .base import BaseCloudProvider


class OnPremiseProvider(BaseCloudProvider):
    """On-premise datacenter provider implementation."""
    
    ONPREMISE_REGIONS = [
        "on-prem-dc1", "on-prem-dc2", "on-prem-dc3",
        "datacenter-east", "datacenter-west",
        "primary-dc", "secondary-dc"
    ]
    
    RACKS = [
        "rack-01", "rack-02", "rack-03", "rack-04",
        "rack-A1", "rack-A2", "rack-B1", "rack-B2"
    ]
    
    def get_provider_name(self) -> str:
        return "onpremise"
    
    def get_regions(self) -> List[str]:
        return self.ONPREMISE_REGIONS.copy()
    
    def generate_host_id(self, service: str, index: int, region: str = None) -> str:
        """Generate on-premise host ID: host-abc123"""
        # On-premise uses simple host ID format
        hex_part = uuid.uuid4().hex[:6]
        return f"host-{hex_part}"
    
    def format_metric_name(self, metric_type: str) -> str:
        """Format metric name for on-premise (no cloud prefix): system.metric"""
        # On-premise uses simple metric names without cloud prefix
        return metric_type
    
    def generate_metadata(self, host_id: str, service: str, region: str) -> Dict[str, Any]:
        """Generate on-premise-specific metadata."""
        rack = random.choice(self.RACKS)
        datacenter = region
        
        return {
            "cloud_provider": "onpremise",
            "rack": rack,
            "datacenter": datacenter,
            "physical_server": f"server-{uuid.uuid4().hex[:8]}",
            "switch_port": f"port-{random.randint(1, 48)}",
            "power_supply_unit": f"psu-{random.choice(['A', 'B'])}"
        }

