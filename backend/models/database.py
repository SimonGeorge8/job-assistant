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
            default_cover_letter = """Dear Hiring Manager,

I am writing to express my strong interest in the {position_title} position at {company_name}. With my background in software development and passion for technology, I am excited about the opportunity to contribute to your team.

{personalized_content}

I am particularly drawn to {company_name} because of {company_reasons}. I believe my skills in {relevant_skills} make me an ideal candidate for this role.

Thank you for considering my application. I look forward to discussing how I can contribute to your team's success.

Best regards,
[Your Name]"""
            
            # Default resume content (simplified)
            default_resume = """{
    "name": "John Doe",
    "email": "john.doe@email.com",
    "phone": "(555) 123-4567",
    "skills": [
        "Python", "JavaScript", "React", "Flask", "Docker", 
        "Git", "SQL", "REST APIs", "Machine Learning"
    ],
    "experience": [
        {
            "title": "Software Developer",
            "company": "Tech Company",
            "duration": "2020-Present",
            "description": "Developed web applications using Python and JavaScript"
        }
    ],
    "education": [
        {
            "degree": "Bachelor of Science in Computer Science",
            "school": "University Name",
            "year": "2020"
        }
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