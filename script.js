document.addEventListener('DOMContentLoaded', () => {
    const ctaButton = document.querySelector('.cta-button');

    if (ctaButton) {
        // Optional: Add a class or scroll effect on button click 
        // to make the interaction feel more polished, even if it just links out.
        ctaButton.addEventListener('click', (e) => {
            console.log("Redirecting user to live converter demo...");
            // No complex JS needed here as the link is handled by HTML 'target="_blank"' 
            // but this console log confirms the script is loaded and working.
        });
    }
});
