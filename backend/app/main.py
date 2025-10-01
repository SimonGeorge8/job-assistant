from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import uuid
import traceback
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our services and models
from models.database import db
from services.gemini import gemini_service
from services.scraper import job_scraper

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configuration
app.config['JSON_SORT_KEYS'] = False

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        templates = db.get_templates()
        
        # Test Gemini service (basic check)
        gemini_status = "ok" if gemini_service.api_key else "no_api_key"
        
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "ok",
                "gemini": gemini_status,
                "scraper": "ok"
            },
            "templates_count": len(templates)
        }, 200
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint for processing job URLs"""
    try:
        data = request.get_json()
        if not data:
            return {"error": "No JSON data provided"}, 400
        
        message = data.get('message', '').strip()
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return {"error": "Message is required"}, 400
        
        # Create or update session
        db.create_session(session_id)
        db.update_session_activity(session_id)
        
        # Check if message contains a URL
        if not ('http://' in message or 'https://' in message):
            return {
                "response": "Please provide a valid job listing URL to analyze.",
                "session_id": session_id,
                "status": "error"
            }, 400
        
        # Extract URL from message (simple approach)
        url = message.strip()
        
        # Step 1: Scrape the job posting
        print(f"Scraping job posting from: {url}")
        scrape_result = job_scraper.scrape_job_posting(url)
        
        if not scrape_result['success']:
            return {
                "response": f"Failed to scrape job posting: {scrape_result['error']}",
                "session_id": session_id,
                "status": "error"
            }, 400
        
        job_content = scrape_result['content']
        if len(job_content) < 100:
            return {
                "response": "Unable to extract sufficient job posting content. Please check the URL and try again.",
                "session_id": session_id,
                "status": "error"
            }, 400
        
        # Step 2: Analyze job posting with Gemini
        print("Analyzing job posting with Gemini...")
        job_info = gemini_service.analyze_job_posting(job_content, url)
        
        # Step 3: Get templates
        cover_letter_templates = db.get_templates('cover_letter')
        resume_templates = db.get_templates('resume')
        
        if not cover_letter_templates:
            return {
                "response": "No cover letter templates found. Please create a template first.",
                "session_id": session_id,
                "status": "error"
            }, 400
        
        if not resume_templates:
            return {
                "response": "No resume templates found. Please create a resume template first.",
                "session_id": session_id,
                "status": "error"
            }, 400
        
        # Use the first available templates
        cover_letter_template = cover_letter_templates[0]['content']
        resume_template = resume_templates[0]['content']
        
        # Parse resume data (handle both JSON string and dict)
        try:
            if isinstance(resume_template, str):
                resume_data = json.loads(resume_template)
            else:
                resume_data = resume_template
        except json.JSONDecodeError:
            # Fallback resume data
            resume_data = {
                "skills": ["Python", "JavaScript", "Problem-solving"],
                "experience": [{"title": "Software Developer", "description": "Developed applications"}]
            }
        
        # Step 4: Personalize cover letter
        print("Personalizing cover letter...")
        personalized_cover_letter = gemini_service.personalize_cover_letter(
            cover_letter_template, job_info, resume_data
        )
        
        # Step 5: Save to database
        job_id = db.save_job_application(
            url=url,
            company_name=job_info.get('company_name', ''),
            position_title=job_info.get('position_title', ''),
            job_description=job_content[:5000],  # Limit length for storage
            extracted_info=job_info,
            generated_cover_letter=personalized_cover_letter,
            session_id=session_id
        )
        
        return {
            "response": personalized_cover_letter,
            "job_details": job_info,
            "session_id": session_id,
            "job_id": job_id,
            "status": "success"
        }, 200
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        print(traceback.format_exc())
        return {
            "error": "Internal server error occurred while processing your request",
            "details": str(e),
            "session_id": session_id if 'session_id' in locals() else None,
            "status": "error"
        }, 500

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """Get all templates or filter by type"""
    try:
        template_type = request.args.get('type')
        templates = db.get_templates(template_type)
        return {
            "templates": templates,
            "count": len(templates),
            "status": "success"
        }, 200
    except Exception as e:
        return {"error": str(e), "status": "error"}, 500

@app.route('/api/templates', methods=['POST'])
def create_template():
    """Create new template"""
    try:
        data = request.get_json()
        if not data:
            return {"error": "No JSON data provided"}, 400
        
        template_type = data.get('type')
        name = data.get('name')
        content = data.get('content')
        
        if not all([template_type, name, content]):
            return {"error": "Type, name, and content are required"}, 400
        
        if template_type not in ['resume', 'cover_letter']:
            return {"error": "Type must be 'resume' or 'cover_letter'"}, 400
        
        template_id = db.create_template(template_type, name, content)
        
        return {
            "message": "Template created successfully",
            "template_id": template_id,
            "status": "success"
        }, 201
    except Exception as e:
        return {"error": str(e), "status": "error"}, 500

@app.route('/api/templates/<int:template_id>', methods=['GET'])
def get_template(template_id):
    """Get template by ID"""
    try:
        template = db.get_template_by_id(template_id)
        if not template:
            return {"error": "Template not found"}, 404
        
        return {
            "template": template,
            "status": "success"
        }, 200
    except Exception as e:
        return {"error": str(e), "status": "error"}, 500

@app.route('/api/templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    """Update template"""
    try:
        data = request.get_json()
        if not data:
            return {"error": "No JSON data provided"}, 400
        
        name = data.get('name')
        content = data.get('content')
        
        if not all([name, content]):
            return {"error": "Name and content are required"}, 400
        
        success = db.update_template(template_id, name, content)
        if not success:
            return {"error": "Template not found"}, 404
        
        return {
            "message": "Template updated successfully",
            "status": "success"
        }, 200
    except Exception as e:
        return {"error": str(e), "status": "error"}, 500

@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """Delete template"""
    try:
        success = db.delete_template(template_id)
        if not success:
            return {"error": "Template not found"}, 404
        
        return {
            "message": "Template deleted successfully",
            "status": "success"
        }, 200
    except Exception as e:
        return {"error": str(e), "status": "error"}, 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get job application history"""
    try:
        session_id = request.args.get('session_id')
        limit = int(request.args.get('limit', 50))
        
        history = db.get_job_history(session_id, limit)
        
        return {
            "history": history,
            "count": len(history),
            "status": "success"
        }, 200
    except Exception as e:
        return {"error": str(e), "status": "error"}, 500

@app.route('/api/test-gemini', methods=['POST'])
def test_gemini():
    """Test Gemini API connection"""
    try:
        data = request.get_json()
        test_content = data.get('content', 'Test job posting content')
        
        # Simple test
        job_info = gemini_service.analyze_job_posting(test_content, 'https://example.com/test-job')
        
        return {
            "status": "success",
            "result": job_info,
            "message": "Gemini API is working correctly"
        }, 200
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Gemini API test failed"
        }, 500

@app.route('/api/test-scraper', methods=['POST'])
def test_scraper():
    """Test web scraper"""
    try:
        data = request.get_json()
        url = data.get('url', 'https://example.com')
        
        result = job_scraper.scrape_job_posting(url)
        
        return {
            "status": "success",
            "result": result,
            "message": "Scraper test completed"
        }, 200
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "Scraper test failed"
        }, 500

@app.errorhandler(404)
def not_found(error):
    return {"error": "Endpoint not found"}, 404

@app.errorhandler(405)
def method_not_allowed(error):
    return {"error": "Method not allowed"}, 405

@app.errorhandler(500)
def internal_error(error):
    return {"error": "Internal server error"}, 500

if __name__ == '__main__':
    # Initialize database on startup
    print("Initializing database...")
    db.init_database()
    print("Database initialized!")
    
    # Print available endpoints
    print("\n=== Available API Endpoints ===")
    print("GET  /api/health - Health check")
    print("POST /api/chat - Process job URL")
    print("GET  /api/templates - Get templates")
    print("POST /api/templates - Create template")
    print("GET  /api/templates/<id> - Get template by ID")
    print("PUT  /api/templates/<id> - Update template")
    print("DELETE /api/templates/<id> - Delete template")
    print("GET  /api/history - Get job history")
    print("POST /api/test-gemini - Test Gemini API")
    print("POST /api/test-scraper - Test web scraper")
    print("================================\n")
    
    # Run the application
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)