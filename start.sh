#!/bin/bash
# Start script for Maszyna Viralowa (Vertex Song) & AI Money Maker
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
uvicorn backend.server:app --host 0.0.0.0 --port 8000
