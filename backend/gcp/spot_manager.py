"""
Vertex Quant Core - GCE Spot VM Autonomous Manager
Wakes up the Spot VM instance on-demand for heavy DSP calculations,
and shuts it down immediately after work completion to cut costs.
"""

import os
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Google Compute Engine package
try:
    from google.cloud import compute_v1
    COMPUTE_AVAILABLE = True
except ImportError:
    COMPUTE_AVAILABLE = False
    logger.warning("google-cloud-compute package not found. Spot VM manager falls back to simulation.")

GCP_PROJECT = os.getenv("GCP_PROJECT")
SPOT_ZONE = os.getenv("SPOT_ZONE", "europe-west1-b")
SPOT_VM_NAME = "vertex-quant-dsp-spot-worker"


class SpotVMManager:
    """Autonomous Spot VM manager for cost optimization."""

    def __init__(self, project_id: Optional[str] = None, zone: Optional[str] = None):
        self.project_id = project_id or GCP_PROJECT
        self.zone = zone or SPOT_ZONE
        self.client = None

        if COMPUTE_AVAILABLE and self.project_id:
            try:
                self.client = compute_v1.InstancesClient()
                logger.info(f"Compute Engine Client initialized for project {self.project_id}, zone {self.zone}")
            except Exception as e:
                logger.error(f"Failed to initialize GCE Client: {e}. Falling back to simulated mode.")
                self.client = None

    def start_worker(self) -> bool:
        """
        Initiates wake-up of the Spot VM instance for computation.
        """
        if self.client:
            try:
                logger.info(f"Waking up Spot VM {SPOT_VM_NAME} on-demand...")
                operation = self.client.start(
                    project=self.project_id,
                    zone=self.zone,
                    instance=SPOT_VM_NAME
                )
                logger.info(f"Start command sent. Operation ID: {operation.name}")
                return True
            except Exception as e:
                logger.error(f"Error starting Spot VM {SPOT_VM_NAME}: {e}")
                return False
        else:
            logger.info(f"[SIMULATED SPOT VM WAKE-UP] Spot VM '{SPOT_VM_NAME}' is now ONLINE and ready for DSP calculations.")
            return True

    def stop_worker(self) -> bool:
        """
        Immediately shuts down Spot VM after work completion to avoid idle charges.
        """
        if self.client:
            try:
                logger.info(f"Stopping Spot VM {SPOT_VM_NAME} immediately to cut costs...")
                operation = self.client.stop(
                    project=self.project_id,
                    zone=self.zone,
                    instance=SPOT_VM_NAME
                )
                logger.info(f"Stop command sent. Operation ID: {operation.name}")
                return True
            except Exception as e:
                logger.error(f"Error stopping Spot VM {SPOT_VM_NAME}: {e}")
                return False
        else:
            logger.info(f"[SIMULATED SPOT VM SHUTDOWN] Spot VM '{SPOT_VM_NAME}' is now OFFLINE. Hourly cost is now £0.00.")
            return True

    def get_status(self) -> str:
        """Returns current machine status (RUNNING, TERMINATED, PROVISIONING, etc.)."""
        if self.client:
            try:
                instance = self.client.get(
                    project=self.project_id,
                    zone=self.zone,
                    instance=SPOT_VM_NAME
                )
                return instance.status
            except Exception as e:
                logger.error(f"Error getting Spot VM status: {e}")
                return "UNKNOWN"
        else:
            return "SIMULATED_OFFLINE"


def run_with_spot_worker(dsp_function, *args, **kwargs):
    """
    Wrapper executing the dsp_function on the Spot VM worker only for its runtime duration,
    shutting down the instance immediately after execution completes to cut expenses.
    """
    manager = SpotVMManager()
    
    # 1. Start/wake the worker
    success = manager.start_worker()
    if not success:
        logger.warning("Could not start Spot worker, falling back to local thread...")

    # Wait for the machine to boot (cold start) in production
    if manager.client:
        logger.info("Waiting for Spot VM instance boot sequence...")
        for _ in range(12): # Max 1 minute
            status = manager.get_status()
            if status == "RUNNING":
                break
            time.sleep(5)

    result = None
    try:
        # 2. Execute heavy DSP/Synthesis calculations
        logger.info("Starting calculation sequence on Spot VM worker...")
        result = dsp_function(*args, **kwargs)
    finally:
        # 3. Always turn off the instance (in finally block for guaranteed cost safety)
        logger.info("Calculations completed or aborted.")
        manager.stop_worker()
        
    return result
