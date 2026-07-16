import os
import sys
import pytest
from fastapi.testclient import TestClient

# Use mock MongoDB client for offline/sandbox testing
os.environ["MOCK_MONGO"] = "true"

# Ensure backend path is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from backend.server import app

client = TestClient(app)

def test_root_endpoint():
    """Test that root endpoint returns the Cyber Gold HTML dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Maszyna Viralowa" in response.text
    assert "Cyber Gold" in response.text or "cyber-gold" in response.text
    assert "binaryRain" in response.text

def test_viral_ingest_endpoint():
    """Test the Fiverr brief ingestion and scene extraction endpoint."""
    brief_data = {
        "brief": "Potrzebuję luksusowej reklamy napoju bezalkoholowego z motywem złota i neonu, 3 sceny."
    }
    response = client.post("/api/viral/ingest", json=brief_data)
    assert response.status_code == 200
    data = response.json()
    assert "project_name" in data
    assert "mood" in data
    assert "style" in data
    assert "scenes" in data
    assert len(data["scenes"]) > 0
    assert data["scenes"][0]["scene_number"] == 1
    assert "visual_prompt" in data["scenes"][0]

def test_viral_generate_graphics_endpoint():
    """Test vertical graphics and video generation in H.265 container."""
    graphics_data = {
        "scene_index": 0,
        "visual_prompt": "Futuristic 3D gold can floating in black liquid, high contrast",
        "project_name": "GoldImpulse"
    }
    response = client.post("/api/viral/generate-graphics", json=graphics_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "file_name" in data
    assert data["resolution"] == "1080x1920"
    
    # Verify the simulated file is actually created
    file_name = data["file_name"]
    download_response = client.get(f"/api/viral/download/{file_name}")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "video/mp4"

def test_viral_optimize_reach_endpoint():
    """Test description, title and hashtag optimization for social media."""
    optimize_data = {
        "project_name": "GoldImpulse",
        "mood": "Energetic, Luxury",
        "style": "Cyber Gold, 3D",
        "scenes_summary": "Floating can with golden sparkles"
    }
    response = client.post("/api/viral/optimize-reach", json=optimize_data)
    assert response.status_code == 200
    data = response.json()
    assert "optimized_title" in data
    assert "optimized_description" in data
    assert "optimized_tags" in data

def test_viral_audio_brief_endpoint():
    """Test lektor audio briefing generation and download."""
    audio_data = {
        "project_name": "GoldImpulse",
        "mood": "Energetic, Luxury",
        "style": "Cyber Gold"
    }
    response = client.post("/api/viral/audio-brief", json=audio_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "audio_url" in data
    assert "brief_text" in data
    
    # Extract filename from url
    audio_url = data["audio_url"]
    file_name = audio_url.split("/")[-1]
    
    # Verify the audio file download works
    download_response = client.get(f"/api/viral/audio/{file_name}")
    assert download_response.status_code == 200
    assert download_response.headers["content-type"] == "audio/mpeg"
