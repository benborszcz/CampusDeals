var checkList = document.getElementById('list1');
checkList.getElementsByClassName('anchor')[0].onclick = function(evt) {
    if (checkList.classList.contains('visible'))
        checkList.classList.remove('visible');
    else
        checkList.classList.add('visible');
}

function requestLocation() {
    if (document.getElementById('distance-select').value !== "" && navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            // Populate hidden form fields
            document.getElementById('userLat').value = position.coords.latitude;
            document.getElementById('userLon').value = position.coords.longitude;
        }, function(error) {
            alert('Unable to retrieve your location. Please check your settings and try again.');
        });
    }
}