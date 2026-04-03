from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime, timezone
from bson import ObjectId
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Import emergent integrations
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, 
    CheckoutSessionResponse, 
    CheckoutStatusResponse, 
    CheckoutSessionRequest
)

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = MongoClient(MONGO_URL)
db = client["ai_money_maker"]
jobs_collection = db["jobs"]
completed_work_collection = db["completed_work"]
payment_transactions_collection = db["payment_transactions"]

# API Keys
EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "sk_test_emergent")

# Pydantic Models
class Job(BaseModel):
    title: str
    description: str
    job_type: str  # "blog_post", "product_description", "social_media", etc.
    word_count: int
    price_gbp: float
    status: str = "available"  # available, in_progress, completed
    created_at: Optional[datetime] = None

class CompletedWork(BaseModel):
    job_id: str
    job_title: str
    generated_content: str
    word_count: int
    earnings_gbp: float
    completed_at: Optional[datetime] = None

class PaymentRequest(BaseModel):
    amount: float
    origin_url: str
    metadata: Optional[Dict[str, str]] = None

class Stats(BaseModel):
    total_earnings_gbp: float
    jobs_completed: int
    jobs_available: int
    today_earnings: float
    this_week_earnings: float

# Helper function to convert ObjectId to string
def serialize_doc(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

# Initialize sample jobs if database is empty
def init_sample_jobs():
    if jobs_collection.count_documents({}) == 0:
        sample_jobs = [
            {
                "title": "Blog Post: Benefits of Digital Marketing",
                "description": "Write a 500-word blog post about the benefits of digital marketing for small businesses",
                "job_type": "blog_post",
                "word_count": 500,
                "price_gbp": 25.00,
                "status": "available",
                "created_at": datetime.now(timezone.utc)
            },
            {
                "title": "Product Description: Eco-Friendly Water Bottle",
                "description": "Create a compelling 200-word product description for an eco-friendly water bottle",
                "job_type": "product_description",
                "word_count": 200,
                "price_gbp": 15.00,
                "status": "available",
                "created_at": datetime.now(timezone.utc)
            },
            {
                "title": "Social Media Campaign: Fitness App Launch",
                "description": "Write 5 engaging social media posts (100 words each) for a new fitness app launch",
                "job_type": "social_media",
                "word_count": 500,
                "price_gbp": 30.00,
                "status": "available",
                "created_at": datetime.now(timezone.utc)
            },
            {
                "title": "Email Marketing: Summer Sale Announcement",
                "description": "Create a 300-word email marketing campaign for a summer sale event",
                "job_type": "email_marketing",
                "word_count": 300,
                "price_gbp": 20.00,
                "status": "available",
                "created_at": datetime.now(timezone.utc)
            },
            {
                "title": "Article: Future of AI in Business",
                "description": "Write an informative 800-word article about the future of AI in business",
                "job_type": "article",
                "word_count": 800,
                "price_gbp": 40.00,
                "status": "available",
                "created_at": datetime.now(timezone.utc)
            }
        ]
        jobs_collection.insert_many(sample_jobs)
        print("Sample jobs initialized")

# Initialize jobs on startup
init_sample_jobs()

# Root endpoint
@app.get("/")
async def root():
    return {"message": "AI Money Maker API is running"}

# Get available jobs
@app.get("/api/jobs/available")
async def get_available_jobs():
    jobs = list(jobs_collection.find({"status": "available"}).sort("created_at", -1))
    return [serialize_doc(job) for job in jobs]

# Get job by ID
@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    try:
        job = jobs_collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return serialize_doc(job)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Execute job with AI
@app.post("/api/jobs/execute/{job_id}")
async def execute_job(job_id: str):
    try:
        # Get job
        job = jobs_collection.find_one({"_id": ObjectId(job_id)})
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job["status"] != "available":
            raise HTTPException(status_code=400, detail="Job is not available")
        
        # Update status to in_progress
        jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": "in_progress"}}
        )
        
        # Generate content using GPT-5.2
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"job_{job_id}",
            system_message="You are a professional marketing copywriter. Create high-quality, engaging content that meets the client's requirements exactly."
        ).with_model("openai", "gpt-5.2")
        
        # Create prompt based on job details
        prompt = f"""Create {job['job_type'].replace('_', ' ')} content with the following requirements:
        
Title: {job['title']}
Description: {job['description']}
Target word count: {job['word_count']} words

Please write professional, engaging content that exactly matches these requirements. Only provide the content, no additional explanations."""
        
        user_message = UserMessage(text=prompt)
        generated_content = await chat.send_message(user_message)
        
        # Save completed work
        completed_work = {
            "job_id": job_id,
            "job_title": job["title"],
            "generated_content": generated_content,
            "word_count": job["word_count"],
            "earnings_gbp": job["price_gbp"],
            "completed_at": datetime.now(timezone.utc)
        }
        completed_work_collection.insert_one(completed_work)
        
        # Update job status
        jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": "completed"}}
        )
        
        return {
            "success": True,
            "message": "Job completed successfully",
            "earnings_gbp": job["price_gbp"],
            "content_preview": generated_content[:200] + "..."
        }
        
    except Exception as e:
        # Revert status if error
        jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": "available"}}
        )
        raise HTTPException(status_code=500, detail=f"Error executing job: {str(e)}")

# Get statistics
@app.get("/api/stats")
async def get_stats():
    from datetime import timedelta
    
    # Total earnings
    completed_works = list(completed_work_collection.find({}))
    total_earnings = sum([work["earnings_gbp"] for work in completed_works])
    
    # Jobs completed
    jobs_completed = len(completed_works)
    
    # Jobs available
    jobs_available = jobs_collection.count_documents({"status": "available"})
    
    # Today's earnings
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_works = []
    for w in completed_works:
        if w.get("completed_at"):
            # Make sure the datetime is timezone-aware
            completed_at = w["completed_at"]
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=timezone.utc)
            if completed_at >= today_start:
                today_works.append(w)
    today_earnings = sum([work["earnings_gbp"] for work in today_works])
    
    # This week's earnings (last 7 days)
    week_start = datetime.now(timezone.utc) - timedelta(days=7)
    week_works = []
    for w in completed_works:
        if w.get("completed_at"):
            # Make sure the datetime is timezone-aware
            completed_at = w["completed_at"]
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=timezone.utc)
            if completed_at >= week_start:
                week_works.append(w)
    this_week_earnings = sum([work["earnings_gbp"] for work in week_works])
    
    return {
        "total_earnings_gbp": round(total_earnings, 2),
        "jobs_completed": jobs_completed,
        "jobs_available": jobs_available,
        "today_earnings": round(today_earnings, 2),
        "this_week_earnings": round(this_week_earnings, 2)
    }

# Get work history
@app.get("/api/work/history")
async def get_work_history():
    works = list(completed_work_collection.find({}).sort("completed_at", -1).limit(50))
    return [serialize_doc(work) for work in works]

# Get specific completed work
@app.get("/api/work/{work_id}")
async def get_completed_work(work_id: str):
    try:
        work = completed_work_collection.find_one({"_id": ObjectId(work_id)})
        if not work:
            raise HTTPException(status_code=404, detail="Work not found")
        return serialize_doc(work)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Stripe Payment Integration
@app.post("/api/payments/create-session")
async def create_payment_session(request: Request, payment_request: PaymentRequest):
    try:
        # Create success and cancel URLs
        origin_url = payment_request.origin_url
        success_url = f"{origin_url}?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{origin_url}?payment=cancelled"
        
        # Initialize Stripe checkout
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        # Create checkout session request
        checkout_request = CheckoutSessionRequest(
            amount=payment_request.amount,
            currency="gbp",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=payment_request.metadata or {"source": "ai_money_maker"}
        )
        
        # Create session
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Save transaction to database
        transaction = {
            "session_id": session.session_id,
            "amount": payment_request.amount,
            "currency": "gbp",
            "status": "pending",
            "payment_status": "initiated",
            "metadata": payment_request.metadata or {},
            "created_at": datetime.now(timezone.utc)
        }
        payment_transactions_collection.insert_one(transaction)
        
        return {
            "url": session.url,
            "session_id": session.session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating payment session: {str(e)}")

# Get payment status
@app.get("/api/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request):
    try:
        # Initialize Stripe checkout
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        # Get status from Stripe
        checkout_status = await stripe_checkout.get_checkout_status(session_id)
        
        # Update database
        existing_transaction = payment_transactions_collection.find_one({"session_id": session_id})
        
        if existing_transaction:
            # Only update if not already processed as paid
            if existing_transaction.get("payment_status") != "paid":
                payment_transactions_collection.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "status": checkout_status.status,
                        "payment_status": checkout_status.payment_status,
                        "updated_at": datetime.now(timezone.utc)
                    }}
                )
        
        return {
            "session_id": session_id,
            "status": checkout_status.status,
            "payment_status": checkout_status.payment_status,
            "amount_total": checkout_status.amount_total,
            "currency": checkout_status.currency
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting payment status: {str(e)}")

# Stripe webhook
@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    try:
        # Get webhook body and signature
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        # Initialize Stripe checkout
        host_url = str(request.base_url).rstrip('/')
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        
        # Handle webhook
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Update transaction in database
        if webhook_response.session_id:
            existing_transaction = payment_transactions_collection.find_one(
                {"session_id": webhook_response.session_id}
            )
            
            if existing_transaction and existing_transaction.get("payment_status") != "paid":
                payment_transactions_collection.update_one(
                    {"session_id": webhook_response.session_id},
                    {"$set": {
                        "payment_status": webhook_response.payment_status,
                        "event_type": webhook_response.event_type,
                        "updated_at": datetime.now(timezone.utc)
                    }}
                )
        
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
