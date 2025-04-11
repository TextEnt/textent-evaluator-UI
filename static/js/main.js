document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Validation for assessment form inputs
    const scoreInputs = document.querySelectorAll('input[type="number"]');
    scoreInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (isNaN(value) || value < 0 || value > 1) {
                this.classList.add('is-invalid');
                this.nextElementSibling.textContent = 'Score must be between 0 and 1';
            } else {
                this.classList.remove('is-invalid');
                this.classList.add('is-valid');
                this.nextElementSibling.textContent = '';
            }
        });
    });

    // Handle keyboard shortcuts for navigation
    document.addEventListener('keydown', function(e) {
        // Skip if user is typing in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        const nextButton = document.querySelector('.btn-next');
        
        // Right arrow key for next
        if (e.key === 'ArrowRight' && nextButton) {
            e.preventDefault();
            nextButton.click();
        }
    });

    // Auto-submit form when navigating with next button
    const navButtons = document.querySelectorAll('.btn-next');
    console.log('Navigation buttons found:', navButtons.length);
    
    navButtons.forEach(button => {
        console.log('Nav button:', button, 'Data response ID:', button.dataset.responseId);
        
        button.addEventListener('click', function(e) {
            console.log('Button clicked:', this, 'Data response ID:', this.dataset.responseId);
            e.preventDefault();
            
            const form = document.getElementById('assessment-form');
            console.log('Form found:', form);
            
            if (form) {
                // Update the existing hidden input with the response ID
                const nextResponseInput = document.getElementById('next_response_input');
                if (nextResponseInput) {
                    nextResponseInput.value = this.dataset.responseId;
                    console.log('Updated hidden input with value:', nextResponseInput.value);
                    
                    // Submit the form by programmatically clicking the submit button
                    console.log('Submitting form by clicking submit button...');
                    const submitButton = form.querySelector('input[type="submit"]');
                    if (submitButton) {
                        submitButton.click();
                    } else {
                        console.error('Submit button not found!');
                    }
                } else {
                    console.error('Hidden input for next_response not found!');
                }
            } else {
                console.error('Form not found!');
            }
        });
    });

    // Focus on first empty score input when page loads
    const emptyInputs = Array.from(scoreInputs).filter(input => !input.value);
    if (emptyInputs.length > 0) {
        emptyInputs[0].focus();
    }

    // Search functionality
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = document.querySelector('input[name="query"]');
            if (!searchInput.value.trim()) {
                e.preventDefault();
                alert('Please enter a search query');
            }
        });
    }

    // Display confirmation before deleting
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
});
