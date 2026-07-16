"""
Vertex Quant Core - Cost & Billing Protection Monitor
Handles automatic and secure cloud resource shutdown when expenditures
exceed pre-defined safety limits, protecting free GCP credits.
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Daily safety cap (e.g. maximum permitted spending in GBP per day)
DAILY_BUDGET_CAP_GBP = float(os.getenv("DAILY_BUDGET_CAP_GBP", "10.0"))


class GCPCostMonitor:
    """Cost monitoring manager to protect free GCP credits."""

    def __init__(self, db_client=None):
        self.state_file = "/tmp/gcp_cost_state.json"
        self.collection = None
        
        # Enable persistent storage via MongoDB if available
        if db_client is not None:
            try:
                self.collection = db_client["gcp_cost_state"]
                logger.info("GCPCostMonitor initialized with MongoDB persistent storage.")
            except Exception as e:
                logger.warning(f"Failed to use MongoDB for cost storage: {e}. Falling back to file storage.")
                self.collection = None

        self._init_state()

    def _init_state(self):
        """Initializes cost state store if it does not exist."""
        if self.collection:
            try:
                if self.collection.count_documents({}) == 0:
                    initial_state = {
                        "_id": "current_costs",
                        "daily_spend_gbp": 0.0,
                        "total_spend_gbp": 0.0,
                        "last_updated": os.getenv("CURRENT_DATETIME", "2026-07-16T12:00:00Z"),
                        "kill_switch_active": False
                    }
                    self.collection.insert_one(initial_state)
            except Exception as e:
                logger.error(f"Error initializing MongoDB cost state: {e}")
        else:
            if not os.path.exists(self.state_file):
                initial_state = {
                    "daily_spend_gbp": 0.0,
                    "total_spend_gbp": 0.0,
                    "last_updated": os.getenv("CURRENT_DATETIME", "2026-07-16T12:00:00Z"),
                    "kill_switch_active": False
                }
                self._save_state(initial_state)

    def _read_state(self) -> Dict[str, Any]:
        if self.collection:
            try:
                doc = self.collection.find_one({"_id": "current_costs"})
                if doc:
                    return doc
            except Exception as e:
                logger.error(f"Error reading MongoDB cost state: {e}")

        # Fallback to local file storage
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except Exception:
            return {
                "daily_spend_gbp": 0.0,
                "total_spend_gbp": 0.0,
                "last_updated": os.getenv("CURRENT_DATETIME", "2026-07-16T12:00:00Z"),
                "kill_switch_active": False
            }

    def _save_state(self, state: Dict[str, Any]):
        if self.collection:
            try:
                # Ensure _id is present for MongoDB
                state["_id"] = "current_costs"
                self.collection.replace_one({"_id": "current_costs"}, state, upsert=True)
                return
            except Exception as e:
                logger.error(f"Error replacing MongoDB cost state: {e}")

        # Fallback to local file storage
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cost state file: {e}")

    def track_llm_cost(self, prompt_tokens: int, completion_tokens: int, model_name: str):
        """
        Calculates and logs approximate token cost for Gemini 2.5 Flash
        to update daily spending metrics in real-time.
        """
        # Gemini 2.5 Flash ultra-cheap input/output token pricing:
        # Input: $0.075 / 1M tokens (~£0.06)
        # Output: $0.30 / 1M tokens (~£0.24)
        input_rate = 0.00000006  # GBP per token
        output_rate = 0.00000024 # GBP per token

        cost = (prompt_tokens * input_rate) + (completion_tokens * output_rate)
        
        state = self._read_state()
        state["daily_spend_gbp"] += cost
        state["total_spend_gbp"] += cost
        state["last_updated"] = os.getenv("CURRENT_DATETIME", "2026-07-16T12:00:00Z")

        # Budget ceiling check
        if state["daily_spend_gbp"] >= DAILY_BUDGET_CAP_GBP:
            state["kill_switch_active"] = True
            logger.critical(
                f"🚨 CRITICAL: GCP Daily budget cap of £{DAILY_BUDGET_CAP_GBP} exceeded! "
                f"Current daily spend: £{state['daily_spend_gbp']:.4f}. Activating Cloud Kill Switch!"
            )
        else:
            logger.info(f"Cost tracked: +£{cost:.6f}. Current daily spend: £{state['daily_spend_gbp']:.4f}")

        self._save_state(state)

    def is_kill_switch_active(self) -> bool:
        """Checks whether system should block calls due to cost overrun."""
        state = self._read_state()
        return state.get("kill_switch_active", False)

    def handle_pubsub_billing_alert(self, pubsub_message: Dict[str, Any]):
        """
        Processes pub/sub messages from Google Cloud Billing Budgets.
        Allows instant and automated Cloud Run / GCE spot VM deactivations.
        """
        try:
            cost_amount = pubsub_message.get("costAmount", 0.0)
            budget_amount = pubsub_message.get("budgetAmount", 200.0)
            
            logger.info(f"Received Google Billing Alert: Spent £{cost_amount} of £{budget_amount}")

            if cost_amount >= budget_amount:
                state = self._read_state()
                state["kill_switch_active"] = True
                self._save_state(state)
                logger.critical("🔥 GCP BILLING LIMIT REACHED! Cloud Kill Switch is now PERMANENTLY ACTIVE.")
        except Exception as e:
            logger.error(f"Error parsing billing alert message: {e}")

    def reset_daily_budget(self):
        """Resets daily cost tracking metrics and resets Kill Switch."""
        state = self._read_state()
        state["daily_spend_gbp"] = 0.0
        state["kill_switch_active"] = False
        state["last_updated"] = os.getenv("CURRENT_DATETIME", "2026-07-16T12:00:00Z")
        self._save_state(state)
        logger.info("Daily budget counters reset successfully.")
