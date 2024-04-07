function voteDeal(dealId, isUpvote) {
    fetch('/deal/' + dealId + (isUpvote ? '/upvote' : '/downvote'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 'deal_id': dealId }),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the vote count on the page
            const voteDirection = isUpvote ? 1 : -1;
            const voteCountElement = document.getElementById('vote-count-' + dealId);
            voteCountElement.textContent = parseInt(voteCountElement.textContent) + voteDirection;
        } else {
            // Handle error
            console.error(`Failed to ${isUpvote ? 'upvote' : 'downvote'}`);
        }
    })
    .catch(error => console.error('Error:', error));
}

function upvote(dealId) {
    fetch('/deal/' + dealId + '/upvote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Add any other headers your API requires
        },
        body: JSON.stringify({ 'deal_id': dealId }),
        // Include credentials if your API requires authentication
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the vote count on the page
            let voteCountElement = document.getElementById('vote-count-' + dealId);
            voteCountElement.textContent = parseInt(voteCountElement.textContent) + 1;
        } else {
            // Handle error
            console.error('Failed to upvote');
        }
    })
    .catch(error => console.error('Error:', error));
}

function downvote(dealId) {
    fetch('/deal/' + dealId + '/downvote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Add any other headers your API requires
        },
        body: JSON.stringify({ 'deal_id': dealId }),
        // Include credentials if your API requires authentication
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the vote count on the page
            let voteCountElement = document.getElementById('vote-count-' + dealId);
            voteCountElement.textContent = parseInt(voteCountElement.textContent) - 1;
        } else {
            // Handle error
            console.error('Failed to downvote');
        }
    })
    .catch(error => console.error('Error:', error));
}

function requestLocation() {
    if (document.getElementById('distance-input').value !== "" && navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            // Populate hidden form fields
            document.getElementById('userLat').value = position.coords.latitude;
            document.getElementById('userLng').value = position.coords.longitude;
        }, function(error) {
            alert('Unable to retrieve your location. Please check your settings and try again.');
        });
    }
}