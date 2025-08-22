from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv

from auth.google_auth import GoogleAuthHandler
from services.gmail_service import GmailService
from services.email_parser import EmailParser
from services.transaction_extractor import TransactionExtractor
from services.intelligent_extractor import IntelligentExtractor
from services.analytics_service import AnalyticsService
from services.email_classifier import EmailClassifier
from services.async_processor import AsyncEmailProcessor

load_dotenv()

app = FastAPI(title="Email Transaction Parser", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize services
auth_handler = GoogleAuthHandler()
gmail_service = GmailService()
email_parser = EmailParser()
transaction_extractor = TransactionExtractor()
intelligent_extractor = IntelligentExtractor()
analytics_service = AnalyticsService()
email_classifier = EmailClassifier()
async_processor = AsyncEmailProcessor()

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")

@app.get("/auth/login")
async def login():
    auth_url = auth_handler.get_auth_url()
    return {"auth_url": auth_url}

@app.get("/auth/callback")
async def auth_callback(code: str):
    try:
        credentials = auth_handler.exchange_code_for_token(code)
        # Redirect back to frontend with access token in URL fragment
        return RedirectResponse(url=f"/static/index.html?access_token={credentials.token}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/emails/fetch")
async def fetch_emails(access_token: str):
    try:
        gmail_service.set_credentials(access_token)
        emails = gmail_service.fetch_emails_last_6_months()  # No limit
        parsed_emails = [email_parser.parse_email(email) for email in emails]
        return {"emails": parsed_emails, "count": len(parsed_emails)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/transactions/extract")
async def extract_transactions(access_token: str):
    try:
        gmail_service.set_credentials(access_token)
        emails = gmail_service.fetch_emails_last_6_months()  # No limit
        
        transactions = []
        for email in emails:
            parsed_email = email_parser.parse_email(email)
            extracted_transactions = transaction_extractor.extract_transactions(parsed_email)
            transactions.extend(extracted_transactions)
        
        return {"transactions": transactions, "count": len(transactions), "emails_processed": len(emails)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/insights/intelligent")
async def extract_intelligent_insights(access_token: str):
    try:
        gmail_service.set_credentials(access_token)
        emails = gmail_service.fetch_emails_last_6_months()  # No limit
        
        # Use credit card classifier to filter emails
        parsed_emails = [email_parser.parse_email(email) for email in emails]
        classified = email_classifier.classify_emails_batch(parsed_emails)
        
        # Process only credit card related emails
        relevant_emails = classified["definitely_financial"] + classified["maybe_financial"]
        
        extracted_data = []
        for parsed_email in relevant_emails:
            insights = intelligent_extractor.extract_financial_insights(
                parsed_email.get('bodyText', ''),
                parsed_email.get('from', ''),
                parsed_email.get('subject', '')
            )
            insights['email_id'] = parsed_email.get('id')
            extracted_data.append(insights)
        
        stats = email_classifier.get_classification_stats(classified)
        return {
            "insights": extracted_data, 
            "emails_processed": len(emails), 
            "credit_card_emails_analyzed": len(relevant_emails),
            "optimization_stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/analytics/comprehensive")
async def get_comprehensive_analytics(access_token: str):
    try:
        gmail_service.set_credentials(access_token)
        emails = gmail_service.fetch_emails_last_6_months()  # No limit
        
        # Use credit card classifier to filter emails
        parsed_emails = [email_parser.parse_email(email) for email in emails]
        classified = email_classifier.classify_emails_batch(parsed_emails)
        
        # Process only credit card related emails
        relevant_emails = classified["definitely_financial"] + classified["maybe_financial"]
        
        extracted_data = []
        for parsed_email in relevant_emails:
            insights = intelligent_extractor.extract_financial_insights(
                parsed_email.get('bodyText', ''),
                parsed_email.get('from', ''),
                parsed_email.get('subject', '')
            )
            insights['email_id'] = parsed_email.get('id')
            extracted_data.append(insights)
        
        # Generate comprehensive analytics
        analytics = analytics_service.generate_comprehensive_insights(extracted_data)
        
        stats = email_classifier.get_classification_stats(classified)
        return {
            "analytics": analytics,
            "metadata": {
                "emails_processed": len(emails),
                "credit_card_emails": len(relevant_emails),
                "optimization_stats": stats,
                "processing_date": "2025-08-21"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# NEW OPTIMIZED ENDPOINTS

@app.get("/insights/optimized")
async def extract_optimized_insights(access_token: str, max_emails: int = 1000):
    """Optimized AI insights with two-tier processing and batching"""
    try:
        gmail_service.set_credentials(access_token)
        
        # Add reasonable limit for synchronous endpoint to prevent timeouts
        print(f"Fetching emails (max: {max_emails})...")
        emails = gmail_service.fetch_emails_last_6_months()
        
        # Limit emails for synchronous processing to prevent timeout
        if len(emails) > max_emails:
            emails = emails[:max_emails]
            print(f"Limited to first {max_emails} emails for synchronous processing")
        
        print(f"Processing {len(emails)} emails...")
        
        # Step 1: Parse emails
        parsed_emails = [email_parser.parse_email(email) for email in emails]
        
        # Step 2: Two-tier classification
        classified = email_classifier.classify_emails_batch(parsed_emails)
        stats = email_classifier.get_classification_stats(classified)
        
        # Step 3: Process only relevant emails with AI
        relevant_emails = classified["definitely_financial"] + classified["maybe_financial"]
        print(f"Found {len(relevant_emails)} relevant emails to process with AI")
        
        extracted_data = intelligent_extractor.extract_insights_batch(relevant_emails, batch_size=5)
        
        return {
            "insights": extracted_data,
            "optimization_stats": stats,
            "performance_improvement": f"Processed {len(relevant_emails)} emails instead of {len(emails)} (saved {stats['ai_processing_reduction']}%)",
            "note": f"Processed first {len(emails)} emails. Use async endpoint for complete dataset."
        }
    except Exception as e:
        print(f"Error in optimized insights: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/analytics/start-async")
async def start_async_analytics(access_token: str):
    """Start async comprehensive analytics processing - ALL EMAILS"""
    try:
        gmail_service.set_credentials(access_token)
        
        job_id = await async_processor.start_processing_job(
            gmail_service, email_parser, intelligent_extractor, 
            email_classifier, analytics_service, limit=None  # No limit
        )
        
        return {"job_id": job_id, "status": "started", "message": "Processing ALL emails from last 6 months in background"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/analytics/status/{job_id}")
async def get_analytics_status(job_id: str):
    """Get status of async analytics job"""
    job = async_processor.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job

@app.get("/analytics/stream/{job_id}")
async def stream_analytics_progress(job_id: str):
    """Stream real-time progress updates for analytics job"""
    async def generate_updates():
        async for update in async_processor.get_job_stream(job_id):
            yield update
    
    return StreamingResponse(generate_updates(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)