var selectionAnchorNode;

// similar to the color parts of `initializeReadingPreferences`,
// but also updates the toggle button icons, as the DOM is already loaded when this is called.
function activateColorScheme() {
    let theme;
    let current_theme = localStorage.getItem("ar5iv_theme") || "automatic";
    let colorSchemeToggle = document.querySelector('.color-tog');
    let autoIcon = document.querySelectorAll('.automatic-tog');
    let lightIcon = document.querySelectorAll('.light-tog');
    let darkIcon = document.querySelectorAll('.dark-tog');

    if (current_theme === "automatic") {
        if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
            theme = "dark";
        } else {
            theme = "light";
        }
        colorSchemeToggle.setAttribute('aria-label', 'System preference')
        autoIcon.forEach(x => x.style.display = 'block');
        lightIcon.forEach(x => x.style.display = 'none');
        darkIcon.forEach(x => x.style.display = 'none');
    } else if (current_theme === "light") {
        colorSchemeToggle.setAttribute('aria-label', 'Light mode')
        autoIcon.forEach(x => x.style.display = 'none');
        lightIcon.forEach(x => x.style.display = 'block');
        darkIcon.forEach(x => x.style.display = 'none');
        theme = "light";
    } else {
        colorSchemeToggle.setAttribute('aria-label', 'Dark mode')
        autoIcon.forEach(x => x.style.display = 'none');
        lightIcon.forEach(x => x.style.display = 'none');
        darkIcon.forEach(x => x.style.display = 'block');
        theme = "dark";
    }

    if (theme == "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
    } else {
        document.documentElement.setAttribute("data-theme", "light");
    }
}

function toggleColorScheme() {
    var current_theme = localStorage.getItem("ar5iv_theme");
    if (current_theme) {
        if (current_theme == "light") {
            localStorage.setItem("ar5iv_theme", "dark");
        } else if (current_theme == "dark") {
            localStorage.setItem("ar5iv_theme", "automatic");
        } else {
            localStorage.setItem("ar5iv_theme", "light");
        }
    } else {
        localStorage.setItem("ar5iv_theme", "light");
    }
    activateColorScheme();
}

// For toc, header and footer, we assume they are enabled by default (on large viewports).
// What is valuable is when users want to disable them, their preference can be sticky in that browser.
function toggleNavTOC() {
    const toc = document.querySelectorAll('.ltx_page_navbar>nav.ltx_TOC');
    if (toc.length > 0) {
        const style = window.getComputedStyle(toc[0]);
        let tocDisplay = (style.display === 'none') ? 'block' : 'none';
        document.documentElement.setAttribute("data-toc-display", tocDisplay);
        localStorage.setItem('arxiv_html_paper_toc_display', tocDisplay);
    }
}
function hideNavTOC() {
    const toc = document.querySelectorAll('.ltx_page_navbar>nav.ltx_TOC');
    if (toc.length > 0) {
        document.documentElement.setAttribute("data-toc-display", 'none');
        localStorage.setItem('arxiv_html_paper_toc_display', 'none');
    }
}

// in sync with our CSS @media breakpoints for ToC and header
// const narrowViewport = window.matchMedia("(max-width: 1279px)").matches;
// Toggles header and footer
function toggleReadingMode() {
    const header = document.querySelectorAll('.arxiv-html-header');
    const collapseIcon = document.getElementById('disable-reading-mode-btn');
    if (header.length > 0 && collapseIcon) {
        const style = window.getComputedStyle(header[0]);
        let readingMode = (style.display === 'none') ? 'disabled' : 'enabled';
        if (narrowViewport && readingMode === 'enabled') {
            // In narrow viewports, the header logically owns the ToC UI,
            // thus a header hide should also hide the ToC.
            hideNavTOC();
        }
        document.documentElement.setAttribute("data-reading-mode", readingMode);
        localStorage.setItem('arxiv_html_paper_reading_mode', readingMode);
    }
}

function showModalForm() {
    const modal = document.getElementById('modal-form');
    if (modal) {
        modal.showModal();
    } else {
        console.error('Modal element with id "modal-form" not found.');
    }
}

function hideModalForm() {
    const modal = document.getElementById('modal-form');
    if (modal) {
        modal.close();
    } else {
        console.error('Modal element with id "modal-form" not found.');
    }
}
