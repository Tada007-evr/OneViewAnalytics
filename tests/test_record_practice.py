import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from oneview_db import calculate_practice_result, validate_grid


class RecordPracticePaperTests(unittest.TestCase):
    def row(self, question, max_marks, marks_lost, error_type, mapping_valid=True):
        return {
            "Question": question,
            "Topic": "Algebra",
            "Sub-topic": "Quadratics",
            "Max Marks": max_marks,
            "Marks Lost": marks_lost,
            "Error Type": error_type,
            "mapping_valid": mapping_valid,
        }

    def test_results_summary_sample(self):
        grid = pd.DataFrame([
            self.row("1", 20, 2, "Conceptual Error"),
            self.row("2(a)", 15, 0, "No Error"),
            self.row("2(b)", 15, 1, "Careless Error"),
            self.row("3", 25, 4, "Application Error"),
        ])
        lost, score, pct = calculate_practice_result(grid, 75)
        self.assertEqual(lost, 7)
        self.assertEqual(score, 68)
        self.assertAlmostEqual(pct, 90.6666666667)

    def test_zero_lost_requires_no_error(self):
        grid = pd.DataFrame([self.row("1", 5, 0, "Calculation Error")])
        errors = validate_grid(grid, 75)
        self.assertTrue(any("must be No Error" in e for e in errors))

    def test_positive_lost_requires_error_category(self):
        grid = pd.DataFrame([self.row("1", 5, 2, "No Error")])
        errors = validate_grid(grid, 75)
        self.assertTrue(any("select an Error Type" in e for e in errors))

    def test_marks_lost_cannot_exceed_max(self):
        grid = pd.DataFrame([self.row("1", 5, 6, "Careless Error")])
        errors = validate_grid(grid, 75)
        self.assertTrue(any("cannot exceed Max Marks" in e for e in errors))

    def test_marks_lost_must_be_whole_number(self):
        grid = pd.DataFrame([self.row("1", 5, "1.5", "Careless Error")])
        errors = validate_grid(grid, 75)
        self.assertTrue(any("whole number" in e for e in errors))

    def test_blank_marks_lost_is_blocked(self):
        grid = pd.DataFrame([self.row("1", 5, "", None)])
        errors = validate_grid(grid, 75)
        self.assertTrue(any("Marks Lost is required" in e for e in errors))

    def test_mapping_must_be_exact(self):
        grid = pd.DataFrame([self.row("1", 5, 0, "No Error", mapping_valid=False)])
        errors = validate_grid(grid, 75)
        self.assertTrue(any("exactly one Topic and one Sub-topic" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
