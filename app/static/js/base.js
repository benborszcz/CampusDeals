window.locationEnabled = false;

document.addEventListener("DOMContentLoaded", function() {
    var searchInput = document.querySelector('.search-input');

    searchInput.addEventListener('focus', function() {
        this.classList.add('expanded');
    });

    searchInput.addEventListener('blur', function() {
        this.classList.remove('expanded');
    });

    window.locationEnabled = localStorage.getItem('locationEnabled') === 'true';
    console.log('localStorage locationEnabled = ' + localStorage.getItem('locationEnabled'));
    setLocation(window.locationEnabled);
    if (window.updateDistanceInputState) {
        window.updateDistanceInputState(window.locationEnabled);
    }
});

var checkList = document.getElementById('list1');
checkList.getElementsByClassName('anchor')[0].onclick = function(evt) {
    if (checkList.classList.contains('visible'))
        checkList.classList.remove('visible');
    else
        checkList.classList.add('visible');
}

function toggleLocation() {
    if (!window.locationEnabled) {
        window.locationEnabled = true;
        setLocation(true);
        localStorage.setItem('locationEnabled', true);
    } else {
        window.locationEnabled = false;
        setLocation(false);
        localStorage.setItem('locationEnabled', false);
    }
}

function setLocation(state){
    var locationButton = document.getElementById('location-toggle');
    if (state) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                if (document.getElementById('userLat') != null){
                    document.getElementById('userLat').value = position.coords.latitude;
                    document.getElementById('userLng').value = position.coords.longitude;
                    console.log('lat: ' + document.getElementById('userLat').value);
                    console.log('lng: ' + document.getElementById('userLng').value);
                }
                locationButton.classList.remove('btn-outline-primary');
                locationButton.classList.add('btn-primary');
                locationButton.textContent = 'Location Enabled';
                if (window.updateDistanceInputState) {
                    console.log('(T) Calling updateDistance with ' + window.locationEnabled);
                    window.updateDistanceInputState(window.locationEnabled);
                }
            }, function() {
                alert('Location access denied. Enable location to use proximity search.');
            });
        } else {
            alert('Geolocation is not supported by this browser.');
        }
    } else {
        locationButton.classList.remove('btn-primary');
        locationButton.classList.add('btn-outline-primary');
        locationButton.textContent = 'Enable Location';
        if (document.getElementById('userLat') != null){
            document.getElementById('userLat').value = '';
            document.getElementById('userLng').value = '';
            console.log('lat: ' + document.getElementById('userLat').value);
            console.log('lng: ' + document.getElementById('userLng').value);
        }
        
        if (window.updateDistanceInputState) {
            console.log('(F) Calling updateDistance with ' + window.locationEnabled);
            window.updateDistanceInputState(window.locationEnabled);
        }
    }
}