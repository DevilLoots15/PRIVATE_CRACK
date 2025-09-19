document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
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
    
    // Backend URL - Updated
    const BACKEND_URL = 'https://private-crack.onrender.com';
    
    // List of all platforms to check
    const platforms = [
        "Plex", "Steam", "GitHub", "Origin", "BattleNet", "Roblox",
        "Discord", "Reddit", "Spotify", "Trello", "Netflix"
    ];
    
    let checkId = null;
    let combos = [];
    
    console.log('Combo Checker Frontend Loaded');
    console.log('Backend URL:', BACKEND_URL);
    
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            fileName.textContent = file.name;
            checkButton.disabled = false;
        } else {
            fileName.textContent = 'No file chosen';
            checkButton.disabled = true;
        }
    });
    
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            showError('Please select a file first');
            return;
        }
        
        // Hide previous results and errors
        resultsSection.classList.add('hidden');
        errorSection.classList.add('hidden');
        
        // Show progress
        progressSection.classList.remove('hidden');
        updateProgress(0);
        
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('file', file);
        
        // Send request to backend
        fetch(`${BACKEND_URL}/api/check`, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            checkId = data.check_id;
            console.log('Check started with ID:', checkId);
            pollResults();
        })
        .catch(error => {
            handleApiError(error, 'file upload');
            progressSection.classList.add('hidden');
        });
    });
    
    function pollResults() {
        if (!checkId) return;
        
        console.log('Polling results for ID:', checkId);
        
        fetch(`${BACKEND_URL}/api/results/${checkId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                if (data.status === 'completed') {
                    console.log('Check completed successfully');
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
                handleApiError(error, 'polling results');
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
            platforms.forEach(platform => {
                const platformCell = document.createElement('td');
                const status = item.results[platform] || 'Bad';
                platformCell.textContent = status;
                platformCell.className = `status-${status.toLowerCase()}`;
                row.appendChild(platformCell);
            });
            
            resultsBody.appendChild(row);
        });
        
        console.log('Displayed results for', results.length, 'combos');
    }
    
    downloadButton.addEventListener('click', function() {
        if (!checkId) {
            showError('No results to download. Please check combos first.');
            return;
        }
        
        console.log('Downloading results for ID:', checkId);
        
        fetch(`${BACKEND_URL}/api/results/${checkId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
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
                
                console.log('Download completed');
            })
            .catch(error => {
                handleApiError(error, 'downloading results');
            });
    });
    
    function convertToCSV(results) {
        const headers = ['Combo', ...platforms];
        const rows = results.map(item => {
            return [
                `"${item.combo}"`,  // Wrap in quotes to handle commas in combos
                ...platforms.map(site => item.results[site] || 'Bad')
            ];
        });
        
        return [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n');
    }
    
    function handleApiError(error, context) {
        console.error(`Error in ${context}:`, error);
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            showError('Cannot connect to the server. Please check if the backend is running at: ' + BACKEND_URL);
        } else if (error.message.includes('404')) {
            showError('Server endpoint not found. Please check the backend API.');
        } else if (error.message.includes('500')) {
            showError('Server error. Please try again later.');
        } else {
            showError(error.message);
        }
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        errorSection.classList.remove('hidden');
        console.error('Error:', message);
    }
    
    // Test backend connection on load
    console.log('Testing backend connection...');
    fetch(`${BACKEND_URL}/api/status`)
        .then(response => {
            if (response.ok) {
                console.log('✓ Backend connection successful');
            } else {
                console.warn('⚠ Backend returned status:', response.status);
            }
        })
        .catch(error => {
            console.error('✗ Backend connection failed:', error.message);
        });
});