import os
import json
import uuid
import random
import argparse
import shutil
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from cloud_providers import CloudProviderFactory, CloudConfig

# --- CONFIGURATION ---
# Note: START_DATE, DAYS_TO_GENERATE, and GRANULARITY_MINUTES are now loaded from config.json
BASE_DIR = "melt_data"

# Topology Simulation (REGIONS now comes from cloud config)
SERVICES = ["web-frontend", "auth-service", "payment-gateway", "inventory-db", "recommendation-engine"]
HOSTS_PER_SERVICE = 5

# Service Dependency Graph
SERVICE_DEPENDENCIES = {
    "web-frontend": ["auth-service", "payment-gateway", "recommendation-engine"],
    "payment-gateway": ["inventory-db"],
    "recommendation-engine": ["inventory-db"],
    "auth-service": ["inventory-db"]
}

# --- SCENARIO DEFINITIONS ---
INCIDENT_TYPES = {
    "MEMORY_LEAK": {"metric": "memory_usage", "effect": "ramp_up", "severity": "P3", "cascading_prob": 0.4},
    "DB_CONTENTION": {"metric": "db_connection_pool", "effect": "spike", "severity": "P2", "cascading_prob": 0.8},
    "NETWORK_PACKET_LOSS": {"metric": "packet_loss", "effect": "noise_spike", "severity": "P2", "cascading_prob": 0.3},
    "CPU_SATURATION": {"metric": "cpu_utilization", "effect": "plateau", "severity": "P1", "cascading_prob": 0.5},
    "CASCADING_FAILURE": {"metric": "service_availability", "effect": "cascade", "severity": "P1", "cascading_prob": 0.9},
    "NETWORK_PARTITION": {"metric": "network_connectivity", "effect": "regional", "severity": "P1", "cascading_prob": 1.0},
    "DEPENDENCY_DEGRADATION": {"metric": "upstream_latency", "effect": "gradual", "severity": "P2", "cascading_prob": 0.7},
    "CONFIG_MISMATCH": {"metric": "config_drift", "effect": "intermittent", "severity": "P3", "cascading_prob": 0.2},
    "RESOURCE_EXHAUSTION": {"metric": "resource_pool", "effect": "shared", "severity": "P2", "cascading_prob": 0.6}
}

class MELTGenerator:
    def __init__(self, cloud_config: CloudConfig = None):
        """Initialize MELT generator with cloud configuration.
        
        Args:
            cloud_config: CloudConfig instance. If None, creates default config with onpremise enabled.
        """
        if cloud_config is None:
            cloud_config = CloudConfig()
            # Default to onpremise if no config
            if not cloud_config.get_enabled_clouds():
                cloud_config.enable_cloud("onpremise")
        
        self.cloud_config = cloud_config
        self.providers = CloudProviderFactory.create_providers_from_config(cloud_config)
        self.regions = cloud_config.get_all_regions()
        self.topology = self._build_topology()
        self.incidents = []
        self._prepare_directories()
        self.service_to_hosts = self._build_service_mapping()
        self.region_to_hosts = self._build_region_mapping()
    
    def _build_service_mapping(self):
        """Map service names to their host IDs."""
        mapping = {}
        for node in self.topology:
            service = node['service']
            if service not in mapping:
                mapping[service] = []
            mapping[service].append(node['host_id'])
        return mapping
    
    def _build_region_mapping(self):
        """Map regions to their host IDs."""
        mapping = {}
        for node in self.topology:
            region = node['region']
            if region not in mapping:
                mapping[region] = []
            mapping[region].append(node['host_id'])
        return mapping

    def _prepare_directories(self):
        # Delete existing melt_data folder if it exists
        if os.path.exists(BASE_DIR):
            shutil.rmtree(BASE_DIR)
            print(f"Deleted existing {BASE_DIR} folder")
        
        # Create fresh directory structure
        for dtype in ['metrics', 'events', 'logs', 'traces', 'metadata']:
            os.makedirs(os.path.join(BASE_DIR, dtype), exist_ok=True)

    def _build_topology(self):
        """Build topology using cloud providers for host IDs and regions."""
        topology = []
        for svc in SERVICES:
            for i in range(HOSTS_PER_SERVICE):
                # Select a random region from enabled clouds
                region = random.choice(self.regions)
                
                # Get the provider for this region
                provider = CloudProviderFactory.get_provider_for_region(region, self.cloud_config)
                if provider is None:
                    # Fallback to first available provider
                    provider = list(self.providers.values())[0]
                
                # Generate cloud-specific host ID
                host_id = provider.generate_host_id(svc, i, region)
                
                # Generate cloud-specific metadata
                metadata = provider.generate_metadata(host_id, svc, region)
                
                topology.append({
                    "host_id": host_id,
                    "service": svc,
                    "region": region,
                    "cloud_provider": provider.get_provider_name(),
                    "ip": f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}",
                    **metadata
                })
        return topology

    def generate_incident_schedule(self, current_date):
        """Randomly schedules incidents for the day with cascading failures."""
        daily_incidents = []
        # 25-30% chance of incident per day (more realistic)
        incident_probability = 0.25 + random.random() * 0.05
        
        if random.random() < incident_probability:
            # Choose incident type (weighted towards more complex types)
            incident_weights = {
                "MEMORY_LEAK": 0.15,
                "DB_CONTENTION": 0.15,
                "NETWORK_PACKET_LOSS": 0.10,
                "CPU_SATURATION": 0.10,
                "CASCADING_FAILURE": 0.15,
                "NETWORK_PARTITION": 0.10,
                "DEPENDENCY_DEGRADATION": 0.15,
                "CONFIG_MISMATCH": 0.05,
                "RESOURCE_EXHAUSTION": 0.05
            }
            incident_type = random.choices(
                list(incident_weights.keys()),
                weights=list(incident_weights.values())
            )[0]
            
            # Select target based on incident type
            if incident_type == "NETWORK_PARTITION":
                # Regional incident affects all services in a region
                # Choose from regions that actually have hosts
                available_regions = list(self.region_to_hosts.keys())
                if not available_regions:
                    # Fallback: just pick a random region from config
                    target_region = random.choice(self.regions)
                    # Create empty list for affected hosts (will be populated below)
                    affected_hosts = []
                else:
                    target_region = random.choice(available_regions)
                    affected_hosts = self.region_to_hosts[target_region]
                
                if affected_hosts:
                    primary_host = random.choice(affected_hosts)
                    primary_service = next(n['service'] for n in self.topology if n['host_id'] == primary_host)
                else:
                    # Fallback: pick any host from topology
                    target = random.choice(self.topology)
                    primary_host = target['host_id']
                    primary_service = target['service']
            elif incident_type == "RESOURCE_EXHAUSTION":
                # Affects all services using a shared resource (e.g., database)
                primary_service = "inventory-db"
                primary_host = random.choice(self.service_to_hosts[primary_service])
            else:
                # Single service incident
                target = random.choice(self.topology)
                primary_host = target['host_id']
                primary_service = target['service']
            
            start_hour = random.randint(8, 20)  # Business hours bias
            duration = random.randint(1, 6)  # Longer duration for complex incidents
            
            # Create primary incident
            primary_incident = {
                "id": str(uuid.uuid4()),
                "type": incident_type,
                "target_host": primary_host,
                "target_service": primary_service,
                "start_time": current_date + timedelta(hours=start_hour),
                "end_time": current_date + timedelta(hours=start_hour + duration),
                "root_cause": INCIDENT_TYPES[incident_type],
                "status": "RESOLVED",
                "is_primary": True,
                "affected_hosts": [primary_host],
                "affected_services": [primary_service],
                "cascading_incidents": []
            }
            daily_incidents.append(primary_incident)
            
            # Generate cascading incidents
            cascading_prob = INCIDENT_TYPES[incident_type]["cascading_prob"]
            if random.random() < cascading_prob and primary_service in SERVICE_DEPENDENCIES:
                dependent_services = SERVICE_DEPENDENCIES[primary_service]
                for dep_service in dependent_services:
                    if random.random() < 0.6:  # 60% chance each dependent service is affected
                        cascade_delay = random.randint(1, 4)  # 15-60 minutes delay
                        cascade_host = random.choice(self.service_to_hosts[dep_service])
                        
                        cascade_incident = {
                            "id": str(uuid.uuid4()),
                            "type": "DEPENDENCY_DEGRADATION",
                            "target_host": cascade_host,
                            "target_service": dep_service,
                            "start_time": primary_incident['start_time'] + timedelta(minutes=cascade_delay * 15),
                            "end_time": primary_incident['end_time'] + timedelta(minutes=random.randint(0, 2) * 15),
                            "root_cause": INCIDENT_TYPES["DEPENDENCY_DEGRADATION"],
                            "status": "RESOLVED",
                            "is_primary": False,
                            "primary_incident_id": primary_incident['id'],
                            "affected_hosts": [cascade_host],
                            "affected_services": [dep_service]
                        }
                        daily_incidents.append(cascade_incident)
                        primary_incident['cascading_incidents'].append(cascade_incident['id'])
                        primary_incident['affected_hosts'].append(cascade_host)
                        if dep_service not in primary_incident['affected_services']:
                            primary_incident['affected_services'].append(dep_service)
            
            # Handle regional incidents
            if incident_type == "NETWORK_PARTITION":
                # Get all hosts in the target region
                region_hosts = self.region_to_hosts.get(target_region, [])
                if not region_hosts:
                    # Fallback: get hosts by filtering topology
                    region_hosts = [n['host_id'] for n in self.topology if n['region'] == target_region]
                primary_incident['affected_hosts'] = region_hosts
                primary_incident['affected_services'] = list(set(
                    n['service'] for n in self.topology if n['region'] == target_region
                ))
        
        return daily_incidents

    def _apply_seasonality(self, timestamp):
        """Returns a multiplier (0.5 to 1.5) based on hour of day."""
        hour = timestamp.hour
        # Simple sine wave for business hours peak (9am - 5pm)
        return 1.0 + 0.5 * np.sin((hour - 9) * np.pi / 12)

    def _get_active_incidents(self, timestamp, all_incidents):
        """Get all active incidents at a given timestamp."""
        active = []
        for incident in all_incidents:
            if incident['start_time'] <= timestamp < incident['end_time']:
                active.append(incident)
        return active
    
    def _is_host_affected(self, host_id, active_incidents):
        """Check if a host is affected by any active incident."""
        for incident in active_incidents:
            if host_id in incident.get('affected_hosts', [incident.get('target_host')]):
                return incident
        return None
    
    def _generate_metrics(self, timestamp, active_incidents):
        metrics_batch = []
        seasonality = self._apply_seasonality(timestamp)
        
        # Check for maintenance window (low traffic periods)
        is_maintenance = timestamp.hour >= 2 and timestamp.hour < 5
        maintenance_multiplier = 0.3 if is_maintenance else 1.0

        for node in self.topology:
            # Base Baselines
            cpu = random.gauss(30, 5) * seasonality * maintenance_multiplier
            mem = random.gauss(40, 2)
            latency = random.gauss(20, 5)
            error_rate = 0.1  # Base error rate
            packet_loss = 0.0
            db_connections = random.gauss(20, 5)
            resource_pool_util = random.gauss(30, 10)

            # Check if this host is affected by any incident
            affecting_incident = self._is_host_affected(node['host_id'], active_incidents)
            
            if affecting_incident:
                ic_type = affecting_incident['type']
                elapsed = (timestamp - affecting_incident['start_time']).total_seconds() / 3600
                time_to_end = (affecting_incident['end_time'] - timestamp).total_seconds() / 3600
                
                # Partial outage: only some hosts fail
                if random.random() < 0.7:  # 70% of hosts affected
                    if ic_type == "MEMORY_LEAK":
                        # Gradual degradation
                        mem += (20 * elapsed)
                        latency += (10 * elapsed)
                        if mem > 90:
                            error_rate = 5.0
                            cpu += 20  # GC overhead

                    elif ic_type == "DB_CONTENTION":
                        latency *= 5
                        error_rate = 2.0
                        db_connections = min(100, db_connections * 3)
                        if node['service'] == "inventory-db":
                            cpu += 30

                    elif ic_type == "CPU_SATURATION":
                        cpu = 95 + random.random() * 5
                        latency += 50
                        if cpu > 98:
                            error_rate = 3.0

                    elif ic_type == "NETWORK_PACKET_LOSS":
                        packet_loss = random.gauss(15, 5)
                        latency += packet_loss * 10
                        error_rate = packet_loss / 10

                    elif ic_type == "NETWORK_PARTITION":
                        # Regional network issue (host already identified as affected)
                        packet_loss = random.gauss(50, 10)
                        latency *= 10
                        error_rate = 10.0
                        cpu += 20  # Retry overhead

                    elif ic_type == "DEPENDENCY_DEGRADATION":
                        # Upstream service is slow
                        latency += random.gauss(200, 50)
                        error_rate = 1.5
                        if latency > 500:
                            error_rate = 5.0  # Timeout errors

                    elif ic_type == "CASCADING_FAILURE":
                        # Multiple services failing
                        cpu += 40
                        latency += 100
                        error_rate = 4.0
                        mem += 20

                    elif ic_type == "CONFIG_MISMATCH":
                        # Intermittent failures
                        if random.random() < 0.3:  # 30% of requests fail
                            error_rate = 3.0
                            latency += 100

                    elif ic_type == "RESOURCE_EXHAUSTION":
                        # Shared resource pool exhausted
                        resource_pool_util = 95 + random.random() * 5
                        latency += 150
                        error_rate = 3.0
                        if resource_pool_util > 98:
                            error_rate = 8.0
                
                # Recovery pattern: gradual recovery near end
                if time_to_end < 0.5:  # Last 30 minutes
                    recovery_factor = time_to_end / 0.5
                    error_rate *= recovery_factor
                    latency *= (0.5 + 0.5 * recovery_factor)
                    cpu *= (0.5 + 0.5 * recovery_factor)

            # Clamp values
            cpu = max(0, min(100, cpu))
            mem = max(0, min(100, mem))
            packet_loss = max(0, min(100, packet_loss))
            db_connections = max(0, min(100, db_connections))
            resource_pool_util = max(0, min(100, resource_pool_util))

            # Get cloud provider for this node
            cloud_provider_name = node.get('cloud_provider', 'onpremise')
            provider = self.providers.get(cloud_provider_name)
            if provider is None:
                provider = list(self.providers.values())[0]
            
            # Format metric names using cloud provider
            formatted_metrics = {
                provider.format_metric_name('system.cpu.util'): round(cpu, 2),
                provider.format_metric_name('system.mem.util'): round(mem, 2),
                provider.format_metric_name('net.latency.ms'): round(latency, 2),
                provider.format_metric_name('app.error_rate'): round(error_rate, 2),
                provider.format_metric_name('app.request_count'): int(random.randint(100, 500) * seasonality * maintenance_multiplier),
                provider.format_metric_name('net.packet_loss.pct'): round(packet_loss, 2),
                provider.format_metric_name('db.connection_pool.util'): round(db_connections, 2),
                provider.format_metric_name('resource.pool.util'): round(resource_pool_util, 2)
            }
            
            # Build metric entry with cloud-specific metadata
            metric_entry = {
                "timestamp": timestamp.isoformat(),
                "host_id": node['host_id'],
                "service": node['service'],
                "region": node['region'],
                "cloud_provider": cloud_provider_name,
                "metrics": formatted_metrics
            }
            
            # Add cloud-specific metadata fields
            cloud_metadata = {k: v for k, v in node.items() 
                            if k not in ['host_id', 'service', 'region', 'ip', 'cloud_provider']}
            if cloud_metadata:
                metric_entry["metadata"] = cloud_metadata
            
            metrics_batch.append(metric_entry)
        return metrics_batch

    def _generate_logs_and_traces(self, timestamp, active_incidents):
        logs_batch = []
        traces_batch = []
        
        for node in self.topology:
            # Check if this host is affected by any incident
            affecting_incident = self._is_host_affected(node['host_id'], active_incidents)
            
            # --- TRACES ---
            trace_id = uuid.uuid4().hex
            span_id = uuid.uuid4().hex
            status_code = 200
            duration = random.gauss(50, 10)

            if affecting_incident:
                ic_type = affecting_incident['type']
                # Higher failure rate for more severe incidents
                failure_rate = 0.3
                if ic_type in ["NETWORK_PARTITION", "CASCADING_FAILURE"]:
                    failure_rate = 0.6
                elif ic_type in ["RESOURCE_EXHAUSTION", "DB_CONTENTION"]:
                    failure_rate = 0.5
                
                if random.random() < failure_rate:
                    status_code = 500
                    duration = random.randint(500, 2000)
                    if ic_type == "DEPENDENCY_DEGRADATION":
                        duration = random.randint(1000, 3000)  # Upstream timeout
            
            # Get cloud provider for this node
            cloud_provider_name = node.get('cloud_provider', 'onpremise')
            
            trace = {
                "trace_id": trace_id,
                "span_id": span_id,
                "timestamp": timestamp.isoformat(),
                "service_name": node['service'],
                "operation": "GET /api/v1/resource",
                "duration_ms": duration,
                "status_code": status_code,
                "cloud_provider": cloud_provider_name,
                "region": node['region'],
                "attributes": {
                    "http.method": "GET",
                    "host.name": node['host_id']
                }
            }
            # Add cloud-specific metadata to attributes
            cloud_metadata = {k: v for k, v in node.items() 
                            if k not in ['host_id', 'service', 'region', 'ip', 'cloud_provider']}
            if cloud_metadata:
                trace["attributes"].update({f"cloud.{k}": v for k, v in cloud_metadata.items()})
            
            traces_batch.append(trace)

            # --- LOGS ---
            log_level = "INFO"
            msg = f"Processed request {trace_id}"
            
            if status_code == 500 and affecting_incident:
                log_level = "ERROR"
                ic_type = affecting_incident['type']
                
                if ic_type == "DB_CONTENTION":
                    msg = "ConnectionPoolTimeoutException: Unable to acquire connection from pool"
                elif ic_type == "MEMORY_LEAK":
                    msg = "java.lang.OutOfMemoryError: Java heap space"
                elif ic_type == "NETWORK_PARTITION":
                    msg = "NetworkException: Connection timeout to upstream service"
                elif ic_type == "DEPENDENCY_DEGRADATION":
                    msg = f"UpstreamTimeoutException: Service {affecting_incident.get('target_service', 'unknown')} did not respond"
                elif ic_type == "CASCADING_FAILURE":
                    msg = "CascadingFailureException: Multiple downstream services unavailable"
                elif ic_type == "RESOURCE_EXHAUSTION":
                    msg = "ResourceExhaustedException: Shared resource pool exhausted"
                elif ic_type == "CONFIG_MISMATCH":
                    msg = "ConfigurationError: Service configuration mismatch detected"
                elif ic_type == "CPU_SATURATION":
                    msg = "CpuSaturationException: CPU utilization exceeded threshold"
                else:
                    msg = "Internal Server Error: Timeout waiting for upstream"
            elif affecting_incident and random.random() < 0.1:  # 10% chance of WARNING during incident
                log_level = "WARNING"
                msg = f"Performance degradation detected: {affecting_incident['type']}"

            # Get cloud provider for this node
            cloud_provider_name = node.get('cloud_provider', 'onpremise')

            log_entry = {
                "timestamp": timestamp.isoformat(),
                "level": log_level,
                "service": node['service'],
                "host": node['host_id'],
                "cloud_provider": cloud_provider_name,
                "region": node['region'],
                "trace_id": trace_id,  # Correlated
                "message": msg
            }
            # Add cloud-specific metadata
            cloud_metadata = {k: v for k, v in node.items() 
                            if k not in ['host_id', 'service', 'region', 'ip', 'cloud_provider']}
            if cloud_metadata:
                log_entry["metadata"] = cloud_metadata
            logs_batch.append(log_entry)

        return logs_batch, traces_batch

    def _generate_events(self, timestamp, active_incidents, granularity_minutes):
        events_batch = []
        
        # Deployment Event (Random, less frequent but more realistic)
        if random.random() < 0.008:  # ~2-3 per week
            service = random.choice(SERVICES)
            version = f"v2.{random.randint(4, 6)}.{random.randint(0, 9)}"
            events_batch.append({
                "timestamp": timestamp.isoformat(),
                "type": "DEPLOYMENT",
                "service": service,
                "region": random.choice(self.regions),
                "version": version,
                "deployment_id": str(uuid.uuid4()),
                "status": random.choice(["SUCCESS", "SUCCESS", "SUCCESS", "ROLLBACK"]),  # 75% success rate
                "message": f"Deployment {version} to {service}",
                "metadata": {
                    "deployed_by": f"user-{random.choice(['alice', 'bob', 'charlie', 'diana'])}",
                    "rollback_reason": random.choice(["Health check failed", "Error rate spike", "Latency increase"]) if random.random() < 0.25 else None
                }
            })
        
        # Maintenance Window Events
        if timestamp.hour == 2 and timestamp.minute == 0:
            events_batch.append({
                "timestamp": timestamp.isoformat(),
                "type": "MAINTENANCE_WINDOW",
                "status": "STARTED",
                "message": "Scheduled maintenance window started",
                "affected_services": random.sample(SERVICES, k=random.randint(1, 3))
            })
        elif timestamp.hour == 4 and timestamp.minute == 45:
            events_batch.append({
                "timestamp": timestamp.isoformat(),
                "type": "MAINTENANCE_WINDOW",
                "status": "COMPLETED",
                "message": "Scheduled maintenance window completed"
            })
        
        # Scaling Events (Auto-scaling based on load - more likely during incidents)
        scale_prob = 0.02  # Base probability
        
        # Increase scaling probability during incidents (to handle load)
        if active_incidents:
            scale_prob = 0.05  # Higher during incidents
        
        if random.random() < scale_prob:
            # Prefer services affected by incidents for scale-up
            affected_services = []
            for incident in active_incidents:
                affected_services.extend(incident.get('affected_services', []))
            
            if affected_services and random.random() < 0.6:  # 60% chance to scale affected service
                service = random.choice(affected_services)
                action = "SCALE_UP"  # Always scale up during incidents
                incident = next((inc for inc in active_incidents if service in inc.get('affected_services', [])), None)
            else:
                service = random.choice(SERVICES)
                action = random.choice(["SCALE_UP", "SCALE_DOWN", "SCALE_UP"])
                incident = None
            
            # Determine trigger based on incident type if applicable
            if incident:
                if incident['type'] == "CPU_SATURATION":
                    trigger = "CPU threshold"
                elif incident['type'] == "MEMORY_LEAK":
                    trigger = "Memory threshold"
                elif incident['type'] in ["DB_CONTENTION", "RESOURCE_EXHAUSTION"]:
                    trigger = "Request rate"
                else:
                    trigger = "Latency threshold"
            else:
                trigger = random.choice(["CPU threshold", "Memory threshold", "Request rate", "Latency threshold"])
            
            scale_event = {
                "timestamp": timestamp.isoformat(),
                "type": "AUTOSCALE",
                "service": service,
                "action": action,
                "current_replicas": random.randint(2, 8),
                "new_replicas": random.randint(3, 10) if action == "SCALE_UP" else random.randint(1, 5),
                "trigger": trigger,
                "message": f"Auto-scaling {service}: {action}"
            }
            
            # Link to incident if applicable
            if incident:
                scale_event["incident_id"] = incident['id']
                scale_event["incident_type"] = incident['type']
            
            events_batch.append(scale_event)
        
        # Configuration Change Events
        if random.random() < 0.01:  # ~1% chance per interval
            service = random.choice(SERVICES)
            config_type = random.choice(["feature_flag", "timeout", "connection_pool", "cache_size", "rate_limit"])
            events_batch.append({
                "timestamp": timestamp.isoformat(),
                "type": "CONFIG_CHANGE",
                "service": service,
                "config_key": config_type,
                "old_value": str(random.randint(10, 100)),
                "new_value": str(random.randint(10, 100)),
                "changed_by": f"user-{random.choice(['alice', 'bob', 'charlie'])}",
                "message": f"Configuration change: {config_type} updated for {service}"
            })
        
        # Health Check Events (Periodic) - Correlated with incidents
        if timestamp.minute % 30 == 0:  # Every 30 minutes
            for service in random.sample(SERVICES, k=random.randint(1, 3)):
                # Check if this service is affected by any active incident
                service_incidents = [inc for inc in active_incidents if service in inc.get('affected_services', [])]
                
                if service_incidents:
                    # Service has active incidents - health check should reflect degradation
                    incident = service_incidents[0]
                    health_status = random.choice(["DEGRADED", "DEGRADED", "UNHEALTHY"])
                    liveness = "FAIL" if random.random() < 0.7 else "PASS"
                    readiness = "FAIL" if random.random() < 0.6 else "PASS"
                else:
                    # Normal operation - mostly healthy
                    health_status = random.choice(["HEALTHY", "HEALTHY", "HEALTHY", "DEGRADED"])
                    liveness = "PASS" if health_status == "HEALTHY" else random.choice(["PASS", "FAIL"])
                    readiness = "PASS" if health_status == "HEALTHY" else random.choice(["PASS", "FAIL"])
                
                health_event = {
                    "timestamp": timestamp.isoformat(),
                    "type": "HEALTH_CHECK",
                    "service": service,
                    "status": health_status,
                    "checks": {
                        "liveness": liveness,
                        "readiness": readiness,
                        "startup": "PASS"
                    },
                    "message": f"Health check for {service}: {health_status}"
                }
                
                # Link to incident if service is affected
                if service_incidents:
                    health_event["incident_id"] = service_incidents[0]['id']
                    health_event["incident_type"] = service_incidents[0]['type']
                
                events_batch.append(health_event)
        
        # Service Restart Events (Correlated with incidents)
        # Higher probability during incidents, especially memory leaks
        restart_prob = 0.003  # Base probability
        restart_reasons = ["OOM kill", "Crash loop", "Manual restart", "Pod eviction", "Node maintenance"]
        
        # Check if any incidents are active that might cause restarts
        for incident in active_incidents:
            if incident['type'] == "MEMORY_LEAK":
                restart_prob = 0.02  # Much higher during memory leaks
                restart_reasons = ["OOM kill", "OOM kill", "Crash loop", "Manual restart"]
            elif incident['type'] in ["CPU_SATURATION", "RESOURCE_EXHAUSTION"]:
                restart_prob = 0.01  # Higher during resource issues
                restart_reasons = ["Crash loop", "OOM kill", "Manual restart"]
        
        if random.random() < restart_prob:
            # Prefer hosts affected by incidents
            affected_hosts = []
            for incident in active_incidents:
                affected_hosts.extend(incident.get('affected_hosts', []))
            
            if affected_hosts and random.random() < 0.7:  # 70% chance to restart affected host
                host_id = random.choice(affected_hosts)
                node = next((n for n in self.topology if n['host_id'] == host_id), random.choice(self.topology))
                incident = next((inc for inc in active_incidents if host_id in inc.get('affected_hosts', [])), None)
            else:
                node = random.choice(self.topology)
                incident = None
            
            reason = random.choice(restart_reasons)
            restart_event = {
                "timestamp": timestamp.isoformat(),
                "type": "SERVICE_RESTART",
                "service": node['service'],
                "host_id": node['host_id'],
                "region": node['region'],
                "reason": reason,
                "restart_count": random.randint(1, 5),
                "message": f"Service restart: {node['service']} on {node['host_id']} - {reason}"
            }
            
            # Link to incident if applicable
            if incident:
                restart_event["incident_id"] = incident['id']
                restart_event["incident_type"] = incident['type']
            
            events_batch.append(restart_event)
        
        # Incident Events (Enhanced with intermediate events)
        for incident in active_incidents:
            incident_start = incident['start_time']
            incident_end = incident['end_time']
            time_since_start = (timestamp - incident_start).total_seconds() / 60  # minutes
            time_to_end = (incident_end - timestamp).total_seconds() / 60
            
            # Primary incident start (use time window instead of exact match)
            if 0 <= time_since_start < granularity_minutes and incident.get('is_primary', True):
                severity = incident['root_cause']['severity']
                events_batch.append({
                    "timestamp": timestamp.isoformat(),
                    "type": "ALERT_TRIGGER",
                    "severity": "CRITICAL" if severity == "P1" else "HIGH" if severity == "P2" else "MEDIUM",
                    "source": incident['target_host'],
                    "service": incident['target_service'],
                    "region": next((n['region'] for n in self.topology if n['host_id'] == incident['target_host']), "unknown"),
                    "incident_id": incident['id'],
                    "incident_type": incident['type'],
                    "metric": incident['root_cause']['metric'],
                    "threshold_value": random.randint(80, 95),
                    "current_value": random.randint(95, 100),
                    "message": f"Threshold breach: {incident['root_cause']['metric']} exceeded limit. Incident type: {incident['type']}",
                    "metadata": {
                        "alert_rule": f"{incident['root_cause']['metric']}_threshold",
                        "notification_sent": True,
                        "oncall_acknowledged": random.choice([True, False])
                    }
                })
            
            # Cascading incident start
            if 0 <= time_since_start < granularity_minutes and not incident.get('is_primary', True):
                events_batch.append({
                    "timestamp": timestamp.isoformat(),
                    "type": "CASCADE_TRIGGER",
                    "severity": "HIGH",
                    "source": incident['target_host'],
                    "service": incident['target_service'],
                    "region": next((n['region'] for n in self.topology if n['host_id'] == incident['target_host']), "unknown"),
                    "incident_id": incident['id'],
                    "primary_incident_id": incident.get('primary_incident_id'),
                    "upstream_service": incident.get('target_service'),
                    "message": f"Cascading failure detected: {incident['target_service']} affected by upstream issue",
                    "metadata": {
                        "dependency_path": incident.get('target_service', 'unknown'),
                        "propagation_delay_minutes": int(time_since_start)
                    }
                })
            
            # Incident updates during active incidents (every 30-60 minutes)
            if incident.get('is_primary', True) and time_since_start > 0 and time_to_end > 0:
                if time_since_start % 30 < granularity_minutes:  # Update every ~30 minutes
                    update_type = random.choice(["ESCALATION", "UPDATE", "MITIGATION_ATTEMPT"])
                    events_batch.append({
                        "timestamp": timestamp.isoformat(),
                        "type": "INCIDENT_UPDATE",
                        "incident_id": incident['id'],
                        "update_type": update_type,
                        "severity": incident['root_cause']['severity'],
                        "service": incident['target_service'],
                        "affected_hosts_count": len(incident.get('affected_hosts', [])),
                        "affected_services": incident.get('affected_services', []),
                        "message": self._get_incident_update_message(update_type, incident),
                        "metadata": {
                            "updated_by": f"oncall-{random.choice(['engineer1', 'engineer2', 'sre-team'])}",
                            "status": random.choice(["INVESTIGATING", "MITIGATING", "MONITORING"]),
                            "impact": random.choice(["LOW", "MEDIUM", "HIGH"])
                        }
                    })
            
            # Incident resolution (use time window)
            if 0 <= time_to_end < granularity_minutes:
                resolution_time = (incident_end - incident_start).total_seconds() / 60
                events_batch.append({
                    "timestamp": timestamp.isoformat(),
                    "type": "INCIDENT_RESOLVED",
                    "severity": "INFO",
                    "source": incident['target_host'],
                    "service": incident['target_service'],
                    "region": next((n['region'] for n in self.topology if n['host_id'] == incident['target_host']), "unknown"),
                    "incident_id": incident['id'],
                    "incident_type": incident['type'],
                    "duration_minutes": int(resolution_time),
                    "resolution_action": random.choice(["Auto-recovery", "Manual fix", "Rollback", "Configuration change", "Resource scaling"]),
                    "message": f"Incident resolved: {incident['type']} after {int(resolution_time)} minutes",
                    "metadata": {
                        "resolved_by": f"oncall-{random.choice(['engineer1', 'engineer2', 'auto-recovery'])}",
                        "root_cause_identified": random.choice([True, False]),
                        "postmortem_scheduled": random.choice([True, False]) if resolution_time > 60 else False
                    }
                })
        
        # User Action Events (Manual interventions - more likely during incidents)
        user_action_prob = 0.005  # Base probability
        
        # Increase probability during active incidents (engineers taking action)
        if active_incidents:
            user_action_prob = 0.015  # 3x higher during incidents
        
        if random.random() < user_action_prob:
            # Prefer services affected by incidents
            affected_services = []
            for incident in active_incidents:
                affected_services.extend(incident.get('affected_services', []))
            
            if affected_services and random.random() < 0.7:  # 70% chance to act on affected service
                service = random.choice(affected_services)
                incident = next((inc for inc in active_incidents if service in inc.get('affected_services', [])), None)
                # During incidents, prefer mitigation actions
                action_type = random.choice(["FORCE_RESTART", "TRAFFIC_SHIFT", "MANUAL_ROLLBACK", "FEATURE_TOGGLE"])
                reason = random.choice(["Error spike", "Performance issue", "Customer report"])
            else:
                service = random.choice(SERVICES)
                incident = None
                action_type = random.choice(["MANUAL_ROLLBACK", "FORCE_RESTART", "TRAFFIC_SHIFT", "FEATURE_TOGGLE"])
                reason = random.choice(["Performance issue", "Error spike", "Customer report", "Preventive action"])
            
            user_action_event = {
                "timestamp": timestamp.isoformat(),
                "type": "USER_ACTION",
                "action": action_type,
                "service": service,
                "user": f"user-{random.choice(['alice', 'bob', 'charlie', 'diana'])}",
                "reason": reason,
                "message": f"Manual action: {action_type} on {service}",
                "metadata": {
                    "action_id": str(uuid.uuid4()),
                    "approved_by": f"manager-{random.choice(['alice', 'bob'])}"
                }
            }
            
            # Link to incident if applicable
            if incident:
                user_action_event["incident_id"] = incident['id']
                user_action_event["incident_type"] = incident['type']
            
            events_batch.append(user_action_event)
        
        return events_batch
    
    def _get_incident_update_message(self, update_type, incident):
        """Generate realistic incident update messages."""
        if update_type == "ESCALATION":
            return f"Incident {incident['id'][:8]} escalated to {incident['root_cause']['severity']} - {incident['target_service']} still affected"
        elif update_type == "UPDATE":
            return f"Incident update: {incident['type']} affecting {len(incident.get('affected_hosts', []))} hosts, investigation ongoing"
        elif update_type == "MITIGATION_ATTEMPT":
            mitigation = random.choice(["Rolling restart initiated", "Traffic shifted to healthy region", "Configuration hotfix applied", "Resource scaling triggered"])
            return f"Mitigation attempt: {mitigation} for {incident['target_service']}"
        return f"Incident {incident['type']} update"

    def run(self):
        enabled_clouds = self.cloud_config.get_enabled_clouds()
        days_to_generate = self.cloud_config.days_to_generate
        granularity_minutes = self.cloud_config.granularity_minutes
        start_date = self.cloud_config.start_date
        
        print(f"Starting generation for {days_to_generate} days...")
        print(f"Start date: {start_date.strftime('%Y-%m-%d')}")
        print(f"Granularity: {granularity_minutes} minutes")
        print(f"Total data points per day: {24 * 60 // granularity_minutes}")
        print(f"Enabled clouds: {', '.join(enabled_clouds)}")
        print(f"Total regions: {len(self.regions)}")
        print(f"Total hosts: {len(self.topology)}")
        print("-" * 60)
        
        ground_truth_catalog = []
        total_intervals = days_to_generate * (24 * 60 // granularity_minutes)
        processed_intervals = 0

        for day_offset in range(days_to_generate):
            curr_date = start_date + timedelta(days=day_offset)
            date_str = curr_date.strftime("%Y-%m-%d")
            month_str = curr_date.strftime("%Y-%m")
            
            # Create subdirs
            for dtype in ['metrics', 'events', 'logs', 'traces']:
                os.makedirs(os.path.join(BASE_DIR, dtype, month_str), exist_ok=True)

            # Daily Schedule (may include incidents from previous day that extend)
            daily_incidents = self.generate_incident_schedule(curr_date)
            ground_truth_catalog.extend(daily_incidents)

            # Data Containers
            daily_metrics = []
            daily_logs = []
            daily_traces = []
            daily_events = []

            # Time Loop (based on granularity)
            intervals_per_day = 24 * 60 // granularity_minutes
            for interval in range(intervals_per_day):
                curr_time = curr_date + timedelta(minutes=interval * granularity_minutes)
                
                # Get all active incidents at this timestamp
                active_incidents = self._get_active_incidents(curr_time, daily_incidents)

                # Generate Data
                daily_metrics.extend(self._generate_metrics(curr_time, active_incidents))
                l, t = self._generate_logs_and_traces(curr_time, active_incidents)
                daily_logs.extend(l)
                daily_traces.extend(t)
                daily_events.extend(self._generate_events(curr_time, active_incidents, granularity_minutes))
                
                processed_intervals += 1
                if processed_intervals % 100 == 0:
                    progress = (processed_intervals / total_intervals) * 100
                    print(f"Progress: {progress:.1f}% ({processed_intervals}/{total_intervals} intervals)", end='\r')

            # Save Files
            self._save_file(daily_metrics, 'metrics', month_str, date_str)
            self._save_file(daily_logs, 'logs', month_str, date_str)
            self._save_file(daily_traces, 'traces', month_str, date_str)
            self._save_file(daily_events, 'events', month_str, date_str)
            
            progress = ((day_offset + 1) / days_to_generate) * 100
            incident_count = len([i for i in daily_incidents if i.get('is_primary', True)])
            print(f"Completed {date_str} ({progress:.1f}%) - {incident_count} primary incident(s)")

        # Save Ground Truth with enhanced metadata
        ground_truth_enhanced = {
            "generation_config": {
                "start_date": start_date.isoformat(),
                "days_generated": days_to_generate,
                "granularity_minutes": granularity_minutes,
                "total_hosts": len(self.topology),
                "services": SERVICES,
                "regions": self.regions
            },
            "incidents": ground_truth_catalog,
            "summary": {
                "total_incidents": len(ground_truth_catalog),
                "primary_incidents": len([i for i in ground_truth_catalog if i.get('is_primary', True)]),
                "cascading_incidents": len([i for i in ground_truth_catalog if not i.get('is_primary', True)]),
                "incident_types": {}
            }
        }
        
        # Count incidents by type
        for incident in ground_truth_catalog:
            inc_type = incident['type']
            ground_truth_enhanced["summary"]["incident_types"][inc_type] = \
                ground_truth_enhanced["summary"]["incident_types"].get(inc_type, 0) + 1
        
        with open(os.path.join(BASE_DIR, 'metadata', 'incident_catalog.json'), 'w') as f:
            json.dump(ground_truth_enhanced, f, default=str, indent=2)
        
        # Generate Root Cause Analysis Summary
        primary_incidents = [inc for inc in ground_truth_catalog if inc.get('is_primary', True)]
        cascading_incidents = [inc for inc in ground_truth_catalog if not inc.get('is_primary', True)]
        
        # Group primary incidents by type
        root_causes_by_type = {}
        for incident in primary_incidents:
            inc_type = incident['type']
            if inc_type not in root_causes_by_type:
                root_causes_by_type[inc_type] = []
            root_causes_by_type[inc_type].append(incident)
        
        # Build mapping of primary incident to cascading incidents
        incident_map = {inc['id']: inc for inc in ground_truth_catalog}
        
        # Write detailed root cause analysis to file
        root_cause_file = os.path.join(BASE_DIR, 'metadata', 'root_cause.txt')
        with open(root_cause_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("ROOT CAUSE ANALYSIS DETAILS\n")
            f.write("=" * 80 + "\n")
            f.write("\n")
            f.write("This file contains detailed information about all root causes and their\n")
            f.write("resultant cascading incidents. Use this to verify if your RCA model\n")
            f.write("correctly identifies root causes.\n")
            f.write("\n")
            
            # Write root causes grouped by type
            for root_cause_type in sorted(root_causes_by_type.keys()):
                incidents_of_type = root_causes_by_type[root_cause_type]
                f.write(f"\n{'─' * 80}\n")
                f.write(f"ROOT CAUSE TYPE: {root_cause_type} ({len(incidents_of_type)} occurrence(s))\n")
                f.write(f"  Metric: {INCIDENT_TYPES[root_cause_type]['metric']}\n")
                f.write(f"  Severity: {INCIDENT_TYPES[root_cause_type]['severity']}\n")
                f.write(f"  Cascading Probability: {INCIDENT_TYPES[root_cause_type]['cascading_prob'] * 100:.0f}%\n")
                f.write(f"{'─' * 80}\n")
                
                for idx, primary_incident in enumerate(incidents_of_type, 1):
                    start_time = primary_incident['start_time']
                    end_time = primary_incident['end_time']
                    duration = (end_time - start_time).total_seconds() / 60
                    
                    f.write(f"\n  [{idx}] Primary Incident ID: {primary_incident['id']}\n")
                    f.write(f"      Service: {primary_incident['target_service']}\n")
                    f.write(f"      Host: {primary_incident['target_host']}\n")
                    f.write(f"      Time: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%H:%M')} ({duration:.0f} min)\n")
                    f.write(f"      Affected Services: {', '.join(primary_incident.get('affected_services', []))}\n")
                    f.write(f"      Affected Hosts: {len(primary_incident.get('affected_hosts', []))} host(s)\n")
                    
                    # Show cascading incidents
                    cascading_ids = primary_incident.get('cascading_incidents', [])
                    if cascading_ids:
                        f.write(f"      └─ Cascading Incidents ({len(cascading_ids)}):\n")
                        for cascade_id in cascading_ids:
                            if cascade_id in incident_map:
                                cascade = incident_map[cascade_id]
                                cascade_start = cascade['start_time']
                                cascade_duration = (cascade['end_time'] - cascade_start).total_seconds() / 60
                                f.write(f"         • {cascade['target_service']} ({cascade['type']})\n")
                                f.write(f"           ID: {cascade_id}\n")
                                f.write(f"           Time: {cascade_start.strftime('%H:%M')} - {cascade['end_time'].strftime('%H:%M')} ({cascade_duration:.0f} min)\n")
                    else:
                        f.write(f"      └─ No cascading incidents\n")
            
            f.write("\n")
            f.write("=" * 80 + "\n")
            f.write("SUMMARY BY ROOT CAUSE TYPE\n")
            f.write("=" * 80 + "\n")
            for root_cause_type in sorted(root_causes_by_type.keys()):
                count = len(root_causes_by_type[root_cause_type])
                total_cascading = sum(
                    len(inc.get('cascading_incidents', [])) 
                    for inc in root_causes_by_type[root_cause_type]
                )
                f.write(f"  {root_cause_type:30s}: {count:3d} root cause(s) → {total_cascading:3d} cascading incident(s)\n")
            
            f.write("\n")
            f.write("=" * 80 + "\n")
        
        print("-" * 60)
        print(f"Generation complete!")
        print(f"Total incidents: {ground_truth_enhanced['summary']['total_incidents']}")
        print(f"Primary incidents: {ground_truth_enhanced['summary']['primary_incidents']}")
        print(f"Cascading incidents: {ground_truth_enhanced['summary']['cascading_incidents']}")
        print(f"Data saved to: {BASE_DIR}/")
        print()
        print("=" * 80)
        print("ROOT CAUSE ANALYSIS SUMMARY")
        print("=" * 80)
        print()
        for root_cause_type in sorted(root_causes_by_type.keys()):
            count = len(root_causes_by_type[root_cause_type])
            total_cascading = sum(
                len(inc.get('cascading_incidents', [])) 
                for inc in root_causes_by_type[root_cause_type]
            )
            print(f"  {root_cause_type:30s}: {count:3d} root cause(s) → {total_cascading:3d} cascading incident(s)")
        print()
        print(f"Detailed root cause analysis saved to: {root_cause_file}")
        print("=" * 80)

    def _save_file(self, data, dtype, month, date_str):
        path = os.path.join(BASE_DIR, dtype, month, f"{dtype}_{date_str}.json")
        with open(path, 'w') as f:
            json.dump(data, f, indent=None) # Compact JSON

def parse_args():
    """Parse command-line arguments."""
    default_config_path = "config.json"
    
    parser = argparse.ArgumentParser(
        description="Generate MELT (Metrics, Events, Logs, Traces) telemetry data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Configuration:
  All settings (clouds, start date, days to generate, granularity) are configured in config.json
  
Examples:
  # Use default config.json
  python generate_melt_data.py
  
  # Use custom config file
  python generate_melt_data.py --config my_config.json
        """
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=default_config_path,
        metavar="PATH",
        help=f"Path to configuration file (default: {default_config_path})"
    )
    
    return parser.parse_args()


# Run Generator
if __name__ == "__main__":
    args = parse_args()
    
    # Load cloud configuration
    cloud_config = CloudConfig(config_path=args.config)
    
    # Show configuration
    config_source = args.config
    enabled_clouds = cloud_config.get_enabled_clouds()
    
    print("=" * 60)
    print("MELT Data Generator - Configuration")
    print("=" * 60)
    print(f"Configuration file: {config_source}")
    print(f"Start date: {cloud_config.start_date.strftime('%Y-%m-%d')}")
    print(f"Days to generate: {cloud_config.days_to_generate}")
    print(f"Granularity: {cloud_config.granularity_minutes} minutes")
    print(f"Enabled clouds: {', '.join(enabled_clouds) if enabled_clouds else 'none'}")
    
    # Check if at least one cloud is enabled
    if not enabled_clouds:
        print("\nError: No clouds are enabled. Please enable at least one cloud in config.json")
        print(f"Supported clouds: {', '.join(CloudConfig.SUPPORTED_CLOUDS)}")
        exit(1)
    
    print(f"Total regions: {len(cloud_config.get_all_regions())}")
    print("=" * 60)
    print()
    
    # Create generator with cloud configuration
    gen = MELTGenerator(cloud_config=cloud_config)
    gen.run()