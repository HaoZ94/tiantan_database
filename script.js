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

    // --- TEAM PAGE ANIMATION LOGIC (NEW) ---
    // Check if we are on the team page by looking for a unique container
    if (document.getElementById('team-page-content')) {
        
        // Select all the rows that need to be animated
        const teamRows = document.querySelectorAll('.team-grid-row');

        const observerOptions = {
            root: null, // observes intersections relative to the viewport
            rootMargin: '0px',
            threshold: 0.1 // Triggers when 10% of the row is visible
        };

        const observerCallback = (entries, observer) => {
            entries.forEach(entry => {
                // When a row is intersecting (visible)
                if (entry.isIntersecting) {
                    // Add the 'visible' class to trigger the CSS transition
                    entry.target.classList.add('visible');
                    // Stop observing this row so the animation doesn't re-run
                    observer.unobserve(entry.target);
                }
            });
        };

        // Create the Intersection Observer
        const rowObserver = new IntersectionObserver(observerCallback, observerOptions);

        // Loop over each row to observe it and add a staggered delay
        teamRows.forEach((row, index) => {
            // Calculate the delay: 0ms, 200ms, 400ms, etc.
            const delay = index * 200; 
            // Apply the delay as an inline style
            row.style.transitionDelay = `${delay}ms`;
            
            // Start observing the row
            rowObserver.observe(row);
        });
    }
});