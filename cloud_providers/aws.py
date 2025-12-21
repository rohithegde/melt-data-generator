"""AWS cloud provider implementation."""

import random
import uuid
from typing import List, Dict, Any
from .base import BaseCloudProvider


class AWSProvider(BaseCloudProvider):
    """AWS cloud provider implementation."""
    
    AWS_REGIONS = [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1",
        "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
        "sa-east-1", "ca-central-1"
    ]
    
    AWS_INSTANCE_TYPES = [
        "t3.micro", "t3.small", "t3.medium", "t3.large",
        "m5.large", "m5.xlarge", "m5.2xlarge",
        "c5.large", "c5.xlarge", "c5.2xlarge",
        "r5.large", "r5.xlarge"
    ]
    
    AWS_AVAILABILITY_ZONES = ["a", "b", "c", "d"]
    
    def get_provider_name(self) -> str:
        return "aws"
    
    def get_regions(self) -> List[str]:
        return self.AWS_REGIONS.copy()
    
    def generate_host_id(self, service: str, index: int, region: str = None) -> str:
        """Generate AWS EC2 instance ID: i-1234567890abcdef0"""
        # AWS instance IDs are 17 characters: i- followed by 15 hex characters
        hex_part = uuid.uuid4().hex[:15]
        return f"i-{hex_part}"
    
    def format_metric_name(self, metric_type: str) -> str:
        """Format metric name in AWS CloudWatch format: AWS/Service.MetricName"""
        # Map base metrics to AWS CloudWatch namespaces and metric names
        metric_mapping = {
            'system.cpu.util': 'AWS/EC2.CPUUtilization',
            'system.mem.util': 'CWAgent.MemoryUtilization',
            'net.latency.ms': 'AWS/ApplicationELB.TargetResponseTime',
            'app.error_rate': 'AWS/ApplicationELB.HTTPCode_Target_5XX_Count',
            'app.request_count': 'AWS/ApplicationELB.RequestCount',
            'net.packet_loss.pct': 'AWS/EC2.NetworkPacketsOut',
            'db.connection_pool.util': 'AWS/RDS.DatabaseConnections',
            'resource.pool.util': 'AWS/ElastiCache.CurrConnections'
        }
        return metric_mapping.get(metric_type, f"AWS/EC2.{metric_type}")
    
    def generate_metadata(self, host_id: str, service: str, region: str) -> Dict[str, Any]:
        """Generate AWS-specific metadata."""
        az_suffix = random.choice(self.AWS_AVAILABILITY_ZONES)
        availability_zone = f"{region}{az_suffix}"
        
        return {
            "cloud_provider": "aws",
            "availability_zone": availability_zone,
            "instance_type": random.choice(self.AWS_INSTANCE_TYPES),
            "vpc_id": f"vpc-{uuid.uuid4().hex[:8]}",
            "subnet_id": f"subnet-{uuid.uuid4().hex[:8]}",
            "instance_id": host_id,
            "ami_id": f"ami-{uuid.uuid4().hex[:8]}"
        }

