function upvote(dealId, commentId) {
    fetch('/deal/' + dealId + '/comment/' + commentId + '/upvote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Add any other headers your API requires
        },
        body: JSON.stringify({
            'deal_id': dealId,
            'comment_id': commentId
        }),
        // Include credentials if your API requires authentication
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the comment's vote count on the page
            let voteCountElement = document.getElementById('vote-count-' + commentId);
            voteCountElement.textContent = parseInt(voteCountElement.textContent) + 1;
        } else {
            // Handle error
            console.error('Failed to upvote');
        }
    })
    .catch(error => console.error('Error:', error));
}

function downvote(dealId, commentId) {

    fetch('/deal/' + dealId + '/comment/' + commentId + '/downvote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Add any other headers your API requires
        },
        body: JSON.stringify({
            'deal_id': dealId,
            'comment_id': commentId
        }),
        // Include credentials if your API requires authentication
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the comment's vote count on the page
            let voteCountElement = document.getElementById('vote-count-' + commentId);
            voteCountElement.textContent = parseInt(voteCountElement.textContent) - 1;
        } else {
            // Handle error
            console.error('Failed to downvote');
        }
    })
    .catch(error => console.error('Error:', error));
}

function upvoteSubcomment(dealId, parentId, commentId) {
    fetch('/deal/' + dealId + '/comment/' + parentId + '/subcomment/' + commentId + '/upvote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Add any other headers your API requires
        },
        body: JSON.stringify({
            'deal_id': dealId,
            'parent_id': parentId,
            'comment_id': commentId
        }),
        // Include credentials if your API requires authentication
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the comment's vote count on the page
            let voteCountElement = document.getElementById('vote-count-' + commentId);
            voteCountElement.textContent = parseInt(voteCountElement.textContent) + 1;
        } else {
            // Handle error
            console.error('Failed to upvote');
        }
    })
    .catch(error => console.error('Error:', error));
}

function downvoteSubcomment(dealId, parentId, commentId) {

    fetch('/deal/' + dealId + '/comment/' + parentId + '/subcomment/' + commentId + '/downvote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Add any other headers your API requires
        },
        body: JSON.stringify({
            'deal_id': dealId,
            'parent_id': parentId,
            'comment_id': commentId
        }),
        // Include credentials if your API requires authentication
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the comment's vote count on the page
            let voteCountElement = document.getElementById('vote-count-' + commentId);
            voteCountElement.textContent = parseInt(voteCountElement.textContent) - 1;
        } else {
            // Handle error
            console.error('Failed to downvote');
        }
    })
    .catch(error => console.error('Error:', error));
}
