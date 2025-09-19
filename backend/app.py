from flask import Flask, request, jsonify
from flask_cors import CORS
from checker.combo_checker import check_combo_list
import os
import uuid
import json
from datetime import datetime
import tempfile

app = Flask(__name__)
CORS(app)

# Store results in memory (for production, use a database)
results = {}

@app.route('/')
def home():
    return jsonify({
        'message': 'Combo Checker API is running',
        'endpoints': {
            'status': '/api/status',
            'check_combos': '/api/check (POST)',
            'get_results': '/api/results/<check_id> (GET)'
        }
    })

@app.route('/api/check', methods=['POST'])
def check_combos():
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file is a text file
        if not file.filename.endswith('.txt'):
            return jsonify({'error': 'File must be a .txt file'}), 400
        
        # Read and process the file
        content = file.read().decode('utf-8')
        combos = content.split('\n')
        combos = [line.strip() for line in combos if line.strip()]
        
        if len(combos) == 0:
            return jsonify({'error': 'No valid combos found in the file'}), 400
        
        # Generate a unique ID for this check
        check_id = str(uuid.uuid4())
        
        # Start the checking process (in a real app, use a background worker)
        result = check_combo_list(combos)
        
        # Store the result
        results[check_id] = {
            'result': result,
            'created_at': datetime.now().isoformat(),
            'status': 'completed'
        }
        
        return jsonify({'check_id': check_id})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/results/<check_id>', methods=['GET'])
def get_results(check_id):
    if check_id not in results:
        return jsonify({'error': 'Result not found'}), 404
    
    return jsonify(results[check_id])

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True)