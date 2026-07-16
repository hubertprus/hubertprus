"""
Vertex Quant Core - Google Cloud Tasks & Pub/Sub Client
Provides asynchronous task enqueuing to wake up Cloud Run containers
precisely when new jobs arrive, and spin them down after execution.
"""

import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Try to import Google Cloud Tasks and Pub/Sub packages
try:
    from google.cloud import tasks_v2
    from google.cloud import pubsub_v1
    GCP_SERVICES_AVAILABLE = True
except ImportError:
    GCP_SERVICES_AVAILABLE = False
    logger.warning("google-cloud-tasks or google-cloud-pubsub packages not found. Falling back to simulation.")

GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "europe-west1")
TASKS_QUEUE_NAME = "vertex-quant-jobs-queue"
TELEMETRY_TOPIC_NAME = "vertex-quant-telemetry"


class GCPTasksClient:
    """Client for managing asynchronous queueing in Google Cloud Tasks."""

    def __init__(self, project_id: Optional[str] = None, region: Optional[str] = None):
        self.project_id = project_id or GCP_PROJECT
        self.region = region or GCP_REGION
        self.client = None

        if GCP_SERVICES_AVAILABLE and self.project_id:
            try:
                self.client = tasks_v2.CloudTasksClient()
                logger.info(f"Cloud Tasks Client initialized for project {self.project_id} in {self.region}")
            except Exception as e:
                logger.error(f"Failed to initialize Cloud Tasks Client: {e}")
                self.client = None

    def enqueue_job_execution(self, job_id: str, target_url: str) -> Optional[str]:
        """
        Enqueues an asynchronous task in Cloud Tasks to trigger job execution.
        This automatically wakes up our Cloud Run container if it scaled to 0.
        """
        if self.client:
            try:
                parent = self.client.queue_path(self.project_id, self.region, TASKS_QUEUE_NAME)
                
                # Payload containing job ID to execute
                payload = {"job_id": job_id}
                
                # Configure HTTP POST request that wakes up Cloud Run
                task = {
                    "http_request": {
                        "http_method": tasks_v2.HttpMethod.POST,
                        "url": f"{target_url}/api/jobs/execute/{job_id}",
                        "headers": {"Content-Type": "application/json"},
                    }
                }

                response = self.client.create_task(request={"parent": parent, "task": task})
                logger.info(f"Task successfully enqueued: {response.name}")
                return response.name
            except Exception as e:
                logger.error(f"Error enqueuing task: {e}")
                return None
        else:
            logger.info(f"[SIMULATED CLOUD TASKS ENQUEUE] Task created for job: {job_id}. Target webhook: {target_url}/api/jobs/execute/{job_id}")
            return f"mock-task-id-for-{job_id}"


class GCPPubSubClient:
    """Client for sending telemetry events and cost control via Pub/Sub."""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or GCP_PROJECT
        self.publisher = None

        if GCP_SERVICES_AVAILABLE and self.project_id:
            try:
                self.publisher = pubsub_v1.PublisherClient()
                logger.info(f"Pub/Sub Publisher Client initialized for project {self.project_id}")
            except Exception as e:
                logger.error(f"Failed to initialize Pub/Sub client: {e}")
                self.publisher = None

    def publish_event(self, event_type: str, data: Dict[str, Any]) -> Optional[str]:
        """Publishes an event (e.g., job completion, cost alert) to Pub/Sub."""
        if self.publisher:
            try:
                topic_path = self.publisher.topic_path(self.project_id, TELEMETRY_TOPIC_NAME)
                
                # Prepare payload
                payload = {
                    "event_type": event_type,
                    "timestamp": os.getenv("CURRENT_DATETIME", "2026-07-16T12:50:00Z"),
                    "data": data
                }
                data_bytes = json.dumps(payload).encode("utf-8")

                future = self.publisher.publish(topic_path, data_bytes)
                message_id = future.result()
                logger.info(f"Pub/Sub message published: {message_id}")
                return message_id
            except Exception as e:
                logger.error(f"Error publishing to Pub/Sub: {e}")
                return None
        else:
            logger.info(f"[SIMULATED PUB/SUB PUBLISH] Published event '{event_type}' with data: {data}")
            return f"mock-message-id-{event_type}"
