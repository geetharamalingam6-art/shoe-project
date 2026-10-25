/**
 * StepUp.in - Shoe E-Commerce Interactive Script
 * - Hero carousel slider with 4 indicators & auto-rotation
 * - Search handling
 * - Mobile responsive navigation
 * - Mega menu dropdown auto-hide (4-6 seconds)
 * - Interactive cart & notifications
 */

document.addEventListener('DOMContentLoaded', function () {
    // ----------------------------------------------------
    // 1. HERO BANNER SLIDER
    // ----------------------------------------------------
    const slides = document.querySelectorAll('.hero-slide');
    const indicatorDots = document.querySelectorAll('.slider-indicator-dot');
    const prevBtn = document.querySelector('.slider-arrow-prev');
    const nextBtn = document.querySelector('.slider-arrow-next');
    const heroContainer = document.querySelector('.hero-banner-container');

    let currentSlide = 0;
    const totalSlides = slides.length;
    let slideInterval = null;

    function goToSlide(index) {
        if (!slides.length) return;

        // Wrap around
        if (index >= totalSlides) {
            currentSlide = 0;
        } else if (index < 0) {
            currentSlide = totalSlides - 1;
        } else {
            currentSlide = index;
        }

        // Update slides
        slides.forEach((slide, i) => {
            if (i === currentSlide) {
                slide.classList.add('active');
            } else {
                slide.classList.remove('active');
            }
        });

        // Update dots
        indicatorDots.forEach((dot, i) => {
            if (i === currentSlide) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }

    function nextSlide() {
        goToSlide(currentSlide + 1);
    }

    function prevSlide() {
        goToSlide(currentSlide - 1);
    }

    function startAutoSlide() {
        if (slideInterval) clearInterval(slideInterval);
        slideInterval = setInterval(nextSlide, 5000);
    }

    function stopAutoSlide() {
        if (slideInterval) clearInterval(slideInterval);
    }

    if (totalSlides > 0) {
        // Dot clicks
        indicatorDots.forEach((dot) => {
            dot.addEventListener('click', function () {
                const targetSlide = parseInt(this.getAttribute('data-slide-to'), 10);
                goToSlide(targetSlide);
                startAutoSlide(); // Reset timer on manual action
            });
        });

        // Arrow clicks
        if (nextBtn) {
            nextBtn.addEventListener('click', function (e) {
                e.preventDefault();
                nextSlide();
                startAutoSlide();
            });
        }

        if (prevBtn) {
            prevBtn.addEventListener('click', function (e) {
                e.preventDefault();
                prevSlide();
                startAutoSlide();
            });
        }

        // Pause on mouse hover
        if (heroContainer) {
            heroContainer.addEventListener('mouseenter', stopAutoSlide);
            heroContainer.addEventListener('mouseleave', startAutoSlide);
        }

        // Start auto slide
        startAutoSlide();
    }

    // ----------------------------------------------------
    // 2. SEARCH INPUT HANDLING
    // ----------------------------------------------------
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                const query = this.value.trim();
                if (query.length > 0) {
                    window.location.href = `/search/?q=${encodeURIComponent(query)}`;
                }
            }
        });
    }

    // ----------------------------------------------------
    // 3. MOBILE MENU TOGGLE
    // ----------------------------------------------------
    const mobileToggle = document.getElementById('mobile-toggle');
    const navLinks = document.getElementById('header-nav-links');

    if (mobileToggle && navLinks) {
        mobileToggle.addEventListener('click', function () {
            navLinks.classList.toggle('show-mobile');
        });
    }

    // ----------------------------------------------------
    // 4. MEGA MENU DROPDOWN AUTO-HIDE & INTERACTION
    // ----------------------------------------------------
    const navItems = document.querySelectorAll('.category-nav-list > li');
    navItems.forEach(item => {
        let hideTimer = null;
        const dropdown = item.querySelector('.mega-menu-dropdown');
        if (!dropdown) return;

        function showMenu() {
            clearTimeout(hideTimer);
            document.querySelectorAll('.mega-menu-dropdown').forEach(d => {
                if (d !== dropdown) {
                    d.style.display = 'none';
                    d.classList.remove('is-visible');
                }
            });
            dropdown.style.display = 'grid';
            dropdown.classList.add('is-visible');

            // Auto hide after 5 seconds of inactivity (within 4-6s window)
            hideTimer = setTimeout(() => {
                dropdown.style.display = 'none';
                dropdown.classList.remove('is-visible');
            }, 5000);
        }

        function hideMenu(delay = 300) {
            clearTimeout(hideTimer);
            hideTimer = setTimeout(() => {
                dropdown.style.display = 'none';
                dropdown.classList.remove('is-visible');
            }, delay);
        }

        item.addEventListener('mouseenter', showMenu);
        item.addEventListener('mouseleave', () => hideMenu(300));

        // Keep dropdown open while mouse is inside dropdown panel
        dropdown.addEventListener('mouseenter', () => {
            clearTimeout(hideTimer);
        });

        dropdown.addEventListener('mouseleave', () => {
            hideMenu(300);
        });
    });
});
