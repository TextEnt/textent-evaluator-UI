document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Export results button
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            // Show loading state
            exportBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Exporting...';
            exportBtn.disabled = true;

            // Call the export endpoint
            fetch('/export')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Create download link and trigger it
                        const link = document.createElement('a');
                        link.href = data.download_url;
                        link.download = data.filename;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        
                        // Show success message
                        showAlert('Results exported successfully!', 'success');
                    } else {
                        showAlert(`Export failed: ${data.message}`, 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error exporting results:', error);
                    showAlert('An error occurred during export.', 'danger');
                })
                .finally(() => {
                    // Reset button state
                    exportBtn.innerHTML = 'Export Results';
                    exportBtn.disabled = false;
                });
        });
    }

    // Handle search form submission
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(searchForm);
            
            fetch('/search', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show results in a dropdown
                    const resultsDropdown = document.getElementById('searchResults');
                    resultsDropdown.innerHTML = '';
                    
                    data.results.forEach(result => {
                        const resultItem = document.createElement('button');
                        resultItem.className = 'dropdown-item';
                        resultItem.textContent = `${result.author} - ${result.title} (${result.publication_date})`;
                        resultItem.addEventListener('click', function() {
                            window.location.href = `/assessment?id=${result.id}`;
                        });
                        
                        resultsDropdown.appendChild(resultItem);
                    });
                    
                    // Show the dropdown
                    document.getElementById('searchResultsContainer').classList.remove('d-none');
                } else {
                    showAlert(data.message, 'warning');
                    document.getElementById('searchResultsContainer').classList.add('d-none');
                }
            })
            .catch(error => {
                console.error('Error searching:', error);
                showAlert('An error occurred during search.', 'danger');
            });
        });
    }

    // Navigation buttons
    const prevBtn = document.querySelector('.btn-prev');
    const nextBtn = document.querySelector('.btn-next');
    
    if (prevBtn && nextBtn) {
        // Get the file ID from the URL
        const fileId = window.location.pathname.split('/').pop();
        
        // Get current file ID and response ID from URL or data attributes
        if (fileId && (prevBtn || nextBtn)) {
            // The navigation is primarily handled by the code in main.js
            // which submits the form with a hidden input
            console.log('Navigation is handled by main.js');
        }
    }

    // Helper function to show alerts
    function showAlert(message, type) {
        const alertContainer = document.getElementById('alertContainer');
        if (alertContainer) {
            const alert = document.createElement('div');
            alert.className = `alert alert-${type} alert-dismissible fade show`;
            alert.innerHTML = `
                ${message}
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

    // Update statistics periodically
    function updateStatistics() {
        const statsContainer = document.getElementById('statsContainer');
        if (statsContainer) {
            fetch('/statistics')
                .then(response => response.json())
                .then(data => {
                    // Update progress bar
                    const progressBar = document.getElementById('progressBar');
                    if (progressBar) {
                        progressBar.style.width = `${data.progress.percentage}%`;
                        progressBar.setAttribute('aria-valuenow', data.progress.percentage);
                        document.getElementById('progressText').textContent = 
                            `${data.progress.assessed} / ${data.progress.total} responses (${Math.round(data.progress.percentage)}%)`;
                    }
                    
                    // Update average scores
                    const avgTimeScore = document.getElementById('avgTimeScore');
                    const avgSpaceScore = document.getElementById('avgSpaceScore');
                    
                    if (avgTimeScore && avgSpaceScore) {
                        avgTimeScore.textContent = data.avg_scores.time;
                        avgSpaceScore.textContent = data.avg_scores.space;
                    }
                })
                .catch(error => {
                    console.error('Error updating statistics:', error);
                });
        }
    }
    
    // Update statistics on page load and every 30 seconds
    updateStatistics();
    setInterval(updateStatistics, 30000);
});
