import asyncio
import json
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime
import uuid

class AsyncEmailProcessor:
    def __init__(self):
        self.jobs = {}  # Simple in-memory job storage
    
    async def start_processing_job(
        self, 
        gmail_service, 
        email_parser, 
        intelligent_extractor, 
        email_classifier,
        analytics_service,
        limit: int = None
    ) -> str:
        """Start an async processing job and return job ID"""
        
        job_id = str(uuid.uuid4())
        
        self.jobs[job_id] = {
            "status": "starting",
            "progress": 0,
            "total": 0,
            "current_step": "Initializing...",
            "start_time": datetime.now().isoformat(),
            "results": None,
            "error": None
        }
        
        # Start background task
        asyncio.create_task(
            self._process_emails_async(
                job_id, gmail_service, email_parser, intelligent_extractor, 
                email_classifier, analytics_service, limit
            )
        )
        
        return job_id
    
    async def _process_emails_async(
        self, 
        job_id: str, 
        gmail_service, 
        email_parser, 
        intelligent_extractor,
        email_classifier,
        analytics_service,
        limit: int = None
    ):
        """Background async processing of emails"""
        
        try:
            # Step 1: Fetch emails
            self._update_job(job_id, "running", 10, "Fetching ALL emails from Gmail (last 6 months)...")
            emails = gmail_service.fetch_emails_last_6_months()  # No limit
            
            self._update_job(job_id, "running", 20, f"Fetched {len(emails)} emails. Parsing content...")
            
            # Step 2: Parse emails
            parsed_emails = []
            for i, email in enumerate(emails):
                parsed_email = email_parser.parse_email(email)
                parsed_emails.append(parsed_email)
                
                # Update progress every 10 emails
                if i % 10 == 0:
                    progress = 20 + (i / len(emails)) * 30  # 20-50% for parsing
                    self._update_job(job_id, "running", progress, f"Parsing emails... {i+1}/{len(emails)}")
            
            # Step 3: Classify emails (fast rule-based)
            self._update_job(job_id, "running", 50, "Classifying emails by relevance...")
            classified = email_classifier.classify_emails_batch(parsed_emails)
            
            # Get statistics
            stats = email_classifier.get_classification_stats(classified)
            
            # Step 4: AI Processing (only on relevant emails)
            relevant_emails = classified["definitely_financial"] + classified["maybe_financial"]
            self._update_job(
                job_id, "running", 60, 
                f"Processing {len(relevant_emails)} financial emails with AI... (Skipped {stats['probably_not']} irrelevant emails)"
            )
            
            # Process in batches - PARALLELIZED
            extracted_data = []
            batch_size = 5
            max_concurrent_batches = 3  # Limit concurrent batches to avoid overwhelming the AI service
            
            # Create all batches
            batches = []
            for i in range(0, len(relevant_emails), batch_size):
                batch = relevant_emails[i:i+batch_size]
                batches.append((i, batch))
            
            # Process batches in parallel chunks
            for chunk_start in range(0, len(batches), max_concurrent_batches):
                chunk_batches = batches[chunk_start:chunk_start + max_concurrent_batches]
                
                # Create async tasks for concurrent processing
                tasks = []
                for batch_idx, batch in chunk_batches:
                    task = self._process_batch_async(intelligent_extractor, batch, batch_idx)
                    tasks.append(task)
                
                # Execute batches concurrently
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results and update extracted_data
                for result in batch_results:
                    if isinstance(result, Exception):
                        # Log error but continue processing other batches
                        self._update_job(job_id, "running", None, f"Warning: Batch processing error - {str(result)}")
                    else:
                        extracted_data.extend(result)
                
                # Update overall progress after each chunk
                processed_emails = min(chunk_start + max_concurrent_batches, len(batches)) * batch_size
                processed_emails = min(processed_emails, len(relevant_emails))
                progress = 60 + (processed_emails / len(relevant_emails)) * 30  # 60-90% for AI processing
                self._update_job(
                    job_id, "running", progress, 
                    f"AI processing... {processed_emails}/{len(relevant_emails)} emails (parallel processing)"
                )
            
            # Step 5: Generate analytics
            self._update_job(job_id, "running", 90, "Generating comprehensive analytics...")
            analytics = analytics_service.generate_comprehensive_insights(extracted_data)
            
            # Step 6: Complete
            final_results = {
                "analytics": analytics,
                "classification_stats": stats,
                "extracted_insights": extracted_data,
                "metadata": {
                    "total_emails_fetched": len(emails),
                    "financial_emails_processed": len(relevant_emails),
                    "ai_processing_reduction": stats.get("ai_processing_reduction", 0),
                    "processing_completed_at": datetime.now().isoformat()
                }
            }
            
            self._update_job(job_id, "completed", 100, "Processing completed successfully!", final_results)
            
        except Exception as e:
            self._update_job(job_id, "failed", 0, f"Error: {str(e)}", None, str(e))
    
    async def _process_batch_async(
        self, 
        intelligent_extractor, 
        batch: List, 
        batch_idx: int
    ) -> List:
        """Process a single batch asynchronously"""
        try:
            # Add small delay to avoid overwhelming the AI service
            if batch_idx > 0:
                await asyncio.sleep(0.1)
            
            # Process the batch (this calls the synchronous method but wraps it in async)
            batch_results = await asyncio.to_thread(
                intelligent_extractor.extract_insights_batch, 
                batch, 
                batch_size=len(batch)
            )
            return batch_results
        except Exception as e:
            # Return empty list on error - error will be caught by gather()
            raise Exception(f"Batch {batch_idx} processing failed: {str(e)}")
    
    def _update_job(
        self, 
        job_id: str, 
        status: str, 
        progress: float, 
        current_step: str, 
        results: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """Update job status"""
        if job_id in self.jobs:
            self.jobs[job_id].update({
                "status": status,
                "progress": round(progress, 1),
                "current_step": current_step,
                "updated_at": datetime.now().isoformat()
            })
            
            if results:
                self.jobs[job_id]["results"] = results
            
            if error:
                self.jobs[job_id]["error"] = error
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get current job status"""
        return self.jobs.get(job_id)
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old completed jobs"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        jobs_to_remove = []
        for job_id, job_data in self.jobs.items():
            job_time = datetime.fromisoformat(job_data["start_time"]).timestamp()
            if job_time < cutoff_time and job_data["status"] in ["completed", "failed"]:
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
    
    async def get_job_stream(self, job_id: str) -> AsyncGenerator[str, None]:
        """Stream job progress updates"""
        last_progress = -1
        
        while True:
            job = self.get_job_status(job_id)
            
            if not job:
                yield json.dumps({"error": "Job not found"}) + "\n"
                break
            
            # Send update if progress changed
            if job["progress"] != last_progress:
                yield json.dumps({
                    "status": job["status"],
                    "progress": job["progress"],
                    "current_step": job["current_step"],
                    "updated_at": job.get("updated_at")
                }) + "\n"
                
                last_progress = job["progress"]
            
            # Break if job is done
            if job["status"] in ["completed", "failed"]:
                if job["status"] == "completed" and job.get("results"):
                    yield json.dumps({"results": job["results"]}) + "\n"
                elif job["status"] == "failed":
                    yield json.dumps({"error": job.get("error", "Unknown error")}) + "\n"
                break
            
            # Wait before next check
            await asyncio.sleep(1)