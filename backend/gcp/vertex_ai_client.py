"""
Vertex Quant Core - Vertex AI Gemini Client
Uses the official Vertex AI SDK in Google Cloud to execute
LLM calls funded directly by GCP credits.
"""

import os
import json
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

try:
    # Google GenAI / Vertex AI SDK
    from google import genai
    from google.genai import types
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logger.warning("google-genai package not found. Vertex AI will fall back to simulation mode.")

GCP_PROJECT = os.getenv("GCP_PROJECT")
VERTEX_MODEL = os.getenv("VERTEX_MODEL", "gemini-2.5-flash") # Highly cost-effective and modern model


class VertexAIClient:
    """Vertex AI (Gemini) client optimized for cost savings (GCP Credits)."""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or GCP_PROJECT
        self.client = None

        if VERTEX_AI_AVAILABLE and self.project_id:
            try:
                # Initialize Google GenAI client configured for Vertex AI
                self.client = genai.Client(vertex=True, project=self.project_id)
                logger.info(f"Vertex AI Client initialized successfully for project: {self.project_id}")
            except Exception as e:
                logger.error(f"Failed to initialize Vertex AI client: {e}. Falling back to simulation mode.")
                self.client = None

    def generate_content(self, prompt: str, system_instruction: Optional[str] = None, json_output: bool = False) -> str:
        """
        Generates content using Gemini on the Vertex AI platform.
        Runs synchronously or asynchronously on demand.
        """
        if self.client:
            try:
                config = types.GenerateContentConfig()
                if system_instruction:
                    config.system_instruction = system_instruction
                
                if json_output:
                    config.response_mime_type = "application/json"

                response = self.client.models.generate_content(
                    model=VERTEX_MODEL,
                    contents=prompt,
                    config=config
                )
                return response.text
            except Exception as e:
                logger.error(f"Error generating content via Vertex AI: {e}")
                raise e
        else:
            # Fallback/mock mode for local development without credentials/credits
            logger.info("Vertex AI Client running in simulated mode.")
            if json_output:
                return json.dumps({
                    "simulated": True,
                    "model": VERTEX_MODEL,
                    "message": "This is a simulated response from Vertex AI Gemini",
                    "kick_pattern": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
                    "snare_pattern": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
                })
            return f"[SIMULATED VERTEX AI GEMINI response for prompt: {prompt[:30]}...]"

    def chat(self, message: str, history: Optional[List[Dict]] = None, system_instruction: Optional[str] = None) -> str:
        """Multi-turn conversation with agent."""
        if self.client:
            try:
                # Format history into structure accepted by SDK
                formatted_history = []
                if history:
                    for turn in history:
                        formatted_history.append(
                            types.Content(
                                role=turn.get("role", "user"),
                                parts=[types.Part.from_text(text=p) for p in turn.get("parts", [])]
                            )
                        )

                config = types.GenerateContentConfig()
                if system_instruction:
                    config.system_instruction = system_instruction

                # Initialize chat session on Vertex AI
                chat = self.client.chats.create(model=VERTEX_MODEL, history=formatted_history, config=config)
                response = chat.send_message(message)
                return response.text
            except Exception as e:
                logger.error(f"Error in Vertex AI Chat: {e}")
                raise e
        else:
            return f"[SIMULATED VERTEX AI CHAT response for message: {message}]"
