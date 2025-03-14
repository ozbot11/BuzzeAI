document.addEventListener('DOMContentLoaded', function() {
    const posterForm = document.getElementById('posterForm');
    const posterResult = document.getElementById('posterResult');
    const posterContent = document.getElementById('posterContent');

    posterForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        try {
            const formData = {
                club_name: document.getElementById('clubName').value,
                event_details: document.getElementById('eventDetails').value,
                style: document.getElementById('style').value,
                club_id: 1  // Default club ID for testing
            };

            const response = await fetch('/generate_poster', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            posterContent.innerHTML = `
                <div class="generated-poster">
                    ${data.poster.image_url ? 
                        `<img src="${data.poster.image_url}" alt="Generated Poster">` : 
                        ''}
                    <div class="poster-text">${data.poster.content || data.poster}</div>
                </div>
            `;
            
            posterResult.style.display = 'block';
        } catch (error) {
            console.error('Error:', error);
            alert('Error generating poster. Please try again.');
        }
    });
});