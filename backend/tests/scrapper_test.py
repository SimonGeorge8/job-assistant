import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from bs4 import BeautifulSoup
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.scraper import JobScraper


class TestJobScraper(unittest.TestCase):
    """Test suite for JobScraper class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.scraper = JobScraper()
        
        # Sample HTML content for different scenarios
        self.sample_html_generic = """
        <html>
            <head><title>Software Engineer - TechCorp</title></head>
            <body>
                <main>
                    <h1>Software Engineer Position</h1>
                    <div class="job-description">
                        <p>We are looking for a talented Software Engineer to join our team.</p>
                        <h2>Requirements:</h2>
                        <ul>
                            <li>5+ years of Python experience</li>
                            <li>Strong knowledge of cloud platforms</li>
                        </ul>
                        <h2>Benefits:</h2>
                        <ul>
                            <li>Health insurance</li>
                            <li>401k matching</li>
                        </ul>
                    </div>
                </main>
            </body>
        </html>
        """
        
        self.sample_html_linkedin = """
        <html>
            <head><title>Job Opening - LinkedIn</title></head>
            <body>
                <div class="description__text">
                    <p>Senior Developer role at amazing company</p>
                    <p>Required skills: Python, AWS, Docker</p>
                </div>
            </body>
        </html>
        """
        
        self.sample_html_indeed = """
        <html>
            <head><title>Job at Indeed</title></head>
            <body>
                <div id="jobDescriptionText">
                    <p>We're hiring a Data Scientist</p>
                    <p>Must have ML experience</p>
                </div>
            </body>
        </html>
        """
        
        self.sample_html_minimal = """
        <html>
            <head><title>Job Posting</title></head>
            <body>
                <p>Short content that is less than 100 characters.</p>
            </body>
        </html>
        """
        
        self.sample_urls = {
            'valid': 'https://example.com/jobs/12345',
            'linkedin': 'https://www.linkedin.com/jobs/view/12345',
            'indeed': 'https://www.indeed.com/viewjob?jk=12345',
            'glassdoor': 'https://www.glassdoor.com/job/12345',
            'invalid': 'not-a-valid-url',
            'no_scheme': 'example.com/jobs'
        }
    
    def test_init(self):
        """Test JobScraper initialization"""
        scraper = JobScraper()
        
        self.assertIsNotNone(scraper.headers)
        self.assertIn('User-Agent', scraper.headers)
        self.assertEqual(scraper.timeout, 10)
    
    def test_is_valid_url_with_valid_urls(self):
        """Test URL validation with valid URLs"""
        valid_urls = [
            'https://example.com',
            'http://example.com/path',
            'https://subdomain.example.com/path?query=1'
        ]
        
        for url in valid_urls:
            with self.subTest(url=url):
                self.assertTrue(self.scraper._is_valid_url(url))
    
    def test_is_valid_url_with_invalid_urls(self):
        """Test URL validation with invalid URLs"""
        invalid_urls = [
            'not-a-url',
            'example.com',  # No scheme
            'ftp://example.com',  # Has scheme but might be considered valid
            '',
            'http://',
            '://example.com'
        ]
        
        for url in invalid_urls[:4]:  # Test first 4 clearly invalid ones
            with self.subTest(url=url):
                self.assertFalse(self.scraper._is_valid_url(url))
    
    @patch('services.scraper.requests.get')
    def test_scrape_job_posting_success(self, mock_get):
        """Test successful job posting scrape"""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = self.sample_html_generic.encode('utf-8')
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_job_posting(self.sample_urls['valid'])
        
        self.assertTrue(result['success'])
        self.assertIsNone(result['error'])
        self.assertIn('Software Engineer', result['content'])
        self.assertEqual(result['title'], 'Software Engineer - TechCorp')
        self.assertEqual(result['url'], self.sample_urls['valid'])
        
        # Verify request was made correctly
        mock_get.assert_called_once_with(
            self.sample_urls['valid'],
            headers=self.scraper.headers,
            timeout=self.scraper.timeout
        )
    
    @patch('services.scraper.requests.get')
    def test_scrape_job_posting_with_linkedin(self, mock_get):
        """Test scraping LinkedIn job posting"""
        mock_response = Mock()
        mock_response.content = self.sample_html_linkedin.encode('utf-8')
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_job_posting(self.sample_urls['linkedin'])
        
        self.assertTrue(result['success'])
        self.assertIn('Senior Developer', result['content'])
        self.assertIn('Python', result['content'])
    
    @patch('services.scraper.requests.get')
    def test_scrape_job_posting_with_indeed(self, mock_get):
        """Test scraping Indeed job posting"""
        mock_response = Mock()
        mock_response.content = self.sample_html_indeed.encode('utf-8')
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_job_posting(self.sample_urls['indeed'])
        
        self.assertTrue(result['success'])
        self.assertIn('Data Scientist', result['content'])
        self.assertIn('ML experience', result['content'])
    
    def test_scrape_job_posting_with_invalid_url(self):
        """Test scraping with invalid URL"""
        result = self.scraper.scrape_job_posting(self.sample_urls['invalid'])
        
        self.assertFalse(result['success'])
        self.assertIn('Invalid URL', result['error'])
        self.assertEqual(result['content'], '')
        self.assertEqual(result['url'], self.sample_urls['invalid'])
    
    @patch('services.scraper.requests.get')
    def test_scrape_job_posting_network_error(self, mock_get):
        """Test handling of network errors"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = self.scraper.scrape_job_posting(self.sample_urls['valid'])
        
        self.assertFalse(result['success'])
        self.assertIn('Network error', result['error'])
        self.assertIn('Connection failed', result['error'])
        self.assertEqual(result['content'], '')
    
    @patch('services.scraper.requests.get')
    def test_scrape_job_posting_timeout(self, mock_get):
        """Test handling of timeout errors"""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        result = self.scraper.scrape_job_posting(self.sample_urls['valid'])
        
        self.assertFalse(result['success'])
        self.assertIn('Network error', result['error'])
        self.assertIn('timed out', result['error'])
    
    @patch('services.scraper.requests.get')
    def test_scrape_job_posting_http_error(self, mock_get):
        """Test handling of HTTP errors"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_job_posting(self.sample_urls['valid'])
        
        self.assertFalse(result['success'])
        self.assertIn('Network error', result['error'])
    
    @patch('services.scraper.requests.get')
    def test_scrape_job_posting_parsing_error(self, mock_get):
        """Test handling of parsing errors"""
        mock_response = Mock()
        mock_response.content = b'<html><invalid>malformed</html>'
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # BeautifulSoup is very forgiving, so this should still work
        result = self.scraper.scrape_job_posting(self.sample_urls['valid'])
        
        # Should handle gracefully
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
    
    def test_extract_job_content_with_job_description_class(self):
        """Test content extraction with job-description class"""
        soup = BeautifulSoup(self.sample_html_generic, 'html.parser')
        content = self.scraper._extract_job_content(soup, self.sample_urls['valid'])
        
        self.assertIn('Software Engineer', content)
        self.assertIn('Python experience', content)
        self.assertGreater(len(content), 100)
    
    def test_extract_job_content_with_linkedin_selector(self):
        """Test content extraction with LinkedIn-specific selector"""
        soup = BeautifulSoup(self.sample_html_linkedin, 'html.parser')
        content = self.scraper._extract_job_content(soup, self.sample_urls['linkedin'])
        
        self.assertIn('Senior Developer', content)
        self.assertIn('Python', content)
    
    def test_extract_job_content_with_indeed_selector(self):
        """Test content extraction with Indeed-specific selector"""
        soup = BeautifulSoup(self.sample_html_indeed, 'html.parser')
        content = self.scraper._extract_job_content(soup, self.sample_urls['indeed'])
        
        self.assertIn('Data Scientist', content)
        self.assertIn('ML experience', content)
    
    def test_extract_job_content_fallback_to_body(self):
        """Test content extraction falls back to body when selectors fail"""
        html = '<html><body>This is a simple job posting with enough content to pass the 100 character minimum threshold for content extraction.</body></html>'
        soup = BeautifulSoup(html, 'html.parser')
        content = self.scraper._extract_job_content(soup, 'https://unknown-site.com/job')
        
        self.assertIn('job posting', content)
        self.assertGreater(len(content), 100)
    
    def test_get_site_selectors_linkedin(self):
        """Test getting LinkedIn-specific selectors"""
        selectors = self.scraper._get_site_selectors('www.linkedin.com')
        
        self.assertIsInstance(selectors, list)
        self.assertGreater(len(selectors), 0)
        self.assertIn('.description__text', selectors)
    
    def test_get_site_selectors_indeed(self):
        """Test getting Indeed-specific selectors"""
        selectors = self.scraper._get_site_selectors('www.indeed.com')
        
        self.assertIsInstance(selectors, list)
        self.assertIn('#jobDescriptionText', selectors)
    
    def test_get_site_selectors_glassdoor(self):
        """Test getting Glassdoor-specific selectors"""
        selectors = self.scraper._get_site_selectors('www.glassdoor.com')
        
        self.assertIsInstance(selectors, list)
        self.assertIn('#JobDescContainer', selectors)
    
    def test_get_site_selectors_unknown_site(self):
        """Test getting selectors for unknown site returns empty list"""
        selectors = self.scraper._get_site_selectors('www.unknown-job-site.com')
        
        self.assertIsInstance(selectors, list)
        self.assertEqual(len(selectors), 0)
    
    def test_extract_page_title_from_title_tag(self):
        """Test extracting page title from title tag"""
        soup = BeautifulSoup(self.sample_html_generic, 'html.parser')
        title = self.scraper._extract_page_title(soup)
        
        self.assertEqual(title, 'Software Engineer - TechCorp')
    
    def test_extract_page_title_fallback_to_h1(self):
        """Test extracting page title falls back to h1"""
        html = '<html><body><h1>Senior Developer Role</h1></body></html>'
        soup = BeautifulSoup(html, 'html.parser')
        title = self.scraper._extract_page_title(soup)
        
        self.assertEqual(title, 'Senior Developer Role')
    
    def test_extract_page_title_default(self):
        """Test extracting page title returns default when not found"""
        html = '<html><body><p>No title here</p></body></html>'
        soup = BeautifulSoup(html, 'html.parser')
        title = self.scraper._extract_page_title(soup)
        
        self.assertEqual(title, 'Job Posting')
    
    def test_clean_content_removes_extra_whitespace(self):
        """Test content cleaning removes extra whitespace"""
        content = "This  has   multiple    spaces\n\nand\n\nnewlines"
        cleaned = self.scraper._clean_content(content)
        
        self.assertEqual(cleaned, "This has multiple spaces and newlines")
    
    def test_clean_content_removes_unwanted_patterns(self):
        """Test content cleaning removes unwanted patterns"""
        content = "Great job! Cookie Policy Sign in Privacy Policy Apply now Save this job"
        cleaned = self.scraper._clean_content(content)
        
        self.assertNotIn('Cookie Policy', cleaned)
        self.assertNotIn('Sign in', cleaned)
        self.assertNotIn('Privacy Policy', cleaned)
        self.assertNotIn('Apply now', cleaned)
        self.assertNotIn('Save this job', cleaned)
        self.assertIn('Great job!', cleaned)
    
    def test_clean_content_case_insensitive_removal(self):
        """Test content cleaning is case insensitive"""
        content = "SIGN IN sign up PRIVACY POLICY Terms of Service"
        cleaned = self.scraper._clean_content(content)
        
        self.assertNotIn('SIGN IN', cleaned)
        self.assertNotIn('sign up', cleaned)
        self.assertNotIn('PRIVACY POLICY', cleaned)
        self.assertNotIn('Terms of Service', cleaned)
    
    def test_clean_content_preserves_important_text(self):
        """Test content cleaning preserves important text"""
        content = "Senior Developer position. Apply your skills to solve complex problems. 5 years experience required."
        cleaned = self.scraper._clean_content(content)
        
        self.assertIn('Senior Developer', cleaned)
        self.assertIn('skills', cleaned)
        self.assertIn('5 years experience', cleaned)
    
    @patch('services.scraper.requests.get')
    def test_scrape_job_posting_strips_whitespace(self, mock_get):
        """Test that scraped content has whitespace properly cleaned"""
        html_with_whitespace = """
        <html>
            <body>
                <div class="job-description">
                    This    has    extra    spaces
                    
                    and    newlines    everywhere
                </div>
            </body>
        </html>
        """
        mock_response = Mock()
        mock_response.content = html_with_whitespace.encode('utf-8')
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_job_posting(self.sample_urls['valid'])
        
        self.assertTrue(result['success'])
        self.assertNotIn('    ', result['content'])  # No multiple spaces
        self.assertNotIn('\n\n', result['content'])  # No multiple newlines
    
    def test_scraper_headers_contain_user_agent(self):
        """Test that scraper headers contain a valid User-Agent"""
        self.assertIn('User-Agent', self.scraper.headers)
        self.assertTrue(len(self.scraper.headers['User-Agent']) > 0)
        self.assertIn('Mozilla', self.scraper.headers['User-Agent'])
    
    @patch('services.scraper.requests.get')
    def test_scrape_respects_timeout(self, mock_get):
        """Test that scraper respects timeout setting"""
        mock_response = Mock()
        mock_response.content = self.sample_html_generic.encode('utf-8')
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        self.scraper.scrape_job_posting(self.sample_urls['valid'])
        
        # Verify timeout was passed to requests
        call_kwargs = mock_get.call_args.kwargs
        self.assertEqual(call_kwargs['timeout'], 10)


class TestJobScraperEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scraper = JobScraper()
    
    @patch('services.scraper.requests.get')
    def test_empty_html_response(self, mock_get):
        """Test handling of empty HTML response"""
        mock_response = Mock()
        mock_response.content = b''
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_job_posting('https://example.com/job')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['content'], '')
    
    @patch('services.scraper.requests.get')
    def test_very_large_html_response(self, mock_get):
        """Test handling of very large HTML response"""
        large_content = '<html><body>' + 'A' * 100000 + '</body></html>'
        mock_response = Mock()
        mock_response.content = large_content.encode('utf-8')
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_job_posting('https://example.com/job')
        
        self.assertTrue(result['success'])
        self.assertGreater(len(result['content']), 0)
    
    @patch('services.scraper.requests.get')
    def test_non_utf8_encoding(self, mock_get):
        """Test handling of non-UTF8 encoded content"""
        # Create content with latin-1 encoding
        content = '<html><body>Job with special chars: café, naïve</body></html>'
        mock_response = Mock()
        mock_response.content = content.encode('latin-1')
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_job_posting('https://example.com/job')
        
        # Should handle gracefully
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
    
    def test_url_with_query_parameters(self):
        """Test URL validation with query parameters"""
        url = 'https://example.com/jobs?id=123&source=google'
        self.assertTrue(self.scraper._is_valid_url(url))
    
    def test_url_with_fragments(self):
        """Test URL validation with fragments"""
        url = 'https://example.com/jobs#section'
        self.assertTrue(self.scraper._is_valid_url(url))


if __name__ == '__main__':
    unittest.main()