document.addEventListener('DOMContentLoaded', function() {
    // Handle search input
    const searchInput = document.getElementById('query');
    const searchForm = document.getElementById('searchForm');
    const searchResultsContainer = document.getElementById('searchResultsContainer');
    const searchResults = document.getElementById('searchResults');
    
    if (searchInput && searchForm && searchResultsContainer && searchResults) {
        // Clear results when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchForm.contains(e.target) && !searchResultsContainer.contains(e.target)) {
                searchResultsContainer.classList.add('d-none');
            }
        });
        
        // Show results container when focusing on search input
        searchInput.addEventListener('focus', function() {
            if (searchResults.children.length > 0) {
                searchResultsContainer.classList.remove('d-none');
            }
        });
        
        // Handle key navigation in search results
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                
                if (searchResults.children.length > 0) {
                    searchResults.children[0].focus();
                }
            }
        });
        
        // Add keyboard navigation for search results
        searchResults.addEventListener('keydown', function(e) {
            const items = Array.from(searchResults.children);
            const currentIndex = items.indexOf(document.activeElement);
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (currentIndex < items.length - 1) {
                    items[currentIndex + 1].focus();
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (currentIndex > 0) {
                    items[currentIndex - 1].focus();
                } else {
                    searchInput.focus();
                }
            } else if (e.key === 'Escape') {
                e.preventDefault();
                searchResultsContainer.classList.add('d-none');
                searchInput.focus();
            }
        });
    }
});
