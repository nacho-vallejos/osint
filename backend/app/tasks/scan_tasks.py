"""
Celery Tasks for OSINT Scanning
Defines asynchronous tasks for performing OSINT collection operations.
"""
from celery import Task
from celery.utils.log import get_task_logger
from typing import Dict, Any
import asyncio
import redis
import json

from app.core.celery_app import celery_app
from app.collectors.dns_collector import DNSCollector
from app.collectors.username_collector import UsernameCollector
from app.collectors.metadata_collector import MetadataCollector
from app.collectors.identity_collector import IdentityCollector
from app.collectors.social_search_collector import SocialSearchCollector
from app.collectors.crtsh_collector import CrtshCollector
from app.collectors.whois_collector import WhoisCollector
from app.collectors.shodan_collector import ShodanCollector
from app.collectors.virustotal_collector import VirusTotalCollector
from app.collectors.haveibeenpwned_collector import HaveIBeenPwnedCollector
from app.collectors.securitytrails_collector import SecurityTrailsCollector
from app.database import SessionLocal
from app.services.history_service import update_scan_log
from app.models.history import ScanStatus
from app.models.schemas import CollectorResult
import os

logger = get_task_logger(__name__)

# Collector mapping: maps collector_type string to Collector class
COLLECTOR_MAP = {
    "dns": DNSCollector,
    "username": UsernameCollector,
    "metadata": MetadataCollector,
    "identity": IdentityCollector,
    "social": SocialCollector,
    "crtsh": CrtshCollector,
    "whois": WhoisCollector,
    "shodan": ShodanCollector,
    "virustotal": VirusTotalCollector,
    "haveibeenpwned": HaveIBeenPwnedCollector,
    "securitytrails": SecurityTrailsCollector,
}


def publish_to_redis(task_id: str, message: dict):
    """
    Publish update to Redis Pub/Sub for WebSocket clients.
    
    Args:
        task_id: Task ID to publish update for
        message: Dictionary to publish
    """
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url, decode_responses=True)
        channel = f"scan_updates:{task_id}"
        
        # Serialize and publish
        json_message = json.dumps(message)
        r.publish(channel, json_message)
        logger.info(f"Published update to {channel}")
    except Exception as e:
        logger.error(f"Failed to publish to Redis: {e}")


class OSINTScanTask(Task):
    """
    Custom Celery Task with state updates for better tracking.
    """
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {task_id} completed successfully for {args[1]} on {args[0]}")
        
        # Publish success to Redis Pub/Sub
        publish_to_redis(task_id, {
            "type": "task_complete",
            "status": "SUCCESS",
            "task_id": task_id,
            "result": retval
        })
        
        # Update scan history log with result
        db = SessionLocal()
        try:
            update_scan_log(
                db=db,
                task_id=task_id,
                status=ScanStatus.SUCCESS,
                result_snapshot=retval
            )
        except Exception as e:
            logger.error(f"Failed to update scan history: {e}")
        finally:
            db.close()
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")
        logger.error(f"Exception info: {einfo}")
        
        # Publish failure to Redis Pub/Sub
        publish_to_redis(task_id, {
            "type": "task_failed",
            "status": "FAILURE",
            "task_id": task_id,
            "error": str(exc)
        })
        
        # Update scan history log with error
        db = SessionLocal()
        try:
            update_scan_log(
                db=db,
                task_id=task_id,
                status=ScanStatus.FAILED,
                error_message=str(exc)
            )
        except Exception as e:
            logger.error(f"Failed to update scan history: {e}")
        finally:
            db.close()


@celery_app.task(
    bind=True,
    base=OSINTScanTask,
    name="app.tasks.scan_tasks.perform_osint_scan",
    max_retries=3,
    default_retry_delay=60,
)
def perform_osint_scan(self, target: str, collector_type: str) -> Dict[str, Any]:
    """
    Perform OSINT scan asynchronously.
    
    Args:
        target: The target to scan (domain, IP, username, email, etc.)
        collector_type: Type of collector to use (dns, username, metadata, etc.)
    
    Returns:
        Dict containing the serialized CollectorResult
        
    Raises:
        ValueError: If collector_type is not supported
        Exception: Any error during collection
    """
    task_id = self.request.id
    logger.info(f"Starting OSINT scan: collector={collector_type}, target={target}, task_id={task_id}")
    
    # Publish initial state to WebSocket clients
    publish_to_redis(task_id, {
        "type": "task_started",
        "status": "STARTED",
        "task_id": task_id,
        "collector_type": collector_type,
        "target": target,
        "message": "Scan initiated..."
    })
    
    # Update task state to PROCESSING
    self.update_state(
        state="PROCESSING",
        meta={
            "collector_type": collector_type,
            "target": target,
            "status": "Initializing collector...",
        }
    )
    
    # Publish processing state
    publish_to_redis(task_id, {
        "type": "task_progress",
        "status": "PROCESSING",
        "task_id": task_id,
        "message": "Initializing collector...",
        "progress": 10
    })
    
    try:
        # Validate collector type
        collector_class = COLLECTOR_MAP.get(collector_type.lower())
        if not collector_class:
            available_collectors = ", ".join(COLLECTOR_MAP.keys())
            error_msg = f"Collector type '{collector_type}' not found. Available: {available_collectors}"
            logger.error(error_msg)
            
            # Publish error
            publish_to_redis(task_id, {
                "type": "task_error",
                "status": "FAILURE",
                "task_id": task_id,
                "error": error_msg
            })
            
            raise ValueError(error_msg)
        
        # Update state: collector instantiated
        self.update_state(
            state="PROCESSING",
            meta={
                "collector_type": collector_type,
                "target": target,
                "status": f"Running {collector_class.__name__}...",
            }
        )
        
        # Publish progress
        publish_to_redis(task_id, {
            "type": "task_progress",
            "status": "PROCESSING",
            "task_id": task_id,
            "message": f"Running {collector_class.__name__}...",
            "progress": 30
        })
        
        # Instantiate collector
        collector = collector_class()
        logger.info(f"Instantiated {collector_class.__name__}")
        
        # Run the async collect method
        # Since Celery workers are synchronous, we need to run the async method in an event loop
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Create new event loop if none exists
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Publish progress
        publish_to_redis(task_id, {
            "type": "task_progress",
            "status": "PROCESSING",
            "task_id": task_id,
            "message": f"Collecting data from {target}...",
            "progress": 50
        })
        
        # Execute the async collect method
        logger.info(f"Executing collection for target: {target}")
        result: CollectorResult = loop.run_until_complete(collector.collect(target))
        
        # Serialize the result
        result_dict = result.model_dump()
        logger.info(f"Collection completed: success={result.success}")
        
        # Update final state with progress
        self.update_state(
            state="PROCESSING",
            meta={
                "collector_type": collector_type,
                "target": target,
                "status": "Processing complete, finalizing results...",
                "success": result.success,
            }
        )
        
        # Publish near-completion progress
        publish_to_redis(task_id, {
            "type": "task_progress",
            "status": "PROCESSING",
            "task_id": task_id,
            "message": "Finalizing results...",
            "progress": 90
        })
        
        # Publish final SUCCESS result (will be sent by on_success hook)
        logger.info(f"Task {task_id} completed successfully")
        
        return result_dict
    
    except ValueError as e:
        # Invalid collector type - don't retry
        logger.error(f"ValueError in scan task: {e}")
        
        error_result = {
            "id": None,
            "collector_name": collector_type,
            "target": target,
            "success": False,
            "data": {},
            "error": str(e),
            "timestamp": None,
            "metadata": {"task_id": self.request.id}
        }
        
        # Publish error
        publish_to_redis(task_id, {
            "type": "task_error",
            "status": "FAILURE",
            "task_id": task_id,
            "error": str(e),
            "result": error_result
        })
        
        return error_result
    
    except Exception as e:
        # Unexpected error - retry with exponential backoff
        logger.error(f"Unexpected error in scan task: {e}", exc_info=True)
        
        # Publish retry notification
        publish_to_redis(task_id, {
            "type": "task_retry",
            "status": "RETRY",
            "task_id": task_id,
            "error": str(e),
            "retry_count": self.request.retries
        })
        
        # Retry the task
        try:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            # Max retries exceeded, return error result
            logger.error(f"Max retries exceeded for task {self.request.id}")
            
            error_result = {
                "id": None,
                "collector_name": collector_type,
                "target": target,
                "success": False,
                "data": {},
                "error": f"Task failed after {self.max_retries} retries: {str(e)}",
                "timestamp": None,
                "metadata": {
                    "task_id": self.request.id,
                    "retries": self.request.retries
                }
            }
            
            # Publish final failure
            publish_to_redis(task_id, {
                "type": "task_failed",
                "status": "FAILURE",
                "task_id": task_id,
                "error": f"Max retries exceeded: {str(e)}",
                "result": error_result
            })
            
            return error_result


@celery_app.task(name="app.tasks.scan_tasks.health_check")
def health_check() -> Dict[str, str]:
    """
    Health check task for monitoring Celery workers.
    """
    return {
        "status": "healthy",
        "service": "celery-worker",
        "message": "Worker is operational"
    }
