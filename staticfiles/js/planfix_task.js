document.addEventListener('DOMContentLoaded', function() {
    // Cache refresh functionality
    const refreshButton = document.getElementById('refresh-button');
    if (refreshButton && refreshButton.dataset.refreshCache === 'true') {
        refreshButton.addEventListener('click', async function() {
            try {
                // Show loading state
                refreshButton.disabled = true;
                refreshButton.style.opacity = '0.7';
                
                // Call the cache refresh endpoint
                const response = await fetch('/chat/api/agent/refresh-cache/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!response.ok) {
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        const data = await response.json();
                        throw new Error(data.message || 'Failed to refresh cache');
                    } else {
                        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                    }
                }
                
                // Reload the page to show updated data
                window.location.reload();
                
            } catch (error) {
                console.error('Error refreshing cache:', error);
                alert(`Failed to refresh cache: ${error.message}`);
            } finally {
                // Reset button state
                refreshButton.disabled = false;
                refreshButton.style.opacity = '1';
            }
        });
    }
}); 