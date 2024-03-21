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

document.addEventListener('DOMContentLoaded', function() {
    var searchInput = document.querySelector('.search-input');
    var suggestionsList = document.getElementById('suggestions');

    searchInput.addEventListener('input', function() {
        var query = this.value;
        if(query.length > 1) {
            fetch(`/autocomplete?query=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    suggestionsList.innerHTML = ''; // Clear existing suggestions
                    data.forEach(function(item) {
                        var li = document.createElement('li');
                        li.textContent = item;
                        li.addEventListener('click', function() {
                            searchInput.value = item; // Fill input with clicked suggestion
                            suggestionsList.innerHTML = ''; // Clear suggestions
                        });
                        suggestionsList.appendChild(li);
                    });
                })
                .catch(error => console.error('Error fetching data:', error));
        } else {
            suggestionsList.innerHTML = '';  // Clear suggestions if input is too short
        }
    });
});