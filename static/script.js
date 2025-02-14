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

    // Course search functionality
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');

    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const searchTerm = searchInput.value.trim();

        if (searchTerm) {
            searchResults.innerHTML = '<div class="text-center">Searching...</div>';

            fetch(`/api/courses?name=${encodeURIComponent(searchTerm)}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success' && data.data.length > 0) {
                        const resultsHtml = data.data.map(course => `
                            <div class="search-result-item">
                                <div class="course-title">
                                    <span class="course-code">${course.courseString}</span> - ${course.title}
                                </div>
                                <div class="course-details">
                                    Credits: ${course.credits}
                                    ${course.sections ? `<br>Sections: ${course.sections.length}` : ''}
                                </div>
                            </div>
                        `).join('');

                        searchResults.innerHTML = resultsHtml;
                    } else {
                        searchResults.innerHTML = '<div class="text-center">No courses found</div>';
                    }
                })
                .catch(error => {
                    console.error('Error searching courses:', error);
                    searchResults.innerHTML = '<div class="text-center text-danger">Error searching courses</div>';
                });
        }
    });

    // Example response
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