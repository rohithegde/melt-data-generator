"""Factory for creating cloud provider instances."""

import json
import os
from typing import Dict, List, Optional, Any
from .base import BaseCloudProvider
from .aws import AWSProvider
from .azure import AzureProvider
from .gcp import GCPProvider
from .openstack import OpenStackProvider
from .nutanix import NutanixProvider
from .vmware import VMwareProvider
from .onpremise import OnPremiseProvider


class CloudConfig:
    """Configuration manager for cloud providers and generation settings."""
    
    SUPPORTED_CLOUDS = ["aws", "azure", "gcp", "openstack", "nutanix", "vmware", "onpremise"]
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize configuration from file or defaults.
        
        Args:
            config_path: Path to configuration JSON file
        """
        self.config_path = config_path
        self.cloud_configs: Dict[str, Dict[str, Any]] = {}
        self.start_date = None
        self.days_to_generate = 365
        self.granularity_minutes = 15
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or use defaults."""
        from datetime import datetime
        
        default_config = {
            "generation": {
                "start_date": "2024-06-01",
                "days_to_generate": 365,
                "granularity_minutes": 15
            },
            "clouds": {
                "aws": {"enabled": False, "regions": ["us-east-1", "eu-west-1"]},
                "azure": {"enabled": False, "regions": ["eastus", "westeurope"]},
                "gcp": {"enabled": False, "regions": ["us-east1", "europe-west1"]},
                "openstack": {"enabled": False, "regions": ["region-one"]},
                "nutanix": {"enabled": False, "regions": ["cluster-1"]},
                "vmware": {"enabled": False, "regions": ["datacenter-1"]},
                "onpremise": {"enabled": True, "regions": ["on-prem-dc1"]}
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    # Merge with defaults, file config takes precedence
                    config = default_config.copy()
                    
                    # Load generation settings
                    if "generation" in file_config:
                        gen_config = file_config["generation"]
                        self.start_date = datetime.strptime(gen_config.get("start_date", default_config["generation"]["start_date"]), "%Y-%m-%d")
                        self.days_to_generate = gen_config.get("days_to_generate", default_config["generation"]["days_to_generate"])
                        self.granularity_minutes = gen_config.get("granularity_minutes", default_config["generation"]["granularity_minutes"])
                    else:
                        self.start_date = datetime.strptime(default_config["generation"]["start_date"], "%Y-%m-%d")
                        self.days_to_generate = default_config["generation"]["days_to_generate"]
                        self.granularity_minutes = default_config["generation"]["granularity_minutes"]
                    
                    # Load cloud settings
                    if "clouds" in file_config:
                        for cloud in self.SUPPORTED_CLOUDS:
                            if cloud in file_config["clouds"]:
                                config["clouds"][cloud].update(file_config["clouds"][cloud])
                    self.cloud_configs = config["clouds"]
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Warning: Error loading config file {self.config_path}: {e}")
                print("Using default configuration.")
                self.cloud_configs = default_config["clouds"]
                self.start_date = datetime.strptime(default_config["generation"]["start_date"], "%Y-%m-%d")
                self.days_to_generate = default_config["generation"]["days_to_generate"]
                self.granularity_minutes = default_config["generation"]["granularity_minutes"]
        else:
            self.cloud_configs = default_config["clouds"]
            self.start_date = datetime.strptime(default_config["generation"]["start_date"], "%Y-%m-%d")
            self.days_to_generate = default_config["generation"]["days_to_generate"]
            self.granularity_minutes = default_config["generation"]["granularity_minutes"]
    
    def is_enabled(self, cloud: str) -> bool:
        """Check if a cloud provider is enabled."""
        return self.cloud_configs.get(cloud, {}).get("enabled", False)
    
    def get_regions(self, cloud: str) -> List[str]:
        """Get regions for a specific cloud."""
        return self.cloud_configs.get(cloud, {}).get("regions", [])
    
    def enable_cloud(self, cloud: str, regions: Optional[List[str]] = None):
        """Enable a cloud provider.
        
        Args:
            cloud: Cloud provider name
            regions: Optional list of regions (uses default if None)
        """
        if cloud not in self.cloud_configs:
            # Initialize with default regions from provider
            provider = CloudProviderFactory.create_provider(cloud)
            default_regions = provider.get_regions()[:2]  # First 2 regions as default
            self.cloud_configs[cloud] = {"enabled": True, "regions": regions or default_regions}
        else:
            self.cloud_configs[cloud]["enabled"] = True
            if regions:
                self.cloud_configs[cloud]["regions"] = regions
    
    def disable_cloud(self, cloud: str):
        """Disable a cloud provider."""
        if cloud in self.cloud_configs:
            self.cloud_configs[cloud]["enabled"] = False
    
    def get_enabled_clouds(self) -> List[str]:
        """Get list of enabled cloud providers."""
        return [cloud for cloud in self.SUPPORTED_CLOUDS if self.is_enabled(cloud)]
    
    def get_all_regions(self) -> List[str]:
        """Get all regions from all enabled clouds."""
        regions = []
        for cloud in self.get_enabled_clouds():
            regions.extend(self.get_regions(cloud))
        return regions


class CloudProviderFactory:
    """Factory for creating cloud provider instances."""
    
    _PROVIDERS = {
        "aws": AWSProvider,
        "azure": AzureProvider,
        "gcp": GCPProvider,
        "openstack": OpenStackProvider,
        "nutanix": NutanixProvider,
        "vmware": VMwareProvider,
        "onpremise": OnPremiseProvider
    }
    
    @classmethod
    def create_provider(cls, cloud_type: str) -> BaseCloudProvider:
        """Create a cloud provider instance.
        
        Args:
            cloud_type: Cloud provider type (aws, azure, gcp, etc.)
            
        Returns:
            BaseCloudProvider instance
            
        Raises:
            ValueError: If cloud_type is not supported
        """
        cloud_type = cloud_type.lower()
        if cloud_type not in cls._PROVIDERS:
            raise ValueError(f"Unsupported cloud type: {cloud_type}. Supported: {list(cls._PROVIDERS.keys())}")
        return cls._PROVIDERS[cloud_type]()
    
    @classmethod
    def create_providers_from_config(cls, config: CloudConfig) -> Dict[str, BaseCloudProvider]:
        """Create provider instances for all enabled clouds.
        
        Args:
            config: CloudConfig instance
            
        Returns:
            Dictionary mapping cloud names to provider instances
        """
        providers = {}
        for cloud in config.get_enabled_clouds():
            providers[cloud] = cls.create_provider(cloud)
        return providers
    
    @classmethod
    def get_provider_for_region(cls, region: str, config: CloudConfig) -> Optional[BaseCloudProvider]:
        """Get the provider instance for a given region.
        
        Args:
            region: Region name
            config: CloudConfig instance
            
        Returns:
            BaseCloudProvider instance or None if region not found
        """
        for cloud in config.get_enabled_clouds():
            if region in config.get_regions(cloud):
                return cls.create_provider(cloud)
        return None

