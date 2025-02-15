document.addEventListener('DOMContentLoaded', function() {
    const campusMap = {
        "1": "College Ave",
        "2": "Busch",
        "3": "Livingston", 
        "4": "Cook/Doug"
    };

    const weekdayMap = {
        "M": "Monday",
        "T": "Tuesday", 
        "W": "Wednesday",
        "H": "Thursday",
        "F": "Friday",
        "S": "Saturday",
        "Su": "Sunday"
    };

    // Helper function to format meeting times
    function formatMeetingTimes(meetingTimes) {
        return meetingTimes.map(meeting => `
            ${weekdayMap[meeting.day] || meeting.day}: ${meeting.start_time.formatted} - ${meeting.end_time.formatted}
            <br>Location: ${meeting.building} ${meeting.room}
            <br>Campus: ${campusMap[meeting.campus] || meeting.campus}
            <br>Mode: ${meeting.mode}
        `).join('<br><br>');
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
                        const resultsHtml = data.data.map((course, courseIndex) => `
                            <div class="search-result-item card mb-4">
                                <div class="card-header">
                                    <h4 class="mb-0">${course.courseString} - ${course.title}</h4>
                                </div>
                                <div class="card-body">
                                    <div class="row mb-3">
                                        <div class="col-md-6">
                                            <p><strong>Subject:</strong> ${course.subject} - ${course.subjectDescription}</p>
                                            <p><strong>Credits:</strong> ${course.credits} (${course.creditsDescription})</p>
                                            <p><strong>School:</strong> ${course.school}</p>
                                        </div>
                                        <div class="col-md-6">
                                            <p><strong>Campus Locations:</strong> ${course.campusLocations.join(', ')}</p>
                                            <p><strong>Prerequisites:</strong> ${course.prerequisites || 'None'}</p>
                                        </div>
                                    </div>

                                    <div class="mb-3">
                                        <h5>Core Requirements:</h5>
                                        <p>${formatCoreRequirements(course.coreRequirements)}</p>
                                    </div>

                                    <div class="sections">
                                        <button class="btn btn-primary mb-3" type="button" 
                                                data-bs-toggle="collapse" 
                                                data-bs-target="#sections-${courseIndex}" 
                                                aria-expanded="false" 
                                                aria-controls="sections-${courseIndex}">
                                            Show/Hide ${course.sections.length} Sections
                                        </button>
                                        <div class="collapse" id="sections-${courseIndex}">
                                            ${course.sections.map(section => `
                                                <div class="section-item card mb-3">
                                                    <div class="card-body">
                                                        <h6>Section ${section.number} (Index: ${section.index})</h6>
                                                        <p><strong>Instructors:</strong> ${section.instructors.join(', ') || 'TBA'}</p>
                                                        <p><strong>Status:</strong> ${section.status}</p>
                                                        ${section.comments ? `<p><strong>Comments:</strong> ${section.comments}</p>` : ''}
                                                        <div class="meeting-times">
                                                            <strong>Meeting Times:</strong><br>
                                                            ${formatMeetingTimes(section.meeting_times)}
                                                        </div>
                                                    </div>
                                                </div>
                                            `).join('')}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('');

                        searchResults.innerHTML = resultsHtml;
                    } else {
                        searchResults.innerHTML = '<div class="alert alert-info">No courses found</div>';
                    }
                })
                .catch(error => {
                    console.error('Error searching courses:', error);
                    searchResults.innerHTML = '<div class="alert alert-danger">Error searching courses</div>';
                });
        }
    });

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
});