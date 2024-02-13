document.addEventListener("DOMContentLoaded", function() {
    var searchInput = document.querySelector('.search-input');

    searchInput.addEventListener('focus', function() {
        this.classList.add('expanded');
    });

    searchInput.addEventListener('blur', function() {
        this.classList.remove('expanded');
    });
});