document.addEventListener('DOMContentLoaded', function() {
    // Check API health status
    function updateStatus() {
        fetch('/api/health')
            .then(response => response.json())
            .then(data => {
                const statusText = document.getElementById('statusText');
                const date = new Date(data.last_update);
                const formattedDate = date.toLocaleString();
                
                if (data.status === 'healthy') {
                    statusText.innerHTML = `
                        <span class="status-healthy">●</span> API is healthy<br>
                        Last updated: ${formattedDate}
                    `;
                } else {
                    statusText.innerHTML = `
                        <span class="status-error">●</span> API is experiencing issues
                    `;
                }
            })
            .catch(error => {
                const statusText = document.getElementById('statusText');
                statusText.innerHTML = `
                    <span class="status-error">●</span> Unable to connect to API
                `;
                console.error('Error fetching API status:', error);
            });
    }

    // Update status every 30 seconds
    updateStatus();
    setInterval(updateStatus, 30000);

    // Fetch example course data
    fetch('/api/courses?subject=CS&course_number=111')
        .then(response => response.json())
        .then(data => {
            const exampleResponse = document.getElementById('exampleResponse');
            exampleResponse.textContent = JSON.stringify(data, null, 4);
            Prism.highlightElement(exampleResponse);
        })
        .catch(error => {
            console.error('Error fetching example data:', error);
        });
});
