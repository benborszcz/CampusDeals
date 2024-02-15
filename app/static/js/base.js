document.addEventListener("DOMContentLoaded", function() {
    var searchInput = document.querySelector('.search-input');

    searchInput.addEventListener('focus', function() {
        this.classList.add('expanded');
    });

    searchInput.addEventListener('blur', function() {
        this.classList.remove('expanded');
    });
});

var checkList = document.getElementById('list1');
checkList.getElementsByClassName('anchor')[0].onclick = function(evt) {
    if (checkList.classList.contains('visible'))
        checkList.classList.remove('visible');
    else
        checkList.classList.add('visible');
}