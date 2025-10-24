// Wait for the document to be fully loaded before running script
document.addEventListener('DOMContentLoaded', () => {
    
    // --- THEME SWITCHER LOGIC ---
    // ... no changes here ...
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
    // ... no changes here ...
    const langButton = document.querySelector('.language-btn');
    const langDropdown = document.querySelector('.language-dropdown');

    // Toggle dropdown visibility when the button is clicked
    if (langButton) { // Add check to ensure button exists
        langButton.addEventListener('click', (event) => {
            // Stop the click from closing the menu immediately
            event.stopPropagation(); 
            if(langDropdown) langDropdown.classList.toggle('show');
        });
    }

    // Close the dropdown if the user clicks outside of it
    window.addEventListener('click', (event) => {
        if (langButton && !langButton.contains(event.target)) {
            if (langDropdown && langDropdown.classList.contains('show')) {
                langDropdown.classList.remove('show');
            }
        }
    });

    // --- TEAM PAGE LOGIC ---
    // Check if we are on the team page by looking for a unique container
    if (document.getElementById('team-page-content')) {
        
        // --- 1. ROW FADE-IN ANIMATION LOGIC ---
        // ... no changes here ...
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

        // --- 2. NEW: TEAM MEMBER DETAIL VIEW LOGIC (MODIFIED) ---
        
        // Select all the clickable member cards
        const memberCards = document.querySelectorAll('.team-member-card');
        
        // Select the overlay and its parts
        const detailOverlay = document.getElementById('member-detail-overlay');
        const detailCard = document.getElementById('member-detail-card');
        const closeBtn = document.getElementById('detail-close-btn');
        
        // Select the content elements to populate
        const detailImg = document.getElementById('detail-img');
        const detailName = document.getElementById('detail-name');
        const detailTitle = document.getElementById('detail-title');
        const detailBio = document.getElementById('detail-bio');
        // NEW: Select honors elements
        const detailHonorsWrapper = document.getElementById('detail-honors-wrapper');
        const detailHonors = document.getElementById('detail-honors');
        
        // Add click listener to each card
        memberCards.forEach(card => {
            card.addEventListener('click', () => {
                // Get data from the clicked card's data attributes
                const name = card.dataset.name;
                const title = card.dataset.title;
                const bio = card.dataset.bio;
                const honors = card.dataset.honors; // NEW: Get honors data
                const imgSrc = card.querySelector('.team-member-img').src;
                
                // Populate the detail card
                if (detailName) detailName.textContent = name;
                if (detailTitle) detailTitle.textContent = title;
                
                // MODIFICATION: Use .innerHTML to render HTML tags like <br>
                if (detailBio) detailBio.innerHTML = bio; 
                
                if (detailImg) {
                    detailImg.src = imgSrc;
                    detailImg.alt = `Profile image of ${name}`;
                }

                // NEW: Populate honors, or hide the section if no honors data exists
                if (detailHonors && detailHonorsWrapper) {
                    if (honors) {
                        detailHonors.innerHTML = honors;
                        detailHonorsWrapper.style.display = 'block';
                    } else {
                        detailHonors.innerHTML = '';
                        detailHonorsWrapper.style.display = 'none';
                    }
                }
                
                // Show the overlay by adding class to body
                document.body.classList.add('detail-view-active');
            });
        });

        // Function to close the detail view
        const closeDetailView = () => {
            document.body.classList.remove('detail-view-active');
        };

        // Add click listener to the close button
        if(closeBtn) closeBtn.addEventListener('click', closeDetailView);

        // Add click listener to the overlay background (to close)
        if(detailOverlay) {
            detailOverlay.addEventListener('click', (event) => {
                // Check if the click is on the overlay itself, not the card
                if (event.target === detailOverlay) {
                    closeDetailView();
                }
            });
        }
    }
});