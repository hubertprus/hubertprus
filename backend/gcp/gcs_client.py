"""
Vertex Quant Core - Google Cloud Storage Client
Handles downloading and uploading of generated audio files, logs, and Solution Kits.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Google Cloud Storage package
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("google-cloud-storage package not found. GCS integration falls back to local storage simulation.")

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")


class GCSClient:
    """Client for interacting with Google Cloud Storage (GCS)."""

    def __init__(self, bucket_name: Optional[str] = None):
        self.bucket_name = bucket_name or GCS_BUCKET_NAME
        self.client = None
        self.bucket = None

        if GCS_AVAILABLE and self.bucket_name:
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
                logger.info(f"GCS Client initialized for bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to initialize GCS Client: {e}. Falling back to simulated local mode.")
                self.client = None

    def upload_file(self, local_file_path: str, destination_blob_name: str) -> Optional[str]:
        """
        Uploads local file to GCS Bucket.
        If GCS package/credentials are missing, falls back to simulated mock local save.
        """
        if not os.path.exists(local_file_path):
            logger.error(f"Local file does not exist: {local_file_path}")
            return None

        if self.bucket:
            try:
                blob = self.bucket.blob(destination_blob_name)
                blob.upload_from_filename(local_file_path)
                # Public URL (or gcs uri)
                gcs_url = f"https://storage.googleapis.com/{self.bucket_name}/{destination_blob_name}"
                logger.info(f"File uploaded to GCS successfully: {gcs_url}")
                return gcs_url
            except Exception as e:
                logger.error(f"Error uploading file to GCS: {e}")
                return None
        else:
            # Simulation mode
            simulated_url = f"file://{os.path.abspath(local_file_path)} [SIMULATED GCS: {destination_blob_name}]"
            logger.info(f"Mock upload file: Saved locally (Simulating GCS path: {simulated_url})")
            return simulated_url

    def upload_data(self, data: bytes, destination_blob_name: str, content_type: str = "application/octet-stream") -> Optional[str]:
        """Uploads raw bytes (e.g., generated audio on-the-fly) to GCS."""
        if self.bucket:
            try:
                blob = self.bucket.blob(destination_blob_name)
                blob.upload_from_string(data, content_type=content_type)
                gcs_url = f"https://storage.googleapis.com/{self.bucket_name}/{destination_blob_name}"
                logger.info(f"Data uploaded to GCS successfully: {gcs_url}")
                return gcs_url
            except Exception as e:
                logger.error(f"Error uploading data bytes to GCS: {e}")
                return None
        else:
            simulated_url = f"memory://raw_bytes [SIMULATED GCS: {destination_blob_name}]"
            logger.info(f"Mock upload data: Bytes accepted (Simulating GCS path: {simulated_url})")
            return simulated_url

    def download_file(self, blob_name: str, local_destination_path: str) -> bool:
        """Downloads file from GCS to local disk."""
        if self.bucket:
            try:
                blob = self.bucket.blob(blob_name)
                blob.download_to_filename(local_destination_path)
                logger.info(f"File {blob_name} downloaded successfully to {local_destination_path}")
                return True
            except Exception as e:
                logger.error(f"Error downloading from GCS: {e}")
                return False
        else:
            logger.info(f"Mock download: Simulating download for {blob_name} -> {local_destination_path}")
            return False
