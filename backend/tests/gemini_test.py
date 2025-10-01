import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys
from io import StringIO

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.gemini import GeminiService

class TestGeminiService(unittest.TestCase):
    """Test suite for GeminiService class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Mock the environment variable
        self.mock_api_key = "test_api_key_12345"
        os.environ["GEMINI_API_KEY"] = self.mock_api_key
        
        # Sample test data
        self.sample_job_content = """
        Company: TechCorp Inc.
        Position: Senior Software Engineer
        Location: San Francisco, CA
        Job Type: Full-time
        
        Requirements:
        - 5+ years of Python experience
        - Strong knowledge of cloud platforms
        - Excellent communication skills
        
        Benefits:
        - Health insurance
        - 401k matching
        - Remote work options
        """
        
        self.sample_job_url = "https://example.com/jobs/12345"
        
        self.sample_job_info = {
            "company_name": "TechCorp Inc.",
            "position_title": "Senior Software Engineer",
            "department": "Engineering",
            "location": "San Francisco, CA",
            "job_type": "Full-time",
            "salary_range": "$120k-$180k",
            "key_requirements": ["5+ years Python", "Cloud platforms", "Communication"],
            "preferred_skills": ["Docker", "Kubernetes", "AWS"],
            "company_description": "Leading tech company",
            "role_description": "Build scalable applications",
            "benefits": ["Health insurance", "401k", "Remote work"],
            "company_culture": "Innovative and collaborative",
            "growth_opportunities": "Leadership positions available",
            "remote_work": "Hybrid remote"
        }
        
        self.sample_resume_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Previous Corp",
                    "duration": "3 years",
                    "achievements": ["Built microservices", "Led team of 5"]
                }
            ],
            "skills": ["Python", "AWS", "Docker", "REST APIs"]
        }
        
        self.sample_cover_letter_template = """
        Dear Hiring Manager,
        
        I am writing to express my interest in the {position_title} position at {company_name}.
        
        {personalized_content}
        
        I am excited about {company_reasons} and would love to contribute to your team.
        
        Sincerely,
        John Doe
        """
    
    def tearDown(self):
        """Clean up after each test method"""
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
    
    @patch('services.gemini.genai.Client')
    def test_init_with_valid_api_key(self, mock_client_class):
        """Test initialization with valid API key"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        service = GeminiService()
        
        self.assertEqual(service.api_key, self.mock_api_key)
        mock_client_class.assert_called_once_with(api_key=self.mock_api_key)
        self.assertEqual(service.client, mock_client_instance)
    
    def test_init_without_api_key(self):
        """Test initialization fails without API key"""
        del os.environ["GEMINI_API_KEY"]
        
        with self.assertRaises(ValueError) as context:
            GeminiService()
        
        self.assertIn("GEMINI_API_KEY", str(context.exception))
    
    @patch('services.gemini.genai.Client')
    def test_analyze_job_posting_success(self, mock_client_class):
        """Test successful job posting analysis"""
        # Setup mock
        mock_response = Mock()
        mock_response.text = json.dumps(self.sample_job_info)
        
        mock_models = Mock()
        mock_models.generate_content.return_value = mock_response
        
        mock_client_instance = Mock()
        mock_client_instance.models = mock_models
        mock_client_class.return_value = mock_client_instance
        
        service = GeminiService()
        result = service.analyze_job_posting(self.sample_job_content, self.sample_job_url)
        
        self.assertEqual(result["company_name"], "TechCorp Inc.")
        self.assertEqual(result["position_title"], "Senior Software Engineer")
        self.assertIn("key_requirements", result)
        mock_models.generate_content.assert_called_once()
        
        # Verify the call was made with correct parameters
        call_args = mock_models.generate_content.call_args
        self.assertEqual(call_args.kwargs['model'], "gemini-2.5-flash")
    
    @patch('services.gemini.genai.Client')
    def test_analyze_job_posting_with_markdown_json(self, mock_client_class):
        """Test job analysis with markdown-wrapped JSON response"""
        # Setup mock with markdown code blocks
        mock_response = Mock()
        mock_response.text = f"```json\n{json.dumps(self.sample_job_info)}\n```"
        
        mock_models = Mock()
        mock_models.generate_content.return_value = mock_response
        
        mock_client_instance = Mock()
        mock_client_instance.models = mock_models
        mock_client_class.return_value = mock_client_instance
        
        service = GeminiService()
        result = service.analyze_job_posting(self.sample_job_content, self.sample_job_url)
        
        self.assertEqual(result["company_name"], "TechCorp Inc.")
        self.assertIsInstance(result, dict)
    
    @patch('services.gemini.genai.Client')
    @patch('sys.stdout', new_callable=StringIO)
    def test_analyze_job_posting_json_decode_error(self, mock_stdout, mock_client_class):
        """Test job analysis handles JSON decode errors gracefully"""
        # Setup mock with invalid JSON
        mock_response = Mock()
        mock_response.text = "This is not valid JSON"
        
        mock_models = Mock()
        mock_models.generate_content.return_value = mock_response
        
        mock_client_instance = Mock()
        mock_client_instance.models = mock_models
        mock_client_class.return_value = mock_client_instance
        
        service = GeminiService()
        result = service.analyze_job_posting(self.sample_job_content, self.sample_job_url)
        
        # Should return default structure
        self.assertIn("company_name", result)
        self.assertIn("position_title", result)
        self.assertIsInstance(result["key_requirements"], list)
    
    @patch('services.gemini.genai.Client')
    @patch('sys.stdout', new_callable=StringIO)
    def test_analyze_job_posting_api_exception(self, mock_stdout, mock_client_class):
        """Test job analysis handles API exceptions"""
        # Setup mock to raise exception
        mock_models = Mock()
        mock_models.generate_content.side_effect = Exception("API Error")
        
        mock_client_instance = Mock()
        mock_client_instance.models = mock_models
        mock_client_class.return_value = mock_client_instance
        
        service = GeminiService()
        result = service.analyze_job_posting(self.sample_job_content, self.sample_job_url)
        
        # Should return default structure
        self.assertIsInstance(result, dict)
        self.assertIn("company_name", result)
    
    @patch('services.gemini.genai.Client')
    def test_personalize_cover_letter_success(self, mock_client_class):
        """Test successful cover letter personalization"""
        # Setup mock
        mock_response = Mock()
        personalized_letter = "Dear Hiring Manager,\n\nI am excited to apply for Senior Software Engineer at TechCorp Inc."
        mock_response.text = personalized_letter
        
        mock_models = Mock()
        mock_models.generate_content.return_value = mock_response
        
        mock_client_instance = Mock()
        mock_client_instance.models = mock_models
        mock_client_class.return_value = mock_client_instance
        
        service = GeminiService()
        result = service.personalize_cover_letter(
            self.sample_cover_letter_template,
            self.sample_job_info,
            self.sample_resume_data
        )
        
        self.assertEqual(result, personalized_letter)
        mock_models.generate_content.assert_called()
    
    @patch('services.gemini.genai.Client')
    @patch('sys.stdout', new_callable=StringIO)
    def test_personalize_cover_letter_exception(self, mock_stdout, mock_client_class):
        """Test cover letter personalization handles exceptions"""
        # Setup mock to raise exception
        mock_models = Mock()
        mock_models.generate_content.side_effect = Exception("API Error")
        
        mock_client_instance = Mock()
        mock_client_instance.models = mock_models
        mock_client_class.return_value = mock_client_instance
        
        service = GeminiService()
        result = service.personalize_cover_letter(
            self.sample_cover_letter_template,
            self.sample_job_info,
            self.sample_resume_data
        )
        
        # Should return fallback letter with basic replacements
        self.assertIn("TechCorp Inc.", result)
        self.assertIn("Senior Software Engineer", result)
    
    @patch('services.gemini.genai.Client')
    def test_clean_json_response_with_markdown(self, mock_client_class):
        """Test JSON cleaning with markdown code blocks"""
        mock_client_class.return_value = Mock()
        service = GeminiService()
        
        input_text = f"```json\n{json.dumps(self.sample_job_info)}\n```"
        result = service._clean_json_response(input_text)
        
        # Should be valid JSON without markdown
        parsed = json.loads(result)
        self.assertEqual(parsed["company_name"], "TechCorp Inc.")
    
    @patch('services.gemini.genai.Client')
    def test_clean_json_response_with_extra_text(self, mock_client_class):
        """Test JSON cleaning with extra text around JSON"""
        mock_client_class.return_value = Mock()
        service = GeminiService()
        
        input_text = f"Here is the JSON:\n{json.dumps(self.sample_job_info)}\nEnd of response"
        result = service._clean_json_response(input_text)
        
        # Should extract only the JSON object
        parsed = json.loads(result)
        self.assertIsInstance(parsed, dict)
    
    @patch('services.gemini.genai.Client')
    def test_create_default_job_info(self, mock_client_class):
        """Test creation of default job info structure"""
        mock_client_class.return_value = Mock()
        service = GeminiService()
        
        result = service._create_default_job_info(self.sample_job_content, self.sample_job_url)
        
        self.assertIn("company_name", result)
        self.assertIn("position_title", result)
        self.assertIsInstance(result["key_requirements"], list)
        self.assertIsInstance(result["benefits"], list)
        self.assertGreater(len(result["key_requirements"]), 0)
    
    @patch('services.gemini.genai.Client')
    def test_create_default_job_info_extracts_company(self, mock_client_class):
        """Test default job info extracts company name when available"""
        mock_client_class.return_value = Mock()
        service = GeminiService()
        
        content = "Company: Amazing Tech\nPosition: Developer"
        result = service._create_default_job_info(content, self.sample_job_url)
        
        self.assertEqual(result["company_name"], "Amazing Tech")
        self.assertEqual(result["position_title"], "Developer")
    
    @patch('services.gemini.genai.Client')
    def test_create_fallback_cover_letter(self, mock_client_class):
        """Test creation of fallback cover letter"""
        mock_client_class.return_value = Mock()
        service = GeminiService()
        
        result = service._create_fallback_cover_letter(
            self.sample_cover_letter_template,
            self.sample_job_info
        )
        
        self.assertIn("TechCorp Inc.", result)
        self.assertIn("Senior Software Engineer", result)
        self.assertNotIn("{company_name}", result)
        self.assertNotIn("{position_title}", result)
    
    @patch('services.gemini.genai.Client')
    def test_create_fallback_cover_letter_with_missing_keys(self, mock_client_class):
        """Test fallback cover letter handles missing job info keys"""
        mock_client_class.return_value = Mock()
        service = GeminiService()
        
        minimal_job_info = {
            "company_name": "Test Corp",
            "position_title": "Engineer"
        }
        
        result = service._create_fallback_cover_letter(
            self.sample_cover_letter_template,
            minimal_job_info
        )
        
        self.assertIn("Test Corp", result)
        self.assertIn("Engineer", result)


class TestGeminiServiceIntegration(unittest.TestCase):
    """Integration tests for GeminiService (require actual API key)"""
    
    def setUp(self):
        """Check if API key is available for integration tests"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            self.skipTest("GEMINI_API_KEY not set - skipping integration tests")
    
    @unittest.skip("Skipped by default to avoid API costs - remove decorator to run")
    def test_real_job_analysis(self):
        """Test real job analysis with actual API (skipped by default)"""
        service = GeminiService()
        
        job_content = """
        Senior Python Developer
        TechStart Inc. - Remote
        
        We're looking for an experienced Python developer to join our team.
        
        Requirements:
        - 5+ years Python experience
        - Experience with Django/Flask
        - AWS knowledge
        
        Benefits:
        - Competitive salary
        - Remote work
        - Health insurance
        """
        
        result = service.analyze_job_posting(job_content, "https://example.com/job")
        
        self.assertIsInstance(result, dict)
        self.assertIn("company_name", result)


if __name__ == '__main__':
    unittest.main()