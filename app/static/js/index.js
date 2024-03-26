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

function updateDistanceInputState(locationEnabled) {
    console.log('Update distance getting called, set to ' + locationEnabled);
    const distanceInput = document.getElementById('distance-input');
    if (locationEnabled) {
        distanceInput.removeAttribute('disabled');
        distanceInput.placeholder = "Enter distance in miles";
    } else {
        distanceInput.setAttribute('disabled', true);
        distanceInput.placeholder = "Enable location to use this filter";
    }
}