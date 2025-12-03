document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const notesContainer = document.getElementById('notesContainer');
    const noteItems = document.querySelectorAll('.note-item');
    
    if (searchInput && searchBtn && notesContainer) {
        // Search functionality
        function performSearch() {
            const searchTerm = searchInput.value.toLowerCase();
            
            noteItems.forEach(item => {
                const title = item.getAttribute('data-title');
                const content = item.getAttribute('data-content');
                
                if (title.includes(searchTerm) || content.includes(searchTerm)) {
                    item.style.display = '';
                    
                    // Highlight search term
                    if (searchTerm.length > 0) {
                        const titleElement = item.querySelector('.note-title');
                        const contentElement = item.querySelector('.note-content');
                        
                        // Simple highlight (you might want to use a library for more robust highlighting)
                        const originalTitle = titleElement.textContent;
                        const originalContent = contentElement.textContent;
                        
                        // This is a simple implementation - in a real app you'd want more sophisticated highlighting
                        // For now, we'll just show the items that match
                    }
                } else {
                    item.style.display = 'none';
                }
            });
            
            // Show message if no results
            const visibleItems = Array.from(noteItems).filter(item => item.style.display !== 'none');
            let noResultsMsg = document.getElementById('noResultsMessage');
            
            if (visibleItems.length === 0 && searchTerm.length > 0) {
                if (!noResultsMsg) {
                    noResultsMsg = document.createElement('div');
                    noResultsMsg.id = 'noResultsMessage';
                    noResultsMsg.className = 'alert alert-info mt-3';
                    noResultsMsg.innerHTML = `<i class="fas fa-info-circle me-1"></i>No notes found matching "${searchTerm}"`;
                    notesContainer.parentNode.insertBefore(noResultsMsg, notesContainer.nextSibling);
                }
            } else if (noResultsMsg) {
                noResultsMsg.remove();
            }
        }
        
        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
    }
});