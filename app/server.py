"""Zero-third-party-dependency StudyFlow web server."""
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
import json
import os
import sqlite3

from .planner import build_plan

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'static'
DATA_DIR = Path(os.environ.get('STUDYFLOW_DATA_DIR', str(ROOT / 'data')))
DB_PATH = DATA_DIR / 'studyflow.db'
COLORS = {'#8b5cf6', '#06b6d4', '#f59e0b', '#ec4899', '#10b981', '#3b82f6'}


def connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA busy_timeout=10000')
    return db


def init_db():
    with connection() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS subjects (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL, difficulty INTEGER NOT NULL,
          hours INTEGER NOT NULL, deadline TEXT NOT NULL, color TEXT NOT NULL)''')
        db.execute('''CREATE TABLE IF NOT EXISTS completed (
          subject_id INTEGER NOT NULL, date TEXT NOT NULL,
          hours INTEGER NOT NULL, PRIMARY KEY(subject_id, date),
          FOREIGN KEY(subject_id) REFERENCES subjects(id))''')


def subjects(db):
    return [dict(r) for r in db.execute('SELECT * FROM subjects ORDER BY deadline, id')]


def completions(db):
    return [dict(r) for r in db.execute('SELECT * FROM completed ORDER BY date, subject_id')]


class Handler(BaseHTTPRequestHandler):
    def send_data(self, code, payload):
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def read_json(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length > 32768 or length < 1:
            raise ValueError('Invalid request size.')
        data = json.loads(self.rfile.read(length))
        if not isinstance(data, dict):
            raise ValueError('Expected JSON object.')
        return data

    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith('/api/'):
            try:
                with connection() as db:
                    if path == '/api/state':
                        return self.send_data(200, {'subjects': subjects(db), 'completed': completions(db)})
                    if path == '/api/plan':
                        return self.send_data(200, build_plan(subjects(db), self.daily_hours(), date.today()))
                return self.send_data(404, {'error': 'Endpoint not found.'})
            except (ValueError, sqlite3.Error) as e:
                return self.send_data(400, {'error': str(e)})
        path = '/index.html' if path == '/' else path
        files = {'/index.html': ('index.html', 'text/html'), '/style.css': ('style.css', 'text/css'), '/app.js': ('app.js', 'text/javascript')}
        if path not in files:
            return self.send_error(404)
        name, mime = files[path]
        raw = (STATIC / name).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime + '; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def daily_hours(self):
        from urllib.parse import parse_qs
        q = parse_qs(urlparse(self.path).query)
        try:
            h = int(q.get('hours', ['5'])[0])
        except (ValueError, TypeError):
            raise ValueError('Daily hours must be an integer.')
        if not 1 <= h <= 24:
            raise ValueError('Daily hours must be between 1 and 24.')
        return h

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            body = self.read_json()
            with connection() as db:
                if path == '/api/subjects':
                    name = str(body.get('name', '')).strip()
                    if not 1 <= len(name) <= 80:
                        raise ValueError('Subject name must have 1–80 characters.')
                    difficulty, hours = int(body.get('difficulty', 0)), int(body.get('hours', 0))
                    if difficulty not in range(1, 6) or hours not in range(1, 1001):
                        raise ValueError('Difficulty: 1–5; hours: 1–1000.')
                    deadline = date.fromisoformat(str(body.get('deadline', '')))
                    if deadline < date.today():
                        raise ValueError('Deadline cannot be in the past.')
                    color = body.get('color', '#8b5cf6')
                    if color not in COLORS:
                        raise ValueError('Invalid color.')
                    db.execute('INSERT INTO subjects(name,difficulty,hours,deadline,color) VALUES (?,?,?,?,?)',
                               (name, difficulty, hours, deadline.isoformat(), color))
                    return self.send_data(201, {'subjects': subjects(db)})
                if path == '/api/complete':
                    sid, day, hours = int(body['subject_id']), date.fromisoformat(body['date']), int(body['hours'])
                    if not 0 <= hours <= 24 or day > date.today():
                        raise ValueError('Invalid completion hours or future date.')
                    subject = db.execute('SELECT id FROM subjects WHERE id=?', (sid,)).fetchone()
                    if not subject:
                        return self.send_data(404, {'error': 'Subject not found.'})
                    if hours == 0:
                        db.execute('DELETE FROM completed WHERE subject_id=? AND date=?', (sid, day.isoformat()))
                    else:
                        db.execute('INSERT INTO completed(subject_id,date,hours) VALUES(?,?,?) ON CONFLICT(subject_id,date) DO UPDATE SET hours=excluded.hours', (sid, day.isoformat(), hours))
                    return self.send_data(200, {'completed': completions(db)})
                if path.startswith('/api/subjects/') and path.endswith('/delete'):
                    sid = int(path.split('/')[3])
                    db.execute('DELETE FROM completed WHERE subject_id=?', (sid,))
                    cursor = db.execute('DELETE FROM subjects WHERE id=?', (sid,))
                    if cursor.rowcount == 0:
                        return self.send_data(404, {'error': 'Subject not found.'})
                    return self.send_data(200, {'subjects': subjects(db), 'completed': completions(db)})
            return self.send_data(404, {'error': 'Endpoint not found.'})
        except (ValueError, KeyError, TypeError, json.JSONDecodeError, sqlite3.Error) as e:
            return self.send_data(400, {'error': str(e)})


def main():
    init_db()
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '8000'))
    print(f'\nStudyFlow AI running at http://{host}:{port}\nPress Ctrl+C to stop.\n', flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == '__main__':
    main()
