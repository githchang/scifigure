from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SkillContractTest(unittest.TestCase):
    def test_skill_declares_free_form_input(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("completely free-form input", text)
        self.assertIn("Never require `method.md`", text)
        self.assertIn("Do not ask the user to create or supply Figure IR", text)

    def test_custom_input_reference_exists(self):
        text = (ROOT / "references" / "custom-input.md").read_text(encoding="utf-8")
        self.assertIn("A file named `method.md` is optional and never required", text)
        self.assertIn("Do not require the user to prepare these artifacts", text)

    def test_readme_describes_free_form_usage(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("completely free-form input", text)
        self.assertIn("End users are not required to write Figure IR", text)


if __name__ == "__main__":
    unittest.main()
