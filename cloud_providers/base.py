"""Base class for cloud provider implementations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import random


class BaseCloudProvider(ABC):
    """Abstract base class for cloud provider implementations."""
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the cloud provider."""
        pass
    
    @abstractmethod
    def get_regions(self) -> List[str]:
        """Return list of region names for this cloud provider."""
        pass
    
    @abstractmethod
    def generate_host_id(self, service: str, index: int, region: str = None) -> str:
        """Generate cloud-specific host ID.
        
        Args:
            service: Service name
            index: Host index within the service
            region: Optional region name
            
        Returns:
            Cloud-specific host ID string
        """
        pass
    
    @abstractmethod
    def format_metric_name(self, metric_type: str) -> str:
        """Format metric name with cloud-specific prefix.
        
        Args:
            metric_type: Base metric type (e.g., 'cpu.util', 'mem.util')
            
        Returns:
            Cloud-formatted metric name
        """
        pass
    
    @abstractmethod
    def generate_metadata(self, host_id: str, service: str, region: str) -> Dict[str, Any]:
        """Generate cloud-specific metadata for a host.
        
        Args:
            host_id: Generated host ID
            service: Service name
            region: Region name
            
        Returns:
            Dictionary of cloud-specific metadata fields
        """
        pass
    
    def get_random_region(self) -> str:
        """Get a random region from available regions."""
        return random.choice(self.get_regions())
    
    def get_all_metric_types(self) -> Dict[str, str]:
        """Return mapping of metric types to their formatted names."""
        base_metrics = {
            'cpu.util': 'system.cpu.util',
            'mem.util': 'system.mem.util',
            'latency.ms': 'net.latency.ms',
            'error_rate': 'app.error_rate',
            'request_count': 'app.request_count',
            'packet_loss.pct': 'net.packet_loss.pct',
            'db.connection_pool.util': 'db.connection_pool.util',
            'resource.pool.util': 'resource.pool.util'
        }
        return {k: self.format_metric_name(v) for k, v in base_metrics.items()}

