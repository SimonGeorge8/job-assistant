import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional
from urllib.parse import urljoin, urlparse

class JobScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 10
    
    def scrape_job_posting(self, url: str) -> Dict[str, str]:
        """Scrape job posting content from URL"""
        try:
            # Validate URL
            if not self._is_valid_url(url):
                return {
                    "success": False,
                    "error": "Invalid URL format",
                    "content": "",
                    "title": "",
                    "url": url
                }
            
            # Make request
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract content based on common job site patterns
            content = self._extract_job_content(soup, url)
            title = self._extract_page_title(soup)
            
            # Clean the content
            cleaned_content = self._clean_content(content)
            
            return {
                "success": True,
                "error": None,
                "content": cleaned_content,
                "title": title,
                "url": url
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Network error: {str(e)}",
                "content": "",
                "title": "",
                "url": url
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Scraping error: {str(e)}",
                "content": "",
                "title": "",
                "url": url
            }
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def _extract_job_content(self, soup: BeautifulSoup, url: str) -> str:
        """Extract job content using various strategies based on the site"""
        domain = urlparse(url).netloc.lower()
        
        # Site-specific selectors
        selectors = self._get_site_selectors(domain)
        
        # Try site-specific selectors first
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                content = ' '.join([elem.get_text(strip=True) for elem in elements])
                if len(content) > 100:  # Ensure we got substantial content
                    return content
        
        # Fallback to common selectors
        common_selectors = [
            '[class*="job-description"]',
            '[class*="job-detail"]',
            '[class*="description"]',
            '[id*="job-description"]',
            '[id*="description"]',
            'main',
            '.content',
            '#content',
            'article'
        ]
        
        for selector in common_selectors:
            elements = soup.select(selector)
            if elements:
                content = ' '.join([elem.get_text(strip=True) for elem in elements])
                if len(content) > 100:
                    return content
        
        # Last resort - get all text from body
        body = soup.find('body')
        if body:
            return body.get_text(strip=True)
        
        return soup.get_text(strip=True)
    
    def _get_site_selectors(self, domain: str) -> list:
        """Get site-specific CSS selectors"""
        site_selectors = {
            'linkedin.com': [
                '.description__text',
                '.jobs-description-content__text',
                '.jobs-box__html-content'
            ],
            'indeed.com': [
                '#jobDescriptionText',
                '.jobsearch-jobDescriptionText',
                '.jobsearch-JobComponent-description'
            ],
            'glassdoor.com': [
                '#JobDescContainer',
                '.jobDescriptionContent',
                '[data-test="jobDescription"]'
            ],
            'monster.com': [
                '#JobDescription',
                '.job-description'
            ],
            'ziprecruiter.com': [
                '.job_description',
                '[data-testid="job-description"]'
            ],
            'careerbuilder.com': [
                '.job-description',
                '#job-summary'
            ]
        }
        
        # Find matching domain
        for site, selectors in site_selectors.items():
            if site in domain:
                return selectors
        
        return []
    
    def _extract_page_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_elem = soup.find('title')
        if title_elem:
            return title_elem.get_text(strip=True)
        
        # Try h1 as fallback
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        return "Job Posting"
    
    def _clean_content(self, content: str) -> str:
        """Clean extracted content"""
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common unwanted patterns
        patterns_to_remove = [
            r'Cookie\s+(?:Policy|Notice|Settings)',
            r'Privacy\s+Policy',
            r'Terms\s+(?:of\s+)?(?:Use|Service)',
            r'Sign\s+(?:in|up|In|Up)',
            r'Subscribe\s+to',
            r'Follow\s+us',
            r'Share\s+this\s+job',
            r'Apply\s+(?:now|online)',
            r'Save\s+(?:this\s+)?job',
            r'Report\s+this\s+job'
        ]
        
        for pattern in patterns_to_remove:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Clean up extra spaces again
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content

# Global scraper instance
job_scraper = JobScraper()