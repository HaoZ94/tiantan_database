// Wait for the document to be fully loaded before running script
document.addEventListener('DOMContentLoaded', () => {
    
    // --- THEME SWITCHER LOGIC ---
    const themeToggle = document.getElementById('checkbox');
    const body = document.body;

    // Function to apply the stored theme on load
    const applyStoredTheme = () => {
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme === 'dark') {
            body.classList.add('dark-theme');
            themeToggle.checked = true;
        } else {
            body.classList.remove('dark-theme');
            themeToggle.checked = false;
        }
    };

    // Event listener for the theme toggle
    themeToggle.addEventListener('change', () => {
        if (themeToggle.checked) {
            body.classList.add('dark-theme');
            localStorage.setItem('theme', 'dark');
        } else {
            body.classList.remove('dark-theme');
            localStorage.setItem('theme', 'light');
        }
    });

    // Apply the theme when the page loads
    applyStoredTheme();

    // --- LANGUAGE DROPDOWN LOGIC (NEW) ---
    const langButton = document.querySelector('.language-btn');
    const langDropdown = document.querySelector('.language-dropdown');

    // Toggle dropdown visibility when the button is clicked
    langButton.addEventListener('click', (event) => {
        // Stop the click from closing the menu immediately
        event.stopPropagation(); 
        langDropdown.classList.toggle('show');
    });

    // Close the dropdown if the user clicks outside of it
    window.addEventListener('click', (event) => {
        if (!langButton.contains(event.target)) {
            if (langDropdown.classList.contains('show')) {
                langDropdown.classList.remove('show');
            }
        }
    });
});
