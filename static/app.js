const menuButton = document.querySelector('.menu-button');
const sidebar = document.querySelector('.sidebar');

if (menuButton && sidebar) {
    menuButton.addEventListener('click', () => sidebar.classList.toggle('open'));
    document.addEventListener('click', (event) => {
        if (window.innerWidth <= 760 && !sidebar.contains(event.target) && !menuButton.contains(event.target)) {
            sidebar.classList.remove('open');
        }
    });
}

// Success/error messages disappear after four seconds.
document.querySelectorAll('.alert').forEach((alert) => {
    setTimeout(() => alert.remove(), 4000);
});
