async function testEndpoint(endpoint) {
    try {
        const response = await fetch(endpoint);
        const data = await response.json();
        
        // Format the JSON response
        const formattedJson = JSON.stringify(data, null, 2);
        
        // Find the closest example-response element
        const responseElement = document.querySelector('#example-response');
        if (responseElement) {
            responseElement.textContent = formattedJson;
            Prism.highlightElement(responseElement);
        }
    } catch (error) {
        console.error('Error testing endpoint:', error);
        alert('Error testing endpoint. Check console for details.');
    }
}

// Initialize syntax highlighting
document.addEventListener('DOMContentLoaded', () => {
    Prism.highlightAll();
});
