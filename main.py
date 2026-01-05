"""
Job Search Dashboard - Backend API
FastAPI server for scraping jobs and managing application status
"""

import sqlite3
import csv
from datetime import datetime
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

# Try to import jobspy - will fail gracefully if not installed
try:
    from jobspy import scrape_jobs
    JOBSPY_AVAILABLE = True
except ImportError:
    JOBSPY_AVAILABLE = False
    print("⚠️  jobspy not installed. Run: pip install python-jobspy")

app = FastAPI(title="Job Search Dashboard API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DB_PATH = Path(__file__).parent / "jobs.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site TEXT,
                title TEXT,
                company TEXT,
                location TEXT,
                job_type TEXT,
                date_posted TEXT,
                job_url TEXT UNIQUE,
                salary_min REAL,
                salary_max REAL,
                salary_source TEXT,
                is_remote INTEGER DEFAULT 0,
                checked INTEGER DEFAULT 0,
                status TEXT DEFAULT 'new',
                notes TEXT DEFAULT '',
                applied_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Add applied_at column if it doesn't exist (for existing databases)
        try:
            conn.execute("ALTER TABLE jobs ADD COLUMN applied_at TEXT")
        except:
            pass  # Column already exists
        conn.commit()

init_db()

# Pydantic models
class JobUpdate(BaseModel):
    checked: Optional[bool] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class ScrapeRequest(BaseModel):
    search_query: Optional[str] = None
    location: Optional[str] = "USA"
    results_wanted: Optional[int] = 100
    hours_old: Optional[int] = 72
    exclude_keywords: Optional[str] = None

# API Routes
@app.get("/api/jobs")
def get_jobs(
    status: Optional[str] = None,
    checked: Optional[bool] = None,
    search: Optional[str] = None
):
    """Get all jobs with optional filters"""
    with get_db() as conn:
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        
        if status and status != "all":
            query += " AND status = ?"
            params.append(status)
        
        if checked is not None:
            query += " AND checked = ?"
            params.append(1 if checked else 0)
        
        if search:
            query += " AND (title LIKE ? OR company LIKE ? OR location LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        
        query += " ORDER BY date_posted DESC, created_at DESC"
        
        cursor = conn.execute(query, params)
        jobs = [dict(row) for row in cursor.fetchall()]
        
        # Convert checked to boolean for frontend
        for job in jobs:
            job['checked'] = bool(job['checked'])
            job['is_remote'] = bool(job['is_remote'])
        
        return {"jobs": jobs, "total": len(jobs)}

@app.patch("/api/jobs/{job_id}")
def update_job(job_id: int, update: JobUpdate):
    """Update job status, checked state, or notes"""
    with get_db() as conn:
        updates = []
        params = []
        
        if update.checked is not None:
            updates.append("checked = ?")
            params.append(1 if update.checked else 0)
        
        if update.status is not None:
            updates.append("status = ?")
            params.append(update.status)
            # Set applied_at timestamp when status changes to 'applied'
            if update.status == 'applied':
                updates.append("applied_at = ?")
                params.append(datetime.now().strftime('%Y-%m-%d'))
            # Clear applied_at if status changes away from 'applied'
            elif update.status != 'applied':
                updates.append("applied_at = NULL")
        
        if update.notes is not None:
            updates.append("notes = ?")
            params.append(update.notes)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        params.append(job_id)
        query = f"UPDATE jobs SET {', '.join(updates)} WHERE id = ?"
        
        cursor = conn.execute(query, params)
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"success": True}

@app.post("/api/scrape")
def scrape_new_jobs(request: ScrapeRequest):
    """Run the job scraper and add new jobs to database"""
    if not JOBSPY_AVAILABLE:
        raise HTTPException(
            status_code=500, 
            detail="jobspy not installed. Run: pip install python-jobspy"
        )
    
    # Default search query
    search_query = request.search_query or (
        '"software engineer" OR "software developer" OR "qa engineer" OR '
        '"quality assurance engineer" OR "test engineer" OR "software test engineer" OR '
        '"Software Development Engineer"'
    )
    
    target_sites = ["indeed", "linkedin", "zip_recruiter", "glassdoor"]
    
    try:
        jobs_df = scrape_jobs(
            site_name=target_sites,
            search_term=search_query,
            location=request.location,
            results_wanted=request.results_wanted,
            hours_old=request.hours_old,
            country_indeed='USA',
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")
    
    if jobs_df.empty:
        return {"message": "No jobs found", "added": 0, "skipped": 0}
    
    # Filter out senior roles using provided keywords or defaults
    if request.exclude_keywords:
        senior_keywords = [k.strip().lower() for k in request.exclude_keywords.split(',')]
    else:
        senior_keywords = ['senior', 'sr.', 'sr', 'lead', 'principal', 'staff', 'manager', 'architect', 'head', 'director']
    
    pattern = '|'.join(senior_keywords)
    filtered_df = jobs_df[~jobs_df['title'].str.contains(pattern, case=False, na=False)].copy()
    
    # Sort by date (newest first) and limit to requested amount
    if 'date_posted' in filtered_df.columns:
        filtered_df['date_posted'] = pd.to_datetime(filtered_df['date_posted'], errors='coerce')
        filtered_df = filtered_df.sort_values(by='date_posted', ascending=False)
    
    # Limit to requested number of results
    filtered_df = filtered_df.head(request.results_wanted)
    
    # Get URLs of jobs user has interacted with (not 'new' status)
    with get_db() as conn:
        cursor = conn.execute("SELECT job_url FROM jobs WHERE status != 'new'")
        preserved_urls = set(row[0] for row in cursor.fetchall())
    
    # Delete ALL jobs with status 'new' 
    with get_db() as conn:
        deleted = conn.execute("DELETE FROM jobs WHERE status = 'new'").rowcount
        conn.commit()
    
    # Filter out jobs that user already has with non-new status (already applied, etc.)
    filtered_df = filtered_df[~filtered_df['job_url'].isin(preserved_urls)]
    
    # Insert into database
    added = 0
    skipped = 0
    
    with get_db() as conn:
        for _, row in filtered_df.iterrows():
            try:
                # Parse date
                date_posted = None
                if pd.notna(row.get('date_posted')):
                    try:
                        date_posted = pd.to_datetime(row['date_posted']).strftime('%Y-%m-%d')
                    except:
                        date_posted = str(row['date_posted'])
                
                conn.execute("""
                    INSERT OR IGNORE INTO jobs 
                    (site, title, company, location, job_type, date_posted, job_url, 
                     salary_min, salary_max, salary_source, is_remote)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('site', ''),
                    row.get('title', ''),
                    row.get('company', ''),
                    row.get('location', ''),
                    row.get('job_type', ''),
                    date_posted,
                    row.get('job_url', ''),
                    row.get('min_amount') if pd.notna(row.get('min_amount')) else None,
                    row.get('max_amount') if pd.notna(row.get('max_amount')) else None,
                    row.get('salary_source', ''),
                    1 if row.get('is_remote') else 0
                ))
                added += 1
                    
            except sqlite3.IntegrityError:
                skipped += 1
        
        conn.commit()
    
    return {
        "message": f"Scraping complete",
        "added": added,
        "skipped": skipped,
        "deleted": deleted,
        "total_found": len(filtered_df)
    }

@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int):
    """Delete a job from the database"""
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {"success": True}

@app.get("/api/stats")
def get_stats():
    """Get job statistics"""
    with get_db() as conn:
        stats = {}
        
        # Total jobs
        stats['total'] = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        
        # By status
        cursor = conn.execute("SELECT status, COUNT(*) as count FROM jobs GROUP BY status")
        stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Checked count
        stats['checked'] = conn.execute("SELECT COUNT(*) FROM jobs WHERE checked = 1").fetchone()[0]
        stats['unchecked'] = stats['total'] - stats['checked']
        
        # By site
        cursor = conn.execute("SELECT site, COUNT(*) as count FROM jobs GROUP BY site")
        stats['by_site'] = {row['site']: row['count'] for row in cursor.fetchall()}
        
        return stats

@app.post("/api/import-csv")
def import_csv():
    """Import jobs from existing CSV file"""
    csv_path = Path(__file__).parent / "recent_non_senior_jobs.csv"
    
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="CSV file not found")
    
    df = pd.read_csv(csv_path)
    added = 0
    
    with get_db() as conn:
        for _, row in df.iterrows():
            try:
                date_posted = None
                if pd.notna(row.get('date_posted')):
                    try:
                        date_posted = pd.to_datetime(row['date_posted']).strftime('%Y-%m-%d')
                    except:
                        date_posted = str(row['date_posted'])
                
                conn.execute("""
                    INSERT OR IGNORE INTO jobs 
                    (site, title, company, location, job_type, date_posted, job_url, 
                     salary_min, salary_max, is_remote)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('site', ''),
                    row.get('title', ''),
                    row.get('company', ''),
                    row.get('location', ''),
                    row.get('job_type', ''),
                    date_posted,
                    row.get('job_url', ''),
                    row.get('min_amount') if pd.notna(row.get('min_amount')) else None,
                    row.get('max_amount') if pd.notna(row.get('max_amount')) else None,
                    1 if row.get('is_remote') else 0
                ))
                added += 1
            except:
                pass
        
        conn.commit()
    
    return {"message": f"Imported {added} jobs from CSV"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)