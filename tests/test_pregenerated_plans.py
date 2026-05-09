import unittest

from uni_app import uni_app as app_module


class PregeneratedPlanTests(unittest.TestCase):
    def test_becs_pregenerated_plans_are_available_for_years_one_and_two(self) -> None:
        degree = "Electronics and Computer Science (BECS)"
        for scope in ("y1s1", "y1s2", "y2s3", "y2s4"):
            with self.subTest(scope=scope):
                plan = app_module._load_pregenerated_study_plan(degree, scope)
                self.assertEqual(len(plan), 110)
                self.assertEqual([entry.get("day") for entry in plan], list(range(1, 111)))
                self.assertTrue(all(entry.get("subject") == "BECS" for entry in plan))

    def test_becs_has_no_year_three_pregenerated_plan(self) -> None:
        plan = app_module._load_pregenerated_study_plan(
            "Electronics and Computer Science (BECS)",
            "y3s5",
        )
        self.assertEqual(plan, [])

    def test_uk_computer_science_pregenerated_plans_are_available_for_years_one_and_two(self) -> None:
        degree = "Computer Science (UK)"
        for scope in ("y1s1", "y1s2", "y2s3", "y2s4"):
            with self.subTest(scope=scope):
                plan = app_module._load_pregenerated_study_plan(degree, scope)
                self.assertEqual(len(plan), 110)
                self.assertEqual([entry.get("day") for entry in plan], list(range(1, 111)))
                self.assertTrue(all(entry.get("subject") == "CS" for entry in plan))

    def test_uk_software_engineering_pregenerated_plans_are_available_for_years_one_and_two(self) -> None:
        degree = "Software Engineering (UK)"
        for scope in ("y1s1", "y1s2", "y2s3", "y2s4"):
            with self.subTest(scope=scope):
                plan = app_module._load_pregenerated_study_plan(degree, scope)
                self.assertEqual(len(plan), 110)
                self.assertEqual([entry.get("day") for entry in plan], list(range(1, 111)))
                self.assertTrue(all(entry.get("subject") == "SE" for entry in plan))

    def test_us_computer_science_pregenerated_plans_are_available_for_years_one_and_two(self) -> None:
        degree = "Computer Science (US)"
        for scope in ("y1s1", "y1s2", "y2s3", "y2s4"):
            with self.subTest(scope=scope):
                plan = app_module._load_pregenerated_study_plan(degree, scope)
                self.assertEqual(len(plan), 110)
                self.assertEqual([entry.get("day") for entry in plan], list(range(1, 111)))
                self.assertTrue(all(entry.get("subject") == "CS" for entry in plan))

    def test_us_software_engineering_pregenerated_plans_are_available_for_years_one_and_two(self) -> None:
        degree = "Software Engineering (US)"
        for scope in ("y1s1", "y1s2", "y2s3", "y2s4"):
            with self.subTest(scope=scope):
                plan = app_module._load_pregenerated_study_plan(degree, scope)
                self.assertEqual(len(plan), 110)
                self.assertEqual([entry.get("day") for entry in plan], list(range(1, 111)))
                self.assertTrue(all(entry.get("subject") == "SE" for entry in plan))

    def test_physical_science_subject_plan_mapping_uses_scoped_subject(self) -> None:
        plan = app_module._load_pregenerated_study_plan("Physical Science", "y1s1:COSC")
        self.assertEqual(len(plan), 110)
        self.assertEqual(plan[0].get("subject"), "COSC")


if __name__ == "__main__":
    unittest.main()
