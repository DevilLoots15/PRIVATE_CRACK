from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
from bs4 import BeautifulSoup
import threading
import concurrent.futures
import uuid
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Store results in memory
results = {}

# Configuration
MAX_RETRIES = 2
THREADS = 10
REQUESTS_PER_SECOND = 20

websites = ["Netflix", "Spotify", "Discord"]  # Reduced for testing

# Throttling
last_request_time = {site: 0 for site in websites}
throttle_lock = {site: threading.Lock() for site in websites}

def throttle(site):
    with throttle_lock[site]:
        now = time.time()
        min_interval = 1.0 / REQUESTS_PER_SECOND
        elapsed = now - last_request_time[site]
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        last_request_time[site] = time.time()

# Simplified checker functions for testing
def check_netflix(email, password):
    try:
        throttle("Netflix")
        # Simulate checking - replace with real API call
        time.sleep(0.1)
        return "Hit" if len(password) > 5 else "Bad"
    except:
        return "Bad"

def check_spotify(email, password):
    try:
        throttle("Spotify")
        # Simulate checking
        time.sleep(0.1)
        return "Hit" if "spotify" in email else "Bad"
    except:
        return "Bad"

def check_discord(email, password):
    try:
        throttle("Discord")
        # Simulate checking
        time.sleep(0.1)
        return "Hit" if len(email) > 0 else "Bad"
    except:
        return "Bad"

def check_site_requests(combo, site):
    try:
        email, password = combo.split(":", 1)
        if site == "Netflix": return check_netflix(email, password)
        if site == "Spotify": return check_spotify(email, password)
        if site == "Discord": return check_discord(email, password)
        return "Bad"
    except:
        return "Bad"

def check_combo(combo):
    result_per_site = {}
    for site in websites:
        status = check_site_requests(combo, site)
        result_per_site[site] = status
    return result_per_site

def check_combo_list(combos):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as executor:
        combo_results = list(executor.map(check_combo, combos))
    
    for i, combo in enumerate(combos):
        results.append({
            'combo': combo,
            'results': combo_results[i]
        })
    
    return results

# Routes
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
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.txt'):
            return jsonify({'error': 'File must be a .txt file'}), 400
        
        content = file.read().decode('utf-8')
        combos = [line.strip() for line in content.split('\n') if line.strip()]
        
        if len(combos) == 0:
            return jsonify({'error': 'No valid combos found in the file'}), 400
        
        check_id = str(uuid.uuid4())
        
        # For testing, just return simulated results
        result = check_combo_list(combos[:5])  # Only check first 5 for testing
        
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