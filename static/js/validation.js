document.addEventListener('DOMContentLoaded', function() {
    // Score input validation
    const timeScoreInput = document.getElementById('time_score');
    const spaceScoreInput = document.getElementById('space_score');
    
    if (timeScoreInput && spaceScoreInput) {
        // Function to validate score input (0-1 range)
        function validateScoreInput(input) {
            const value = parseFloat(input.value);
            const isValid = !isNaN(value) && value >= 0 && value <= 1;
            
            if (isValid) {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
                return true;
            } else {
                input.classList.remove('is-valid');
                input.classList.add('is-invalid');
                return false;
            }
        }
        
        // Add event listeners for input validation
        timeScoreInput.addEventListener('input', function() {
            validateScoreInput(timeScoreInput);
        });
        
        spaceScoreInput.addEventListener('input', function() {
            validateScoreInput(spaceScoreInput);
        });
        
        // Validate form on submission
        const assessmentForm = document.getElementById('assessmentForm');
        if (assessmentForm) {
            assessmentForm.addEventListener('submit', function(e) {
                const timeValid = validateScoreInput(timeScoreInput);
                const spaceValid = validateScoreInput(spaceScoreInput);
                
                if (!timeValid || !spaceValid) {
                    e.preventDefault();
                    
                    // Show error message
                    const alertContainer = document.getElementById('alertContainer');
                    if (alertContainer) {
                        const alert = document.createElement('div');
                        alert.className = 'alert alert-danger alert-dismissible fade show';
                        alert.innerHTML = `
                            Please enter valid scores (between 0 and 1).
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        `;
                        
                        alertContainer.appendChild(alert);
                        
                        // Auto-dismiss after 5 seconds
                        setTimeout(() => {
                            alert.classList.remove('show');
                            setTimeout(() => {
                                alertContainer.removeChild(alert);
                            }, 150);
                        }, 5000);
                    }
                }
            });
        }
    }
    
    // CSV file validation
    const csvFileInput = document.getElementById('csv_file');
    const uploadForm = document.getElementById('uploadForm');
    
    if (csvFileInput && uploadForm) {
        csvFileInput.addEventListener('change', function() {
            const file = csvFileInput.files[0];
            
            if (file) {
                // Check file extension
                const fileName = file.name;
                const fileExt = fileName.split('.').pop().toLowerCase();
                
                if (fileExt !== 'csv') {
                    // Show error message
                    csvFileInput.classList.add('is-invalid');
                    document.getElementById('csvFileError').textContent = 'Please upload a CSV file.';
                } else {
                    csvFileInput.classList.remove('is-invalid');
                    csvFileInput.classList.add('is-valid');
                }
            }
        });
        
        uploadForm.addEventListener('submit', function(e) {
            const file = csvFileInput.files[0];
            
            if (!file) {
                e.preventDefault();
                csvFileInput.classList.add('is-invalid');
                document.getElementById('csvFileError').textContent = 'Please select a file to upload.';
            } else {
                const fileName = file.name;
                const fileExt = fileName.split('.').pop().toLowerCase();
                
                if (fileExt !== 'csv') {
                    e.preventDefault();
                    csvFileInput.classList.add('is-invalid');
                    document.getElementById('csvFileError').textContent = 'Please upload a CSV file.';
                }
            }
        });
    }
});
