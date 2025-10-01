import os
import json
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        self.client = genai.Client(api_key=self.api_key)     

        # self.model = genai.GenerativeModel('gemini-2.5-flash')
    #Works properly 
    def analyze_job_posting(self, job_content: str, job_url: str) -> Dict[str, Any]:
        """Analyze job posting and extract relevant information"""
        prompt = f"""
        Analyze the following job posting and extract key information. Return the response as a valid JSON object with the following structure:

        {{
            "company_name": "Company name",
            "position_title": "Job title",
            "department": "Department if mentioned",
            "location": "Job location",
            "job_type": "Full-time/Part-time/Contract/etc",
            "salary_range": "Salary information if available",
            "key_requirements": ["requirement1", "requirement2", "requirement3"],
            "preferred_skills": ["skill1", "skill2", "skill3"],
            "company_description": "Brief description of the company",
            "role_description": "Brief description of the role",
            "benefits": ["benefit1", "benefit2", "benefit3"],
            "company_culture": "Description of company culture if available",
            "growth_opportunities": "Career growth opportunities mentioned",
            "remote_work": "Remote work policy if mentioned"
        }}

        Job URL: {job_url}
        
        Job Posting Content:
        {job_content}
        
        Please ensure the response is valid JSON format.
        """
        
        try:
            response = self.client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt)
            
            result_text = response.text.strip()
            
            # Clean up the response to ensure it's valid JSON
            result_text = self._clean_json_response(result_text)
            
            # Parse JSON
            job_info = json.loads(result_text)
            return job_info
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw response: {result_text}")
            return self._create_default_job_info(job_content, job_url)
        except Exception as e:
            print(f"Error analyzing job posting: {e}")
            return self._create_default_job_info(job_content, job_url)
    
    def personalize_cover_letter(self, template: str, job_info: Dict[str, Any], resume_data: Dict[str, Any]) -> str:
        """Personalize cover letter based on job information and resume"""
        prompt = f"""
        You are a professional career consultant. Please personalize the following cover letter template based on the job information and candidate's resume.

        Cover Letter Template:
        {template}

        Job Information:
        {json.dumps(job_info, indent=2)}

        Candidate Resume Data:
        {json.dumps(resume_data, indent=2)}

        Instructions:
        1. Replace placeholders like {{company_name}}, {{position_title}} with actual values
        2. Add specific, relevant details about why the candidate is interested in this company
        3. Highlight 2-3 most relevant skills from the candidate's resume that match the job requirements
        4. Include specific examples of the candidate's experience that relate to the job
        5. Mention something specific about the company or role that shows research and genuine interest
        6. Keep the tone professional but personable
        7. Ensure the letter is 3-4 paragraphs and not too lengthy

        Return only the personalized cover letter text, nothing else.
        """
        
        try:
            response = self.client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error personalizing cover letter: {e}")
            return self._create_fallback_cover_letter(template, job_info)
    
    def _clean_json_response(self, text: str) -> str:
        """Clean up JSON response from Gemini"""
        # Remove markdown code blocks if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        
        # Find JSON object in the text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group()
        
        return text
    
    def _create_default_job_info(self, job_content: str, job_url: str) -> Dict[str, Any]:
        """Create default job info structure when parsing fails"""
        # Try to extract basic information with simple regex
        company_match = re.search(r'(?:company|employer|organization):\s*([^\n\r]+)', job_content, re.IGNORECASE)
        title_match = re.search(r'(?:title|position|job):\s*([^\n\r]+)', job_content, re.IGNORECASE)
        
        return {
            "company_name": company_match.group(1).strip() if company_match else "Company",
            "position_title": title_match.group(1).strip() if title_match else "Position",
            "department": "",
            "location": "",
            "job_type": "",
            "salary_range": "",
            "key_requirements": ["Professional experience", "Strong communication skills", "Team collaboration"],
            "preferred_skills": ["Industry knowledge", "Problem-solving", "Adaptability"],
            "company_description": "A growing company focused on innovation and excellence",
            "role_description": "An exciting opportunity to contribute to our team",
            "benefits": ["Competitive salary", "Professional development", "Team environment"],
            "company_culture": "Collaborative and inclusive work environment",
            "growth_opportunities": "Opportunities for career advancement",
            "remote_work": "Please inquire about remote work options"
        }
    
    def _create_fallback_cover_letter(self, template: str, job_info: Dict[str, Any]) -> str:
        """Create fallback cover letter when AI generation fails"""
        # Simple template replacement
        personalized = template.replace("{company_name}", job_info.get("company_name", "Company"))
        personalized = personalized.replace("{position_title}", job_info.get("position_title", "Position"))
        
        # Add basic personalization
        skills = ", ".join(job_info.get("key_requirements", ["professional experience", "strong communication skills"])[:3])
        personalized = personalized.replace("{relevant_skills}", skills)
        
        company_reasons = job_info.get("company_description", "your commitment to excellence and innovation")
        personalized = personalized.replace("{company_reasons}", company_reasons)
        
        personalized_content = f"My experience aligns well with your requirements for {skills}. I am excited about the opportunity to contribute to your team and help achieve your organizational goals."
        personalized = personalized.replace("{personalized_content}", personalized_content)
        
        return personalized

# Global Gemini service instance
gemini_service = GeminiService()