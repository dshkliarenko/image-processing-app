# Image Feature Detection Service

A REST API service for image feature detection using SIFT algorithm with MongoDB caching and Docker deployment.

## Overview

This service utilizes `FeatureDetector` class for REST API that:
- Processes images using OpenCV SIFT feature detection
- Caches results in MongoDB to avoid reprocessing
- Provides asynchronous request handling
- Includes service health checking
- Runs in Docker containers for easy deployment

## Architecture

- **FastAPI**: Asynchronous REST API framework
- **MongoDB**: Database for caching results and logging requests
- **Docker Compose**: Container orchestration for easy deployment
- **FeatureDetector**: Class for SIFT-based feature detection

## Prerequisites

- Docker and Docker Compose installed
- At least 2GB RAM available for containers
- Port 8000 and 27017 available on your system

## Quick Start

1. **Clone and navigate to the project:**
   ```bash
   cd image-processing-app
   ```

2. **Build and start the services:**
   ```bash
   docker-compose up --build
   ```

3. **Wait for warmup completion:**
   The FeatureDetector requires a 5-second warmup. Check status:
   ```bash
   curl http://localhost:8000/check-status
   ```

4. **Process an image:**
   ```bash
   curl -X POST "http://localhost:8000/process-image" \
        -H "accept: application/json" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@path/to/your/image.jpg"
   ```

## API Endpoints

### GET `/check-status`
Returns service readiness and warmup status.

**Response:**
```json
{
  "service_ready": true,
  "detector_ready": true,
  "warmup_completed": true,
  "uptime_seconds": 120.5
}
```

### POST `/process-image`
Process an image file and return feature detection results.

**Parameters:**
- `file`: Image file (multipart/form-data)

**Response:**
```json
{
  "success": true,
  "image_hash": "sha256_hash",
  "filename": "example.jpg",
  "result": {
    "keypoints": 245,
    "descriptors": [245, 128]
  },
  "processing_time": 1.23,
  "cache_hit": false,
  "timestamp": "2024-01-01T12:00:00"
}
```

## Development

### Local Development Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start MongoDB:**
   ```bash
   docker run -d -p 27017:27017 --name mongo mongo:latest
   ```

3. **Set environment variables:**
   ```bash
   export MONGODB_URL=mongodb://localhost:27017
   export DATABASE_NAME=image_processing_db
   export COLLECTION_NAME=image_results
   ```

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Testing the Service

1. **Health check:**
   ```bash
   curl http://localhost:8000/check-status
   ```

2. **Process a test image:**
   ```bash
   # Create a simple test image (requires ImageMagick)
   convert -size 100x100 xc:white -fill black -draw "circle 50,50 30,30" test.jpg

   # Process the image
   curl -X POST "http://localhost:8000/process-image" \
        -H "Content-Type: multipart/form-data" \
        -F "file=@test.jpg"
   ```

3. **Test caching (process the same image again):**
   The second request should return faster with `"cache_hit": true`

## Docker Commands

- **Build and start:** `docker-compose up --build`
- **Start in background:** `docker-compose up -d`
- **View logs:** `docker-compose logs -f api`
- **Stop services:** `docker-compose down`
- **Remove volumes:** `docker-compose down -v`

## Configuration

Environment variables (set in `.env` or docker-compose.yml):
- `MONGODB_URL`: MongoDB connection string
- `DATABASE_NAME`: Database name for storing results
- `COLLECTION_NAME`: Collection name for image results

## Monitoring

- **API Logs:** `docker-compose logs api`
- **MongoDB Logs:** `docker-compose logs mongo`
- **Database Contents:** Use MongoDB Compass or mongo shell to inspect cached results

## Troubleshooting

1. **Service not ready:**
   - Wait for the 5-second warmup period
   - Check logs: `docker-compose logs api`

2. **Image processing fails:**
   - Ensure image file is valid and readable
   - Check OpenCV dependencies in container

3. **Database connection issues:**
   - Verify MongoDB is running: `docker-compose ps`
   - Check MongoDB logs: `docker-compose logs mongo`

4. **Port conflicts:**
   - Change ports in docker-compose.yml if 8000 or 27017 are in use

## Performance Notes

- First-time image processing takes ~1-3 seconds
- Cached results return in milliseconds
- Service supports concurrent requests via async processing
- Thread pool handles CPU-bound operations efficiently