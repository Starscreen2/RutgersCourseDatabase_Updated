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

    // Helper function to format meeting times
    function formatMeetingTimes(meetingTimes) {
        return meetingTimes.map(meeting => `
            ${meeting.day}: ${meeting.start_time.formatted} - ${meeting.end_time.formatted}
            <br>Location: ${meeting.building} ${meeting.room} (${meeting.mode})
        `).join('<br>');
    }

    // Helper function to format core requirements
    function formatCoreRequirements(requirements) {
        if (!requirements || requirements.length === 0) return 'None';
        return requirements.map(req => 
            `${req.code}: ${req.description}`
        ).join('<br>');
    }

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
                            <div class="search-result-item card mb-3">
                                <div class="card-header">
                                    <h4 class="course-title mb-0">
                                        <span class="course-code">${course.courseString}</span> - ${course.title}
                                    </h4>
                                </div>
                                <div class="card-body">
                                    <div class="row">
                                        <div class="col-md-6">
                                            <p><strong>Subject:</strong> ${course.subject}</p>
                                            <p><strong>Credits:</strong> ${course.credits}</p>
                                            <p><strong>School:</strong> ${course.school}</p>
                                            <p><strong>Campus:</strong> ${course.campusLocations.join(', ')}</p>
                                        </div>
                                        <div class="col-md-6">
                                            <p><strong>Prerequisites:</strong> ${course.prerequisites || 'None'}</p>
                                            <p><strong>Core Requirements:</strong><br>${formatCoreRequirements(course.coreRequirements)}</p>
                                        </div>
                                    </div>

                                    <div class="sections mt-3">
                                        <h5>Sections:</h5>
                                        ${course.sections.map(section => `
                                            <div class="section-item card mb-2">
                                                <div class="card-body">
                                                    <h6>Section ${section.number}</h6>
                                                    <p><strong>Instructors:</strong> ${section.instructors.join(', ') || 'TBA'}</p>
                                                    <p><strong>Status:</strong> ${section.status}</p>
                                                    ${section.comments ? `<p><strong>Comments:</strong> ${section.comments}</p>` : ''}
                                                    <p><strong>Meeting Times:</strong><br>${formatMeetingTimes(section.meeting_times)}</p>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
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