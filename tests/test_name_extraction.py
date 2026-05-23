import unittest
from unittest.mock import patch

from ai_parser import extract_best_candidate_name, extract_best_candidate_name_debug


class NameExtractionTests(unittest.TestCase):
    @patch("ai_parser.ollama.chat", side_effect=Exception("ollama unavailable"))
    def test_prefers_clean_uppercase_header_name(self, _mock_chat):
        resume_text = """
        TUSHAR KUKWASE
        Machine Learning Engineer (Remote Internship)
        +91 9876543210
        tushar.kukwase@gmail.com
        linkedin.com/in/tushar-kukwase
        """

        self.assertEqual(
            extract_best_candidate_name(resume_text, email="tushar.kukwase@gmail.com"),
            "Tushar Kukwase",
        )

    @patch("ai_parser.ollama.chat", side_effect=Exception("ollama unavailable"))
    def test_rejects_role_title_when_it_appears_before_name(self, _mock_chat):
        resume_text = """
        Machine Learning Engineer (Remote Internship)
        TUSHAR KUKWASE
        Email: tushar.kukwase@gmail.com
        GitHub: github.com/tusharkukwase
        """

        self.assertEqual(
            extract_best_candidate_name(resume_text, email="tushar.kukwase@gmail.com"),
            "Tushar Kukwase",
        )

    @patch("ai_parser.ollama.chat", side_effect=Exception("ollama unavailable"))
    def test_company_name_does_not_outrank_human_name(self, _mock_chat):
        resume_text = """
        EsperaTech
        Software Engineer with hands-on experience in Flask and MongoDB
        TUSHAR KUKWASE
        +91 9876543210
        tushar.kukwase@gmail.com
        """

        debug = extract_best_candidate_name_debug(resume_text, email="tushar.kukwase@gmail.com")

        self.assertEqual(debug["selected_name"], "Tushar Kukwase")
        rejected_company = [item for item in debug["top_candidates"] if item["text"].startswith("Espera")]
        self.assertTrue(rejected_company)
        self.assertIn("company_name", rejected_company[0]["rejection_reasons"])

    @patch("ai_parser.ollama.chat", side_effect=Exception("ollama unavailable"))
    def test_returns_candidate_when_no_reliable_header_exists(self, _mock_chat):
        resume_text = """
        WORK EXPERIENCE
        PROFESSIONAL EXPERIENCE
        Software Engineer with hands-on experience in Python and Flask
        EsperaTech Pvt Ltd
        Machine Learning Engineer
        """

        debug = extract_best_candidate_name_debug(resume_text, fallback_name="Shootingwala")

        self.assertEqual(debug["selected_name"], "Candidate")
        self.assertIn("no_reliable_name_candidate", debug["rejection_reasons"])

    @patch("ai_parser.ollama.chat", side_effect=Exception("ollama unavailable"))
    def test_handles_name_with_heading_noise(self, _mock_chat):
        resume_text = """
        BRETTE GANA WORK EXPERIENCE
        Registered Nurse
        brette.gana@email.com
        +1 412 555 9988
        """

        self.assertEqual(
            extract_best_candidate_name(resume_text, email="brette.gana@email.com"),
            "Brette Gana",
        )

    @patch("ai_parser.ollama.chat", side_effect=Exception("ollama unavailable"))
    def test_debug_metadata_marks_role_titles_as_rejected(self, _mock_chat):
        resume_text = """
        TUSHAR KUKWASE
        Software Engineer
        Machine Learning Engineer
        Email: tushar.kukwase@gmail.com
        """

        debug = extract_best_candidate_name_debug(resume_text, email="tushar.kukwase@gmail.com")
        rejected_titles = {
            item["text"]: item["rejection_reasons"]
            for item in debug["top_candidates"]
            if item["text"] in {"Software Engineer", "Machine Learning Engineer"}
        }

        self.assertEqual(debug["selected_name"], "Tushar Kukwase")
        self.assertIn("role_title", rejected_titles["Software Engineer"])
        self.assertIn("role_title", rejected_titles["Machine Learning Engineer"])

    @patch("ai_parser.ollama.chat", side_effect=Exception("ollama unavailable"))
    def test_rejects_company_and_section_noise_without_header_name(self, _mock_chat):
        resume_text = """
        PROFESSIONAL EXPERIENCE
        Shootingwala
        EsperaTech Pvt Ltd
        Software Engineer with hands-on experience in AWS, Flask, MongoDB, TensorFlow
        """

        debug = extract_best_candidate_name_debug(resume_text)

        self.assertEqual(debug["selected_name"], "Candidate")
        rejected_company = [item for item in debug["top_candidates"] if item["text"].startswith("Espera")]
        rejected_role = [item for item in debug["top_candidates"] if item["text"].startswith("Software Engineer")]
        self.assertTrue(rejected_company)
        self.assertTrue(rejected_role)
        self.assertIn("company_name", rejected_company[0]["rejection_reasons"])
        self.assertIn("role_title", rejected_role[0]["rejection_reasons"])

    @patch("ai_parser.ollama.chat", side_effect=Exception("ollama unavailable"))
    def test_prefers_header_name_over_name_found_inside_experience_section(self, _mock_chat):
        resume_text = """
        TUSHAR KUKWASE
        Email: tushar.kukwase@gmail.com
        EXPERIENCE
        Shootingwala
        PROJECTS
        TUSHAR KUKWASE EDUCATION
        """

        debug = extract_best_candidate_name_debug(resume_text)

        self.assertEqual(debug["selected_name"], "Tushar Kukwase")
        top_candidate = debug["top_candidates"][0]
        self.assertEqual(top_candidate["text"], "Tushar Kukwase")
        self.assertGreaterEqual(debug["confidence"], 0.5)

    @patch("ai_parser.ollama.chat", side_effect=Exception("ollama unavailable"))
    def test_handles_noisy_ocr_header_without_promoting_role_title(self, _mock_chat):
        resume_text = """
        TUSHAR KUKWASE ::::
        Mach1ne Learn1ng Engineer / Remote Internship
        Email - tushar.kukwase@gmail.com
        Mob: +91 9876543210
        """

        debug = extract_best_candidate_name_debug(resume_text)

        self.assertEqual(debug["selected_name"], "Tushar Kukwase")
        rejected_titles = [
            item for item in debug["top_candidates"]
            if "Engineer" in item["text"] or "Internship" in item["text"]
        ]
        self.assertTrue(rejected_titles)
        self.assertTrue(debug["confidence"] >= 0.5)


if __name__ == "__main__":
    unittest.main()
