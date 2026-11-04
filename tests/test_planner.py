import unittest
from datetime import date, timedelta
from app.planner import build_plan

TODAY = date(2026, 11, 4)

def subject(id, hours, days, difficulty=3):
    return {'id': id, 'name': f'Subject {id}', 'hours': hours,
            'deadline': (TODAY + timedelta(days=days)).isoformat(),
            'difficulty': difficulty, 'color': '#8b5cf6'}

class PlannerTests(unittest.TestCase):
    def test_multiple_subjects_same_day(self):
        p = build_plan([subject(1, 2, 0), subject(2, 3, 0)], 5, TODAY)
        self.assertTrue(p['feasible'])
        self.assertEqual(len(p['days'][0]['sessions']), 2)
    def test_infeasible_deadline(self):
        p = build_plan([subject(1, 6, 0)], 5, TODAY)
        self.assertFalse(p['feasible'])
        self.assertEqual(p['unfinished'][0]['hours'], 1)
    def test_earliest_deadline_first(self):
        p = build_plan([subject(1, 5, 2), subject(2, 2, 0)], 5, TODAY)
        self.assertEqual(p['days'][0]['sessions'][0]['subject_id'], 2)
    def test_no_subjects(self):
        self.assertTrue(build_plan([], 5, TODAY)['feasible'])
    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):build_plan([subject(1, 2, 1)], 0, TODAY)
    def test_deadline_is_inclusive(self):
        self.assertTrue(build_plan([subject(1, 5, 0)], 5, TODAY)['feasible'])

if __name__ == '__main__':unittest.main()
