// Function to copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Show success feedback
        const activeButton = document.activeElement;
        if (activeButton && activeButton.classList.contains('copy-button')) {
            const originalHTML = activeButton.innerHTML;
            activeButton.innerHTML = '<i class="bi bi-check"></i>';
            activeButton.classList.add('copy-success');
            
            setTimeout(() => {
                activeButton.innerHTML = originalHTML;
                activeButton.classList.remove('copy-success');
            }, 1500);
        }
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

document.addEventListener("DOMContentLoaded", function () {
    // Initialize Bootstrap tooltips with HTML enabled
    function initializeTooltips() {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        tooltipTriggerList.forEach(tooltipEl => {
            new bootstrap.Tooltip(tooltipEl, {
                html: true  // ✅ Enables rendering of HTML inside tooltips
            });
        });
    }

    async function fetchSalaryData(instructorName, tooltipElement) {
        try {
            // Convert "LAST, FIRST" to "First Last"
            let nameParts = instructorName.split(", ");
            let formattedName = nameParts.length === 2 ? `${nameParts[1]} ${nameParts[0]}` : instructorName;

            console.log("🔍 Fetching salary for:", formattedName); // Debugging

            const response = await fetch(`/api/salary?name=${encodeURIComponent(formattedName)}`);
            const data = await response.json();
            console.log("📡 API Response:", data); // Debugging

            let tooltipInstance = bootstrap.Tooltip.getInstance(tooltipElement);
            if (!tooltipInstance) return;

            // ✅ Format tooltip content with proper layout while using setContent method
            if (data.error) {
                tooltipInstance.setContent({ '.tooltip-inner': "No salary data found" });
            } else {
                tooltipInstance.setContent({
                    '.tooltip-inner': `
                        <div style="text-align: left; max-width: 280px;">
                            <em>Special thanks to Github: ibrahimmudassar for the data</em><br><br>
                            <em>As of December, 2021</em><br><br>
                            <strong>${data.name}</strong><br><br>
                            <strong>Title:</strong> ${data.title}<br>
                            <strong>Department:</strong> ${data.department}<br>
                            <strong>Campus:</strong> ${data.campus}<br>
                            <strong>Base Pay:</strong> ${data.base_pay}<br>
                            <strong>Gross Pay:</strong> ${data.gross_pay}<br>
                            <strong>Hire Date:</strong> ${data.hire_date}
                        </div>
                    `
                });
            }

            console.log("✅ Tooltip updated successfully"); // Debugging
        } catch (error) {
            console.error("❌ Error fetching salary data:", error);

            let tooltipInstance = bootstrap.Tooltip.getInstance(tooltipElement);
            if (tooltipInstance) {
                tooltipInstance.setContent({ '.tooltip-inner': "Error loading salary data" });
            }
        }
    }

    // ✅ Add single event listener for instructor hover (fixes duplicate event issue)
    document.body.addEventListener("mouseover", function (event) {
        if (event.target.classList.contains("instructor-name")) {
            let instructorName = event.target.textContent.trim();
            let tooltipElement = event.target;

            fetchSalaryData(instructorName, tooltipElement);
        }
    });

    // ✅ Ensure tooltips initialize correctly after dynamic content loads
    initializeTooltips();

    // ================================
    // Course Search Functionality
    // ================================
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('search');
    const searchResults = document.getElementById('results');

    searchForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const searchTerm = searchInput.value.trim();
        
        // Get current URL parameters to maintain consistent year/term/campus values
        const urlParams = new URLSearchParams(window.location.search);
        const year = urlParams.get('year') || '2025';
        const term = urlParams.get('term') || '1';
        const campus = urlParams.get('campus') || 'NB';
        
        // Build the search query with all parameters
        const searchParams = new URLSearchParams({
            year: year,
            term: term,
            campus: campus,
            search: searchTerm
        });

        if (searchTerm) {
            searchResults.innerHTML = '<div class="text-center">Searching...</div>';

            fetch(`/api/courses?${searchParams.toString()}`)
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
                                            <p><strong>Credits:</strong> ${course.credits}</p>
                                            <p><strong>School:</strong> ${course.school}</p>
                                        </div>
                                        <div class="col-md-6">
                                            <p><strong>Campus Locations:</strong> ${course.campusLocations.join(', ')}</p>
                                            <p><strong>Prerequisites:</strong> ${course.prerequisites || 'None'}</p>
                                            <p><strong>Core Codes:</strong> ${Array.isArray(course.coreRequirements) && course.coreRequirements.length > 0 ? 
                                                course.coreRequirements.map(core => `${core.code} (${core.description})`).join(', ') : 'N/A'}</p>
                                        </div>
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
                                                        <p><strong>Instructors:</strong> 
                                                            ${section.instructors.map(instructor => 
                                                                `<span class="instructor-name" data-bs-toggle="tooltip" data-bs-placement="top" 
                                                                title="Loading salary data...">
                                                                ${instructor.trim()}</span>`
                                                            ).join(', ') || 'TBA'}
                                                        </p>
                                                        <p><strong>Status:</strong> <span class="${section.status.toLowerCase() === 'open' ? 'status-open' : 'status-closed'}">${section.status}</span></p>
                                                        <div class="meeting-times">
                                                            <strong>Meeting Times:</strong><br>
                                                            ${section.meeting_times.map(time => `
                                                                <p>
                                                                    ${time.day || 'TBA'} 
                                                                    ${time.start_time.formatted} - ${time.end_time.formatted}<br>
                                                                    Location: ${time.building} ${time.room}<br>
                                                                    Campus: ${time.campus}<br>
                                                                    Mode: ${time.mode}
                                                                </p>
                                                            `).join('')}
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
                        initializeTooltips();
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

    // ================================
    // API Health Status Checker
    // ================================
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

    updateStatus();
    setInterval(updateStatus, 30000);
});