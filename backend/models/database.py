import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class Database:
    def __init__(self, db_path: str = "data/job_assistant.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type VARCHAR(20) NOT NULL CHECK (type IN ('resume', 'cover_letter')),
                    name VARCHAR(100) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    company_name VARCHAR(200),
                    position_title VARCHAR(200),
                    job_description TEXT,
                    extracted_info TEXT, -- JSON string
                    generated_cover_letter TEXT,
                    session_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id VARCHAR(100) PRIMARY KEY,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default templates if they don't exist
            self._insert_default_templates(conn)
            
            conn.commit()
    
    def _insert_default_templates(self, conn):
        """Insert default templates if none exist"""
        # Check if templates exist
        cursor = conn.execute("SELECT COUNT(*) FROM templates")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Default cover letter template
            default_cover_letter = """{
    "greeting": "Dear Hiring Manager,",
    "opening_paragraph": "I am writing to express my interest in joining your development team as a Software Engineer. As a recent Computer Science graduate from Reichman University with a lifelong passion for technology, I am excited to contribute my technical skills and innovative mindset to your organization.",
    "technical_expertise": "My technical expertise spans multiple programming languages including Python, Java, JavaScript, and frameworks like React.js and FastAPI. I have hands-on experience building full-stack applications, implementing AI-powered solutions, and working with cloud architecture using Kubernetes and Docker. Recent projects include developing real-time transcription applications, AI recommendation systems, and distributed portfolio management platforms.",
    "leadership_and_background": "Beyond technical skills, my leadership experience as Head of IT Department at Maccabi Community Leadership has strengthened my communication and mentoring abilities. I am fluent in English and Spanish with dual nationality (Panama/Spain-EU).",
    "motivation_and_passion": "What drives me is a genuine passion for technology that has been with me since childhood. I chose to study in Israel specifically because of its reputation for innovation, and this environment has further fueled my enthusiasm for creating impactful technological solutions.",
    "closing_paragraph": "I would welcome the opportunity to discuss how my technical skills, international background, and passion for software development can contribute to your team's success.",
    "signature": "Sincerely,\\nSimon George Abadi",
    "key_highlights": {
        "education": "Recent Computer Science graduate from Reichman University",
        "programming_languages": ["Python", "Java", "JavaScript"],
        "frameworks": ["React.js", "FastAPI"],
        "technical_skills": ["Full-stack applications", "AI-powered solutions", "Cloud architecture", "Kubernetes", "Docker"],
        "recent_projects": ["Real-time transcription applications", "AI recommendation systems", "Distributed portfolio management platforms"],
        "leadership": "Head of IT Department at Maccabi Community Leadership",
        "soft_skills": ["Communication", "Mentoring"],
        "languages": ["English (Native)", "Spanish (Native)"],
        "nationalities": ["Panama", "Spain-EU"],
        "location_choice": "Studied in Israel for its reputation for innovation",
        "core_motivation": "Lifelong passion for technology since childhood"
    }
}"""
            
            # Default resume content (simplified)
            default_resume = """{
    "name": "Simon George Abadi",
    "email": "simon.abadi@icloud.com",
    "phone": "+34 655 862 801",
    "linkedin": "www.linkedin.com/in/simon-abadi",
    "skills": [
        "Python", "Java", "Haskell", "JavaScript", "C",
        "React.js", "Flask", "FastAPI", "Firebase", "Numpy", "Pandas",
        "Full Stack Dev", "Backend Developer", "DevOps", "Functional Programming",
        "Docker", "Kubernetes", "RESTful APIs", "NGINX", "Microservices Architecture",
        "Machine Learning", "Cloud Computing", "Software Engineering", "AI",
        "OpenAI Embeddings API", "Cosine Similarity", "Vector Search Optimization",
        "Distributed Systems", "Containerization", "Cloud Architecture",
        "HTML", "CSS", "Network Setup", "Troubleshooting", "Hardware Maintenance"
    ],
    "coursework": [
        "Software Development using AI",
        "Cloud Computing and Software Engineering",
        "Numerical Optimization in Python",
        "Machine Learning",
        "Algorithms",
        "Operating Systems",
        "Functional Programming",
        "Complexity Theory"
    ],
    "projects": [
        {
            "title": "AI Show Recommendation",
            "role": "Developer",
            "duration": "December 2024",
            "description": "Engineered a sophisticated content recommendation algorithm using OpenAI's embeddings API to transform TV show descriptions into semantic vector embeddings, Implementing cosine similarity calculations and vector search optimization to enable precise content matching with 95%+ accuracy."
        },
        {
            "title": "Cloud-Based Portfolio Management Application",
            "role": "Developer",
            "duration": "November 2024 - March 2025",
            "description": "Architected and deployed a distributed portfolio management system utilizing Kubernetes, Docker containers, and microservices architecture. Implemented RESTful API endpoints and configured NGINX as a proxy server to ensure secure and efficient communication between services. Applied cloud architecture principles to build a scalable application with emphasis on containerization and distributed systems design."
        }
    ],
    "experience": [
        {
            "title": "Volunteer in Logistics and Fundraising",
            "company": "Guinness World Record 'Largest Fried Plantain'",
            "location": "Panama City, Panama",
            "duration": "October 2019",
            "description": "Planned logistics for 'PataRun,' 3km marathon, coordinating with 11 sponsors and 6 advertising outlets to raise funds for the main event."
        },
        {
            "title": "Head of IT Department & Youth Leader",
            "company": "Maccabi Community Leadership",
            "location": "Panama City, Panama",
            "duration": "January 2018 - August 2021",
            "description": "Managed IT operations, including network setup, troubleshooting, and hardware maintenance for the whole organization. Led the design and development of the organization's first official website using HTML and CSS, establishing their initial digital presence and online community engagement platform. Served as youth leader, mentoring young community members while simultaneously overseeing technology initiatives that enhanced educational and recreational programming."
        }
    ],
    "education": [
        {
            "degree": "Bachelor of Science in Computer Science",
            "school": "Reichman University",
            "year": "August 2022 - July 2025"
        },
        {
            "degree": "High School Diploma",
            "school": "MDA",
            "location": "Panama City, Panama",
            "year": "June 2022"
        }
    ],
    "awards": [
        "Maccabi Community Leadership",
        "AP Scholar Award",
        "AP Seminar and Research Certificate Award"
    ],
    "languages": [
        "English (Fluent)",
        "Spanish (Fluent)"
    ],
    "nationalities": [
        "Panama",
        "Spain (EU)"
    ],
    "interests": [
        "Programming",
        "Artificial Intelligence (AI)",
        "Robotics",
        "Running",
        "Guitar"
    ]
}"""
            conn.execute('''
                INSERT INTO templates (type, name, content) 
                VALUES (?, ?, ?)
            ''', ('cover_letter', 'Default Cover Letter', default_cover_letter))
            
            conn.execute('''
                INSERT INTO templates (type, name, content) 
                VALUES (?, ?, ?)
            ''', ('resume', 'Default Resume', default_resume))
    
    def get_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all templates or filter by type"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if template_type:
                cursor = conn.execute(
                    "SELECT * FROM templates WHERE type = ? ORDER BY created_at DESC", 
                    (template_type,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM templates ORDER BY created_at DESC"
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def get_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get template by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM templates WHERE id = ?", 
                (template_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_template(self, template_type: str, name: str, content: str) -> int:
        """Create new template"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO templates (type, name, content) 
                VALUES (?, ?, ?)
            ''', (template_type, name, content))
            conn.commit()
            return cursor.lastrowid
    
    def update_template(self, template_id: int, name: str, content: str) -> bool:
        """Update existing template"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                UPDATE templates 
                SET name = ?, content = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (name, content, template_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_template(self, template_id: int) -> bool:
        """Delete template"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def save_job_application(self, url: str, company_name: str, position_title: str, 
                           job_description: str, extracted_info: Dict[str, Any], 
                           generated_cover_letter: str, session_id: str) -> int:
        """Save job application data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO jobs (url, company_name, position_title, job_description, 
                                extracted_info, generated_cover_letter, session_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (url, company_name, position_title, job_description, 
                  json.dumps(extracted_info), generated_cover_letter, session_id))
            conn.commit()
            return cursor.lastrowid
    
    def get_job_history(self, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get job application history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if session_id:
                cursor = conn.execute('''
                    SELECT * FROM jobs WHERE session_id = ? 
                    ORDER BY created_at DESC LIMIT ?
                ''', (session_id, limit))
            else:
                cursor = conn.execute('''
                    SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?
                ''', (limit,))
            
            jobs = []
            for row in cursor.fetchall():
                job = dict(row)
                if job['extracted_info']:
                    try:
                        job['extracted_info'] = json.loads(job['extracted_info'])
                    except json.JSONDecodeError:
                        job['extracted_info'] = {}
                jobs.append(job)
            return jobs
    
    def create_session(self, session_id: str):
        """Create new session"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO sessions (id) VALUES (?)
            ''', (session_id,))
            conn.commit()
    
    def update_session_activity(self, session_id: str):
        """Update session last activity"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE sessions SET last_activity = CURRENT_TIMESTAMP WHERE id = ?
            ''', (session_id,))
            conn.commit()

# Global database instance
db = Database()