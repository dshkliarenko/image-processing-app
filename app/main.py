from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import os
import time
import tempfile
from datetime import datetime
from contextlib import asynccontextmanager

from .database import (
    connect_to_mongo,
    close_mongo_connection,
    get_cached_result,
    save_processing_result,
    log_request,
    calculate_image_hash
)
from .models import ProcessImageResponse, StatusResponse, ErrorResponse
from .feature_detector import FeatureDetector

# Global detector instance
detector = FeatureDetector()
start_time = time.time()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    print("Starting FeatureDetector warmup...")
    await detector.warmup()
    print("FeatureDetector warmup completed")
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="Image Feature Detection Service",
    description="REST API for image feature detection using SIFT algorithm with MongoDB caching",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Image Feature Detection API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": ["/process-image", "/check-status"]
    }

@app.post("/process-image", response_model=ProcessImageResponse)
async def process_image(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Process an image file and return feature detection results"""

    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

    try:
        # Read image data
        image_data = await file.read()
        if not image_data:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Calculate image hash for caching
        image_hash = calculate_image_hash(image_data)

        start_time_processing = time.time()

        # Check cache first
        cached_result = await get_cached_result(image_hash)
        if cached_result:
            processing_time = time.time() - start_time_processing

            # Log request in background
            background_tasks.add_task(
                log_request,
                "process-image",
                image_hash,
                file.filename or "unknown",
                True,  # cache_hit
                processing_time
            )

            return ProcessImageResponse(
                success=True,
                image_hash=image_hash,
                filename=file.filename or "unknown",
                result=cached_result["result"],
                processing_time=processing_time,
                cache_hit=True,
                timestamp=datetime.utcnow()
            )

        # Check if service is ready
        if not detector.ready:
            raise HTTPException(
                status_code=503,
                detail="Service not ready. Please wait for warmup to complete."
            )

        # Save image to temporary file for processing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(image_data)
            temp_file_path = temp_file.name

        try:
            # Process image
            result = await detector.process_image(temp_file_path)
            processing_time = time.time() - start_time_processing

            # Save result to database in background
            background_tasks.add_task(
                save_processing_result,
                image_hash,
                file.filename or "unknown",
                result,
                processing_time
            )

            # Log request in background
            background_tasks.add_task(
                log_request,
                "process-image",
                image_hash,
                file.filename or "unknown",
                False,  # cache_hit
                processing_time
            )

            return ProcessImageResponse(
                success=True,
                image_hash=image_hash,
                filename=file.filename or "unknown",
                result=result,
                processing_time=processing_time,
                cache_hit=False,
                timestamp=datetime.utcnow()
            )

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    except Exception as e:
        # Log error request
        background_tasks.add_task(
            log_request,
            "process-image",
            image_hash if 'image_hash' in locals() else "unknown",
            file.filename or "unknown",
            False,
            0.0,
            "error"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )

@app.get("/check-status", response_model=StatusResponse)
async def check_status():
    """Check service readiness and warmup status"""
    current_time = time.time()
    uptime = current_time - start_time

    return StatusResponse(
        service_ready=True,
        detector_ready=detector.ready,
        warmup_completed=detector.ready,
        uptime_seconds=uptime
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            details=f"Path: {request.url.path}"
        ).dict()
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=os.getenv("API_PORT", 8000),
        reload=True
    )