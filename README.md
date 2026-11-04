# ✦ StudyFlow AI

A responsive, local-first **smart study planner** with a Python backend, modern web interface, SQLite storage, deadline-aware scheduling, progress tracking and CSV export.

## Features

- Add and delete subjects with difficulty, estimated hours, deadline and color
- Generate a schedule that can split one day across several subjects
- See workload insights and study progress
- Log completed hours for today or earlier planned dates
- Export a generated schedule as CSV
- Store subjects and progress in local SQLite (`data/studyflow.db`)
- Works without external Python packages, API keys or internet access
- Responsive dark-mode interface

## Requirements

**Python 3.10+** and a modern web browser.

## Run locally

1. Download or clone the repository.
2. Open a terminal **inside the project folder**.
3. Start the server:

   ```bash
   python main.py
   ```

   On some Windows machines, use `py main.py` instead.

4. Open **http://127.0.0.1:8000** in Chrome, Edge or Firefox.
5. Add subjects, set daily hours and click **Generate smart schedule**.
6. Press `Ctrl+C` in the terminal to stop the server.

No `pip install` is needed. `requirements.txt` is intentionally empty of dependencies.

### If port 8000 is already in use

- macOS/Linux: `PORT=8080 python main.py`
- Windows PowerShell: `$env:PORT=8080; python main.py`

Then open `http://127.0.0.1:8080`.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Project structure

```text
studyflow-web/
├── app/
│   ├── __init__.py
│   ├── planner.py       # Scheduling logic
│   └── server.py        # HTTP API + SQLite
├── static/
│   ├── index.html       # Dashboard UI
│   ├── style.css        # Responsive design
│   └── app.js           # Interactions + API client
├── tests/
│   └── test_planner.py
├── main.py              # Launch entry point
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Scheduling algorithm

Uses **Earliest Deadline First (EDF)**, breaking ties by difficulty, then remaining workload. A subject's work can be split into whole hours and multiple subjects can share a day. Days have fixed study capacity. For this model (all subjects available at the start, divisible tasks, no per-subject daily limits), EDF is feasibility-optimal. If a feasible schedule exists, EDF finds one. If not, it reports unfinished workload. The deadline date itself is included as a study day.

This is an **optimization/scheduling project**, not machine learning. The original prototype explored A*, but the chosen implementation is better suited to these specific constraints.

## Important limitations

- The generated schedule is computed from the full estimated workload. Logged completed hours are tracked separately; **they do not yet reduce the remaining hours used in planning**.
- Only whole-hour blocks are supported; there is no class timetable, weekend filter or calendar synchronization.
- The app is intended for **local, single-user use**. It has no login, authentication, CSRF protection, or rate limiting. **Do not expose the server to the public internet without adding these protections.**
- This repository is ready for GitHub source hosting. **GitHub Pages cannot host the Python/SQLite backend**; to deploy it online you would need a suitable Python hosting service and additional production security work.

## Publish to GitHub

Create a new **empty** repository on GitHub, then run from this folder:

```bash
git init
git add .
git commit -m "Initial commit: StudyFlow AI web app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/studyflow-ai.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. Your `data/` folder and local database are excluded by `.gitignore`.

## Tech stack

Python · HTTP server (standard library) · SQLite · HTML · CSS · JavaScript

## License

MIT
