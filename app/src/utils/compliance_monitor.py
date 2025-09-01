#!/usr/bin/env python3
"""
Compliance Monitoring and Audit System
Tracks API usage, violations, and generates compliance reports
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

@dataclass
class ComplianceEvent:
    """Single compliance event record."""
    timestamp: datetime
    event_type: str  # 'api_request', 'rate_limit_hit', 'content_violation', 'quota_exceeded'
    agent_type: str
    session_id: Optional[str]
    content_length: int
    success: bool
    error_message: Optional[str] = None
    violation_details: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ComplianceMonitor:
    """
    Monitors and logs compliance events for audit purposes.
    Generates reports and alerts for policy violations.
    """
    
    def __init__(self, log_directory: str = "logs/compliance"):
        """Initialize compliance monitor."""
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # In-memory event storage (last 1000 events)
        self.recent_events: List[ComplianceEvent] = []
        self.max_recent_events = 1000
        
        # Daily statistics
        self.daily_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limit_hits': 0,
            'content_violations': 0,
            'quota_exceeded': 0,
            'last_reset': datetime.now().date()
        }
        
        logger.info(f"Compliance monitor initialized, logging to: {self.log_directory}")
    
    def log_event(self, 
                  event_type: str,
                  agent_type: str,
                  content_length: int,
                  success: bool,
                  session_id: Optional[str] = None,
                  error_message: Optional[str] = None,
                  violation_details: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None):
        """Log a compliance event."""
        
        with self._lock:
            # Create event
            event = ComplianceEvent(
                timestamp=datetime.now(),
                event_type=event_type,
                agent_type=agent_type,
                session_id=session_id,
                content_length=content_length,
                success=success,
                error_message=error_message,
                violation_details=violation_details,
                metadata=metadata or {}
            )
            
            # Add to recent events
            self.recent_events.append(event)
            if len(self.recent_events) > self.max_recent_events:
                self.recent_events.pop(0)
            
            # Update daily statistics
            self._update_daily_stats(event)
            
            # Write to file
            self._write_event_to_file(event)
            
            # Check for alerts
            self._check_alert_conditions(event)
    
    def _update_daily_stats(self, event: ComplianceEvent):
        """Update daily statistics."""
        today = datetime.now().date()
        
        # Reset daily stats if new day
        if self.daily_stats['last_reset'] != today:
            self.daily_stats = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'rate_limit_hits': 0,
                'content_violations': 0,
                'quota_exceeded': 0,
                'last_reset': today
            }
        
        # Update counters
        if event.event_type == 'api_request':
            self.daily_stats['total_requests'] += 1
            if event.success:
                self.daily_stats['successful_requests'] += 1
            else:
                self.daily_stats['failed_requests'] += 1
        elif event.event_type == 'rate_limit_hit':
            self.daily_stats['rate_limit_hits'] += 1
        elif event.event_type == 'content_violation':
            self.daily_stats['content_violations'] += 1
        elif event.event_type == 'quota_exceeded':
            self.daily_stats['quota_exceeded'] += 1
    
    def _write_event_to_file(self, event: ComplianceEvent):
        """Write event to daily log file."""
        try:
            date_str = event.timestamp.strftime("%Y-%m-%d")
            log_file = self.log_directory / f"compliance_{date_str}.jsonl"
            
            # Convert to JSON-serializable format
            event_dict = asdict(event)
            event_dict['timestamp'] = event.timestamp.isoformat()
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event_dict) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write compliance event to file: {e}")
    
    def _check_alert_conditions(self, event: ComplianceEvent):
        """Check if event triggers any alerts."""
        # Alert on content violations
        if event.event_type == 'content_violation':
            logger.warning(f"COMPLIANCE ALERT: Content violation detected - {event.violation_details}")
        
        # Alert on quota exceeded
        if event.event_type == 'quota_exceeded':
            logger.error(f"COMPLIANCE ALERT: API quota exceeded - {event.error_message}")
        
        # Alert on high failure rate
        if len(self.recent_events) >= 10:
            recent_failures = sum(1 for e in self.recent_events[-10:] if not e.success)
            if recent_failures >= 8:  # 80% failure rate in last 10 requests
                logger.warning(f"COMPLIANCE ALERT: High failure rate detected: {recent_failures}/10")
    
    def get_daily_summary(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get daily compliance summary."""
        if date is None:
            date = datetime.now()
        
        with self._lock:
            if date.date() == datetime.now().date():
                # Return current day stats
                return self.daily_stats.copy()
            else:
                # Load from file
                return self._load_daily_summary_from_file(date)
    
    def _load_daily_summary_from_file(self, date: datetime) -> Dict[str, Any]:
        """Load daily summary from log file."""
        date_str = date.strftime("%Y-%m-%d")
        log_file = self.log_directory / f"compliance_{date_str}.jsonl"
        
        summary = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limit_hits': 0,
            'content_violations': 0,
            'quota_exceeded': 0,
            'date': date_str
        }
        
        if not log_file.exists():
            return summary
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    event_data = json.loads(line.strip())
                    event_type = event_data.get('event_type', '')
                    success = event_data.get('success', False)
                    
                    if event_type == 'api_request':
                        summary['total_requests'] += 1
                        if success:
                            summary['successful_requests'] += 1
                        else:
                            summary['failed_requests'] += 1
                    elif event_type == 'rate_limit_hit':
                        summary['rate_limit_hits'] += 1
                    elif event_type == 'content_violation':
                        summary['content_violations'] += 1
                    elif event_type == 'quota_exceeded':
                        summary['quota_exceeded'] += 1
                        
        except Exception as e:
            logger.error(f"Failed to load daily summary from {log_file}: {e}")
        
        return summary
    
    def generate_compliance_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        report = {
            'report_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'summary': {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'rate_limit_hits': 0,
                'content_violations': 0,
                'quota_exceeded': 0,
                'success_rate': 0.0
            },
            'daily_breakdown': [],
            'agent_usage': {},
            'violation_details': [],
            'recommendations': []
        }
        
        # Collect daily summaries
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            daily_summary = self.get_daily_summary(current_date)
            report['daily_breakdown'].append(daily_summary)
            
            # Aggregate totals
            for key in ['total_requests', 'successful_requests', 'failed_requests', 
                       'rate_limit_hits', 'content_violations', 'quota_exceeded']:
                report['summary'][key] += daily_summary.get(key, 0)
        
        # Calculate success rate
        total = report['summary']['total_requests']
        if total > 0:
            report['summary']['success_rate'] = report['summary']['successful_requests'] / total
        
        # Add recommendations
        report['recommendations'] = self._generate_recommendations(report['summary'])
        
        return report
    
    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations based on usage patterns."""
        recommendations = []
        
        if summary['rate_limit_hits'] > 0:
            recommendations.append(
                f"Reduce API request frequency - {summary['rate_limit_hits']} rate limit violations detected"
            )
        
        if summary['content_violations'] > 0:
            recommendations.append(
                f"Review content filtering - {summary['content_violations']} content violations detected"
            )
        
        if summary['quota_exceeded'] > 0:
            recommendations.append(
                f"Monitor API quota usage - {summary['quota_exceeded']} quota exceeded events"
            )
        
        if summary['success_rate'] < 0.9:
            recommendations.append(
                f"Improve error handling - success rate is {summary['success_rate']:.1%}"
            )
        
        if not recommendations:
            recommendations.append("Compliance status is good - continue current practices")
        
        return recommendations
    
    def export_compliance_data(self, 
                              start_date: datetime,
                              end_date: datetime,
                              output_file: str):
        """Export compliance data to file for audit purposes."""
        events = []
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            log_file = self.log_directory / f"compliance_{date_str}.jsonl"
            
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            events.append(json.loads(line.strip()))
                except Exception as e:
                    logger.error(f"Failed to read {log_file}: {e}")
            
            current_date += timedelta(days=1)
        
        # Write to output file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'export_metadata': {
                        'start_date': start_date.isoformat(),
                        'end_date': end_date.isoformat(),
                        'export_timestamp': datetime.now().isoformat(),
                        'total_events': len(events)
                    },
                    'events': events
                }, f, indent=2)
            
            logger.info(f"Compliance data exported to {output_file} ({len(events)} events)")
            
        except Exception as e:
            logger.error(f"Failed to export compliance data: {e}")

# Global compliance monitor instance
_global_monitor: Optional[ComplianceMonitor] = None

def get_compliance_monitor() -> ComplianceMonitor:
    """Get or create the global compliance monitor."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ComplianceMonitor()
    return _global_monitor