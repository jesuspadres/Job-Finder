# Job Hunt Dashboard 🎯

A clean, minimal job search dashboard that scrapes jobs from LinkedIn, Indeed, Glassdoor, and ZipRecruiter. Track your applications with checkboxes and status updates.

![Dashboard Preview](preview.png)

## Features

- **Multi-site scraping**: Pulls from LinkedIn, Indeed, Glassdoor, ZipRecruiter
- **Auto-filters seniors roles**: Removes Senior, Lead, Principal, Staff, etc.
- **Checkbox tracking**: Mark jobs as reviewed
- **Status tracking**: New → Interested → Applied → Interview → Rejected
- **Search & filter**: Find jobs by title, company, or location
- **Salary display**: Shows salary ranges when available
- **Direct apply links**: One click to job posting
- **Persistent storage**: SQLite database keeps your data safe

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
cd backend
python main.py
```

The API will run at `http://localhost:8000`

### 3. Open the Dashboard

Simply open `frontend/index.html` in your browser.

Or serve it with Python:
```bash
cd frontend
python -m http.server 3000
```
Then visit `http://localhost:3000`

## Usage

### Scraping New Jobs
Click the **"Scrape New Jobs"** button to fetch the latest postings. By default, it searches for:
- Software Engineer
- Software Developer
- QA Engineer
- Test Engineer
- Software Development Engineer

And filters OUT:
- Senior, Sr., Lead, Principal, Staff, Manager, Architect, Head, Director roles

### Tracking Jobs
- **Checkbox**: Click to mark as reviewed (dims the row)
- **Status dropdown**: Track where you are in the process
- **Apply button**: Opens the job posting in a new tab
- **Delete (✕)**: Remove jobs you're not interested in

### Filtering
- Use the search box to find specific jobs
- Click status buttons to filter by application status

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jobs` | List all jobs (supports `?status=`, `?search=`) |
| PATCH | `/api/jobs/{id}` | Update job status/checked state |
| DELETE | `/api/jobs/{id}` | Remove a job |
| POST | `/api/scrape` | Run the job scraper |
| GET | `/api/stats` | Get dashboard statistics |

## Customizing the Search

Edit the `ScrapeRequest` in `backend/main.py` or send custom parameters:

```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "\"frontend developer\" OR \"react developer\"",
    "location": "Remote",
    "results_wanted": 50,
    "hours_old": 48
  }'
```

## Tech Stack

- **Backend**: FastAPI + SQLite + python-jobspy
- **Frontend**: React 18 + Vanilla CSS (no build step needed)
- **Fonts**: JetBrains Mono + Space Grotesk

## File Structure

```
job-dashboard/
├── backend/
│   ├── main.py           # FastAPI server
│   ├── requirements.txt  # Python dependencies
│   └── jobs.db          # SQLite database (auto-created)
└── frontend/
    └── index.html        # React dashboard (single file)
```

## Tips

1. **Run scraper daily**: Jobs get stale quickly
2. **Use the checkbox**: Helps you remember what you've reviewed
3. **Set status to "Applied"**: Track your applications
4. **Delete rejected/uninterested**: Keep your list clean

---

Built for the job hunt. Good luck! 🚀
