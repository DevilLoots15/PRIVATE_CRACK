from flask import Flask, request, jsonify
from flask_cors import CORS
from checker.combo_checker import check_combo_list
import os
import uuid
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Store results in memory (for production, use a database)
results = {}

@app.route('/api/check', methods=['POST'])
def check_combos():
    try:
        data = request.get_json()
        if not data or 'combos' not in data:
            return jsonify({'error': 'No combos provided'}), 400
        
        combos = data['combos']
        if not isinstance(combos, list):
            return jsonify({'error': 'Combos should be a list'}), 400
        
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