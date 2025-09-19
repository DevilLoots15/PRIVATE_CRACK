document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('comboFile');
    const fileName = document.getElementById('fileName');
    const checkButton = document.getElementById('checkButton');
    const progressSection = document.querySelector('.progress-section');
    const progressBar = document.querySelector('.progress');
    const progressText = document.getElementById('progressText');
    const resultsSection = document.querySelector('.results-section');
    const totalCombos = document.getElementById('totalCombos');
    const validCombos = document.getElementById('validCombos');
    const completionTime = document.getElementById('completionTime');
    const resultsBody = document.getElementById('resultsBody');
    const downloadButton = document.getElementById('downloadButton');
    const errorSection = document.getElementById('errorSection');
    const errorMessage = document.getElementById('errorMessage');
    
    // Update backend URL based on your Render deployment
    const BACKEND_URL = 'https://your-render-app.onrender.com';
    
    let checkId = null;
    let combos = [];
    
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            fileName.textContent = file.name;
            checkButton.disabled = false;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const content = e.target.result;
                combos = content.split('\n')
                    .map(line => line.trim())
                    .filter(line => line.length > 0);
            };
            reader.readAsText(file);
        } else {
            fileName.textContent = 'No file chosen';
            checkButton.disabled = true;
        }
    });
    
    checkButton.addEventListener('click', function() {
        if (combos.length === 0) {
            showError('No valid combos found in the file');
            return;
        }
        
        // Hide previous results and errors
        resultsSection.classList.add('hidden');
        errorSection.classList.add('hidden');
        
        // Show progress
        progressSection.classList.remove('hidden');
        updateProgress(0);
        
        // Send request to backend
        fetch(`${BACKEND_URL}/api/check`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ combos: combos })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            checkId = data.check_id;
            pollResults();
        })
        .catch(error => {
            showError(error.message);
            progressSection.classList.add('hidden');
        });
    });
    
    function pollResults() {
        if (!checkId) return;
        
        fetch(`${BACKEND_URL}/api/results/${checkId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                if (data.status === 'completed') {
                    displayResults(data.result);
                    progressSection.classList.add('hidden');
                    resultsSection.classList.remove('hidden');
                } else {
                    // Calculate progress (this is a simple approximation)
                    const progress = 50; // In a real app, you'd track progress better
                    updateProgress(progress);
                    setTimeout(pollResults, 2000);
                }
            })
            .catch(error => {
                showError(error.message);
                progressSection.classList.add('hidden');
            });
    }
    
    function updateProgress(percent) {
        progressBar.style.width = `${percent}%`;
        progressText.textContent = `${percent}%`;
    }
    
    function displayResults(results) {
        totalCombos.textContent = results.length;
        
        // Count valid combos (at least one hit)
        const validCount = results.filter(item => {
            return Object.values(item.results).some(status => status === 'Hit');
        }).length;
        
        validCombos.textContent = validCount;
        completionTime.textContent = new Date().toLocaleTimeString();
        
        // Clear previous results
        resultsBody.innerHTML = '';
        
        // Add new results (limit to 100 for performance)
        const displayResults = results.slice(0, 100);
        
        displayResults.forEach(item => {
            const row = document.createElement('tr');
            
            // Combo cell
            const comboCell = document.createElement('td');
            comboCell.textContent = item.combo;
            row.appendChild(comboCell);
            
            // Platform cells
            ['Netflix', 'Spotify', 'Discord'].forEach(platform => {
                const platformCell = document.createElement('td');
                const status = item.results[platform] || 'Bad';
                platformCell.textContent = status;
                platformCell.className = `status-${status.toLowerCase()}`;
                row.appendChild(platformCell);
            });
            
            resultsBody.appendChild(row);
        });
    }
    
    downloadButton.addEventListener('click', function() {
        if (!checkId) return;
        
        fetch(`${BACKEND_URL}/api/results/${checkId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Convert results to CSV
                const csvContent = convertToCSV(data.result);
                
                // Download file
                const blob = new Blob([csvContent], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `combo-results-${checkId}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            })
            .catch(error => {
                showError(error.message);
            });
    });
    
    function convertToCSV(results) {
        const headers = ['Combo', ...websites];
        const rows = results.map(item => {
            return [
                item.combo,
                ...websites.map(site => item.results[site] || 'Bad')
            ];
        });
        
        return [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n');
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        errorSection.classList.remove('hidden');
    }
});