function loadContent(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll('section');
    sections.forEach(section => {
        section.classList.remove('active');
        section.classList.add('inactive');
    });

    // Show selected section
    const selectedSection = document.getElementById(sectionId);
    selectedSection.classList.remove('inactive');
    selectedSection.classList.add('active');
}