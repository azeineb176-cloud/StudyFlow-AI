"""Deterministic, deadline-aware daily study scheduling.

Tasks are divisible into whole hours. Each day has a fixed capacity. EDF is
feasibility-optimal for jobs available now with deadlines and preemption.
"""
from datetime import date, timedelta


def build_plan(subjects, hours_per_day, start=None):
    start = start or date.today()
    if not isinstance(hours_per_day, int) or not 1 <= hours_per_day <= 24:
        raise ValueError('Daily study hours must be between 1 and 24.')
    if not subjects:
        return {'feasible': True, 'days': [], 'total_hours': 0, 'message': 'Add a subject to get started.'}
    remaining = {}
    for s in subjects:
        sid = s['id']
        if not isinstance(s['hours'], int) or s['hours'] <= 0:
            raise ValueError('Each subject needs a positive number of hours.')
        if not 1 <= s['difficulty'] <= 5:
            raise ValueError('Difficulty must be between 1 and 5.')
        deadline = date.fromisoformat(s['deadline'])
        if deadline < start:
            raise ValueError(f"Deadline has passed for {s['name']}.")
        remaining[sid] = s['hours']
    last = max(date.fromisoformat(s['deadline']) for s in subjects)
    days = []
    current = start
    while current <= last and any(remaining.values()):
        capacity = hours_per_day
        sessions = []
        eligible = sorted(
            (s for s in subjects if remaining[s['id']] > 0 and date.fromisoformat(s['deadline']) >= current),
            key=lambda s: (s['deadline'], -s['difficulty'], -remaining[s['id']], s['id']),
        )
        for s in eligible:
            if capacity == 0:
                break
            allocated = min(capacity, remaining[s['id']])
            remaining[s['id']] -= allocated
            capacity -= allocated
            sessions.append({'subject_id': s['id'], 'name': s['name'], 'hours': allocated, 'color': s['color']})
        if sessions:
            days.append({'date': current.isoformat(), 'sessions': sessions, 'hours': hours_per_day - capacity})
        current += timedelta(days=1)
    unfinished = [{'name': s['name'], 'hours': remaining[s['id']], 'deadline': s['deadline']}
                  for s in subjects if remaining[s['id']] > 0]
    return {
        'feasible': not unfinished,
        'days': days,
        'total_hours': sum(s['hours'] for s in subjects),
        'scheduled_hours': sum(d['hours'] for d in days),
        'unfinished': unfinished,
        'message': 'All subjects fit before their deadlines.' if not unfinished else 'Not enough time before some deadlines. Increase daily hours or move deadlines.',
    }
