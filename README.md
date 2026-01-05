# Job Hunt Dashboard 🎯

A clean, dark-themed job search dashboard that scrapes jobs from LinkedIn, Indeed, Glassdoor, and ZipRecruiter. Track your applications, filter out senior roles, and keep your job search organized.

## Features

### Job Scraping
- **Multi-site scraping** – Pulls from LinkedIn, Indeed, Glassdoor, ZipRecruiter simultaneously
- **Customizable search queries** – Edit search terms, location, and result limits directly in the UI
- **Auto-filters unwanted roles** – Configurable keyword exclusion (Senior, Lead, Principal, etc.)
- **Fresh data on every scrape** – Old "new" jobs are replaced; your tracked applications are preserved

### Job Tracking
- **Checkbox tracking** – Mark jobs as reviewed (dims the row with strikethrough)
- **Status workflow** – New → Interested → Applied → Interview → Rejected
- **Applied date tracking** – Automatically records when you mark a job as "Applied"
- **Persistent storage** – SQLite database keeps your data safe between sessions

### UI Features
- **Sortable columns** – Click any column header to sort (Position, Company, Location, Salary, Posted, Status)
- **Search & filter** – Find jobs by title, company, or location
- **Status filters** – Quick buttons to show only jobs at a specific status
- **Direct apply links** – One click opens the job posting
- **Settings panel** – Tweak all scraper parameters without touching code
- **Dark brutalist theme** – Easy on the eyes for long job search sessions

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

The API runs at `http://localhost:8000`

### 3. Open the Dashboard

Open `frontend/index.html` in your browser.

Or serve it:
```bash
cd frontend
python -m http.server 3000
```
Then visit `http://localhost:3000`

## Settings Panel

Click **⚙ Settings** to customize your job search:

| Setting | Description | Default |
|---------|-------------|---------|
| **Search Query** | Job titles to search for. Use `OR` for multiple terms, quotes for exact phrases | Software engineer, developer, QA roles |
| **Location** | Geographic filter | USA |
| **Results Wanted** | Max jobs to fetch per scrape (10-500) | 100 |
| **Hours Old** | Only fetch jobs posted within this many hours | 72 |
| **Exclude Keywords** | Comma-separated words to filter OUT of job titles | senior, lead, principal, staff, manager, architect, head, director |

Settings are saved in your browser's localStorage.

## How It Works

### Scraping Behavior
1. Fetches jobs from all 4 sites based on your search query
2. Filters out jobs containing your excluded keywords
3. Sorts by date (newest first) and limits to your requested count
4. **Deletes all existing "new" status jobs** (stale data)
5. **Preserves jobs you've interacted with** (interested, applied, interview, rejected)
6. Inserts fresh jobs into the database

### Status Workflow
- **New** – Fresh from scraper, not yet reviewed
- **Interested** – Worth a closer look
- **Applied** – You've submitted an application (date is recorded)
- **Interview** – You've got an interview scheduled
- **Rejected** – Didn't work out

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/jobs` | List jobs. Query params: `?status=`, `?search=` |
| `PATCH` | `/api/jobs/{id}` | Update job (status, checked, notes) |
| `DELETE` | `/api/jobs/{id}` | Remove a job |
| `POST` | `/api/scrape` | Run the job scraper |
| `GET` | `/api/stats` | Dashboard statistics |

### Example: Custom Scrape

```bash
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "\"frontend developer\" OR \"react engineer\"",
    "location": "Remote",
    "results_wanted": 50,
    "hours_old": 48,
    "exclude_keywords": "senior, lead, manager"
  }'
```

## Tech Stack

- **Backend**: FastAPI + SQLite + python-jobspy
- **Frontend**: React 18 + Vanilla CSS (no build step)
- **Fonts**: JetBrains Mono + Space Grotesk

## File Structure

```
job-dashboard/
├── backend/
│   ├── main.py           # FastAPI server
│   ├── requirements.txt  # Python dependencies
│   └── jobs.db           # SQLite database (auto-created)
├── frontend/
│   └── index.html        # React dashboard (single file)
└── README.md
```

## Tips

1. **Scrape daily** – Jobs get filled fast, keep your list fresh
2. **Use the checkbox** – Helps track what you've already reviewed
3. **Set status immediately** – Mark as "Applied" right after submitting to track the date
4. **Adjust excluded keywords** – Add "intern" or "contract" if those aren't relevant to you
5. **Sort by salary** – Quick way to find the highest-paying opportunities
6. **Delete aggressively** – Remove jobs you're not interested in to keep focus

## Troubleshooting

**"Scraping failed - is the server running?"**
- Make sure the backend is running: `cd backend && python main.py`

**Jobs not showing up after scrape?**
- Check the terminal for errors from python-jobspy
- Some sites may rate-limit; try reducing `results_wanted`

**Applied date not showing?**
- The column is auto-added to existing databases on startup
- If issues persist, delete `jobs.db` and restart (you'll lose existing data)

---

Built for the grind. Good luck out there! 🚀
