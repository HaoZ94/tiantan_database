// Wait for the document to be fully loaded before running script
document.addEventListener('DOMContentLoaded', () => {
    
    // Get the checkbox input
    const themeToggle = document.getElementById('checkbox');
    const body = document.body;

    // Function to apply the stored theme on load
    const applyStoredTheme = () => {
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme === 'dark') {
            body.classList.add('dark-theme');
            themeToggle.checked = true; // Set the toggle to the 'on' position
        } else {
            body.classList.remove('dark-theme');
            themeToggle.checked = false; // Set the toggle to the 'off' position
        }
    };

    // Event listener for the theme toggle (checkbox)
    themeToggle.addEventListener('change', () => {
        // Check if the checkbox is checked
        if (themeToggle.checked) {
            // It's checked, apply dark theme
            body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
        } else {
            // It's not checked, apply light theme
            body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
        }
    });

    // Apply the theme when the page loads
    applyStoredTheme();
});