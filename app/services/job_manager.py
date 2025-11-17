import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class JobManager:
    def __init__(self, jobs_dir: str = "jobs"):
        self.jobs_dir = jobs_dir
        os.makedirs(jobs_dir, exist_ok=True)
    
    def _get_job_file_path(self, job_id: str) -> str:
        return os.path.join(self.jobs_dir, f"{job_id}.json")
    
    def create_job(self, job_id: str, job_type: str, status: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job with the given parameters."""
        job = {
            "job_id": job_id,
            "job_type": job_type,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "data": data,
            "progress": 0,
            "status_message": "Job created",
            "error": None,
            "output_path": None,
            "subtitle_path": None
        }
        
        self._save_job(job)
        return job
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve job information by job ID."""
        job_file_path = self._get_job_file_path(job_id)
        
        if not os.path.exists(job_file_path):
            return None
        
        try:
            with open(job_file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading job file: {e}")
            return None
    
    def update_job_status(self, job_id: str, status: str, progress: int = None, status_message: str = None) -> bool:
        """Update job status, progress, and detailed status message."""
        job = self.get_job(job_id)
        if not job:
            return False
        
        job["status"] = status
        job["updated_at"] = datetime.now().isoformat()
        
        if progress is not None:
            job["progress"] = progress
            
        if status_message is not None:
            job["status_message"] = status_message
        
        self._save_job(job)
        return True
    
    def complete_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Mark job as completed with result data."""
        job = self.get_job(job_id)
        if not job:
            return False
        
        # Verify that required output files actually exist before marking as completed
        if "output_path" in result:
            if not os.path.exists(result["output_path"]):
                error_msg = f"Output file not found: {result['output_path']}"
                print(f"Job {job_id} completion failed: {error_msg}")
                return self.fail_job(job_id, error_msg)
            job["output_path"] = result["output_path"]
        
        if "subtitle_path" in result:
            if not os.path.exists(result["subtitle_path"]):
                error_msg = f"Subtitle file not found: {result['subtitle_path']}"
                print(f"Job {job_id} completion failed: {error_msg}")
                return self.fail_job(job_id, error_msg)
            job["subtitle_path"] = result["subtitle_path"]
        
        # Only mark as completed if all files exist
        job["status"] = "completed"
        job["progress"] = 100
        job["updated_at"] = datetime.now().isoformat()
        
        self._save_job(job)
        return True
    
    def fail_job(self, job_id: str, error_message: str) -> bool:
        """Mark job as failed with error message."""
        job = self.get_job(job_id)
        if not job:
            return False
        
        job["status"] = "failed"
        job["error"] = error_message
        job["updated_at"] = datetime.now().isoformat()
        
        self._save_job(job)
        return True
    
    def _save_job(self, job: Dict[str, Any]) -> None:
        """Save job data to file."""
        job_file_path = self._get_job_file_path(job["job_id"])
        
        try:
            with open(job_file_path, 'w') as f:
                json.dump(job, f, indent=2)
        except Exception as e:
            print(f"Error saving job file: {e}")
    
    def list_jobs(self, limit: int = 100) -> list:
        """List all jobs, most recent first."""
        jobs = []
        
        try:
            job_files = [f for f in os.listdir(self.jobs_dir) if f.endswith('.json')]
            job_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.jobs_dir, x)), reverse=True)
            
            for job_file in job_files[:limit]:
                job_path = os.path.join(self.jobs_dir, job_file)
                with open(job_path, 'r') as f:
                    job = json.load(f)
                    jobs.append(job)
        
        except Exception as e:
            print(f"Error listing jobs: {e}")
        
        return jobs
    
    def cleanup_old_jobs(self, max_age_days: int = 7) -> int:
        """Remove job files older than specified days."""
        import time
        from datetime import timedelta
        
        cleanup_count = 0
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
        try:
            for job_file in os.listdir(self.jobs_dir):
                if job_file.endswith('.json'):
                    job_path = os.path.join(self.jobs_dir, job_file)
                    if os.path.getmtime(job_path) < cutoff_time:
                        os.remove(job_path)
                        cleanup_count += 1
        
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        return cleanup_count