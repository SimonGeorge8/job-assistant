from flask import Flask 
import os 


app = Flask(__name__)

@app.route('/api/health', methods=['GET'])
def health_check():
    return {"status": "ok"}, 200  #Returns a Json with a status code 

if __name__ == '__main__':
    # Run the application
    app.run(host='0.0.0.0', port=5001, debug=True)