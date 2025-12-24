#!/usr/bin/env python3
"""
Utility script to map incidents to related metrics, events, logs, and traces.

Usage:
    python map_incident.py <incident_id>
    python map_incident.py --list  # List all incidents
    python map_incident.py --summary  # Show summary statistics
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


def load_incident_catalog(melt_data_dir="melt_data"):
    """Load the incident catalog."""
    catalog_path = Path(melt_data_dir) / "metadata" / "incident_catalog.json"
    with open(catalog_path) as f:
        return json.load(f)


def map_incident_to_data(incident_id, melt_data_dir="melt_data"):
    """Map an incident to all related metrics, events, logs, and traces."""
    
    # Load incident catalog
    catalog = load_incident_catalog(melt_data_dir)
    
    # Find the incident
    incident = next((i for i in catalog['incidents'] if i['id'] == incident_id), None)
    if not incident:
        raise ValueError(f"Incident {incident_id} not found")
    
    # Parse incident times
    start_time = datetime.fromisoformat(incident['start_time'].replace(' ', 'T'))
    end_time = datetime.fromisoformat(incident['end_time'].replace(' ', 'T'))
    date_str = start_time.strftime('%Y-%m-%d')
    month_str = start_time.strftime('%Y-%m')
    
    result = {
        'incident': incident,
        'events': [],
        'metrics': [],
        'logs': [],
        'traces': []
    }
    
    # Load and filter events (check all days in incident range)
    events_dir = Path(melt_data_dir) / "events" / month_str
    if events_dir.exists():
        current_date = start_time.date()
        end_date = end_time.date()
        while current_date <= end_date:
            events_path = events_dir / f"events_{current_date.strftime('%Y-%m-%d')}.json"
            if events_path.exists():
                with open(events_path) as f:
                    events = json.load(f)
                result['events'].extend([
                    e for e in events
                    if e.get('incident_id') == incident_id
                    or (start_time <= datetime.fromisoformat(e['timestamp']) <= end_time
                        and e.get('service') in incident['affected_services'])
                ])
            current_date = current_date + timedelta(days=1)
    
    # Load and filter metrics
    metrics_path = Path(melt_data_dir) / "metrics" / month_str / f"metrics_{date_str}.json"
    if metrics_path.exists():
        with open(metrics_path) as f:
            metrics = json.load(f)
        result['metrics'] = [
            m for m in metrics
            if (start_time <= datetime.fromisoformat(m['timestamp']) <= end_time
                and m['host_id'] in incident['affected_hosts']
                and m['service'] in incident['affected_services'])
        ]
    
    # Load and filter logs
    logs_path = Path(melt_data_dir) / "logs" / month_str / f"logs_{date_str}.json"
    if logs_path.exists():
        with open(logs_path) as f:
            logs = json.load(f)
        result['logs'] = [
            l for l in logs
            if (start_time <= datetime.fromisoformat(l['timestamp']) <= end_time
                and l['host'] in incident['affected_hosts']
                and l['service'] in incident['affected_services'])
        ]
    
    # Load and filter traces
    traces_path = Path(melt_data_dir) / "traces" / month_str / f"traces_{date_str}.json"
    if traces_path.exists():
        with open(traces_path) as f:
            traces = json.load(f)
        result['traces'] = [
            t for t in traces
            if (start_time <= datetime.fromisoformat(t['timestamp']) <= end_time
                and t['service_name'] in incident['affected_services'])
        ]
    
    return result


def print_incident_mapping(incident_id, melt_data_dir="melt_data"):
    """Print a formatted mapping of an incident to all data types."""
    try:
        mapped_data = map_incident_to_data(incident_id, melt_data_dir)
        incident = mapped_data['incident']
        
        print("=" * 80)
        print(f"INCIDENT MAPPING: {incident_id}")
        print("=" * 80)
        print(f"Type: {incident['type']}")
        print(f"Service: {incident['target_service']}")
        print(f"Host: {incident['target_host']}")
        print(f"Time: {incident['start_time']} - {incident['end_time']}")
        print(f"Affected Services: {', '.join(incident['affected_services'])}")
        print(f"Affected Hosts: {len(incident['affected_hosts'])} host(s)")
        print()
        
        # Events
        events = mapped_data['events']
        events_with_incident_id = [e for e in events if e.get('incident_id') == incident_id]
        print(f"EVENTS: {len(events)} total ({len(events_with_incident_id)} directly linked)")
        event_types = defaultdict(int)
        for e in events:
            event_types[e['type']] += 1
        for event_type, count in sorted(event_types.items()):
            print(f"  - {event_type}: {count}")
        print()
        
        # Metrics
        metrics = mapped_data['metrics']
        print(f"METRICS: {len(metrics)} entries")
        if metrics:
            # Show sample metric
            sample = metrics[0]
            print(f"  Sample metric keys: {list(sample.get('metrics', {}).keys())[:3]}...")
        print()
        
        # Logs
        logs = mapped_data['logs']
        error_logs = [l for l in logs if l['level'] in ['ERROR', 'WARNING']]
        print(f"LOGS: {len(logs)} total ({len(error_logs)} errors/warnings)")
        log_levels = defaultdict(int)
        for l in logs:
            log_levels[l['level']] += 1
        for level, count in sorted(log_levels.items()):
            print(f"  - {level}: {count}")
        print()
        
        # Traces
        traces = mapped_data['traces']
        failed_traces = [t for t in traces if t['status_code'] == 500]
        print(f"TRACES: {len(traces)} total ({len(failed_traces)} failed)")
        if traces:
            avg_duration = sum(t['duration_ms'] for t in traces) / len(traces)
            print(f"  Average duration: {avg_duration:.2f} ms")
        print()
        
        print("=" * 80)
        
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error loading data: {e}")


def list_incidents(melt_data_dir="melt_data"):
    """List all incidents."""
    catalog = load_incident_catalog(melt_data_dir)
    incidents = catalog['incidents']
    
    print(f"Total Incidents: {len(incidents)}")
    print(f"Primary: {sum(1 for i in incidents if i.get('is_primary', True))}")
    print(f"Cascading: {sum(1 for i in incidents if not i.get('is_primary', True))}")
    print()
    print("Incidents:")
    print("-" * 80)
    
    for idx, incident in enumerate(incidents[:20], 1):  # Show first 20
        print(f"{idx}. {incident['id'][:36]}...")
        print(f"   Type: {incident['type']}")
        print(f"   Service: {incident['target_service']}")
        print(f"   Time: {incident['start_time']} - {incident['end_time']}")
        print()
    
    if len(incidents) > 20:
        print(f"... and {len(incidents) - 20} more incidents")


def show_summary(melt_data_dir="melt_data"):
    """Show summary statistics."""
    catalog = load_incident_catalog(melt_data_dir)
    incidents = catalog['incidents']
    
    print("=" * 80)
    print("INCIDENT SUMMARY")
    print("=" * 80)
    print(f"Total Incidents: {len(incidents)}")
    print(f"Primary Incidents: {sum(1 for i in incidents if i.get('is_primary', True))}")
    print(f"Cascading Incidents: {sum(1 for i in incidents if not i.get('is_primary', True))}")
    print()
    
    # Count by type
    incident_types = defaultdict(int)
    for incident in incidents:
        incident_types[incident['type']] += 1
    
    print("Incidents by Type:")
    for inc_type, count in sorted(incident_types.items(), key=lambda x: -x[1]):
        print(f"  {inc_type:30s}: {count:3d}")
    print()
    
    # Date range
    dates = []
    for incident in incidents:
        dates.append(datetime.fromisoformat(incident['start_time'].replace(' ', 'T')))
    
    if dates:
        print(f"Date Range: {min(dates).strftime('%Y-%m-%d')} to {max(dates).strftime('%Y-%m-%d')}")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Map incidents to related MELT data",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'incident_id',
        nargs='?',
        help='Incident ID to map (use --list to see available IDs)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all incidents'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show summary statistics'
    )
    parser.add_argument(
        '--data-dir',
        default='melt_data',
        help='Path to melt_data directory (default: melt_data)'
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_incidents(args.data_dir)
    elif args.summary:
        show_summary(args.data_dir)
    elif args.incident_id:
        print_incident_mapping(args.incident_id, args.data_dir)
    else:
        parser.print_help()
        print("\nExample:")
        print("  python map_incident.py --list")
        print("  python map_incident.py <incident_id>")


if __name__ == "__main__":
    main()

