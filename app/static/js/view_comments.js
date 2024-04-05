function loadComments(messages, dealId) {
    // Fetch comments
    fetch('/view-comments-dashboard/' + dealId)
        .then(response => response.json())
        .then(data => {
            selectCard(document.getElementById('deal-card-' + dealId));
            const comments = data.comments;
            const csrfToken = data.csrf_token;
            const commentsContainer = document.getElementById('comments-container');
            commentsContainer.innerHTML = '';

            // Add the deal title
            const dealTitle = document.createElement('h2');
            dealTitle.className = 'card-title';
            dealTitle.id = 'deal-title';
            dealTitle.textContent = data.title;
            commentsContainer.appendChild(dealTitle);

            // Display flash messages, if any
            messages.forEach(message => {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-' + message[0]; // alert type
                alertDiv.role = 'alert';
                alertDiv.textContent = message[1]; // alert message
                commentsContainer.appendChild(alertDiv);
            });
            if (data.user_authenticated) {
                // Create and append the comment form
                const form = document.createElement('form');
                form.action = 'javascript:void(0)'; // avoids page reload
                form.method = 'post';

                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrf_token';
                csrfInput.value = csrfToken; // use the CSRF token obtained from the response

                const div = document.createElement('div');
                div.className = 'mb-3';

                const textarea = document.createElement('textarea');
                textarea.className = 'form-control';
                textarea.placeholder = 'Write your comment here';
                textarea.name = 'comment';

                const button = document.createElement('button');
                button.type = 'submit';
                button.className = 'btn btn-primary';
                button.id = 'submitButton'
                button.textContent = 'Submit Comment';

                div.appendChild(textarea);
                form.appendChild(csrfInput);
                form.appendChild(div);
                form.appendChild(button);
                commentsContainer.appendChild(form);

                // Event listener for comment submission
                form.addEventListener('submit', function(event) {
                    event.preventDefault(); // Prevent default form submission
                    const formData = new FormData(form);

                    // Submit form data asynchronously
                    fetch('/view-comments/' + dealId, {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(result => {
                        loadComments(result.messages, dealId);
                    })
                    .catch(error => console.error('Error submitting comment:', error));
                });
            } else {
                const paragraphElement = document.createElement('p');

                // Create and append the link element
                const linkElement = document.createElement('a');
                linkElement.href = '/login'; // Ensure the path is correct
                linkElement.textContent = 'Log in';
                paragraphElement.appendChild(linkElement);

                // Create a text node for the part before the link
                const textNodeBeforeLink = document.createTextNode(' to leave a comment.');
                paragraphElement.appendChild(textNodeBeforeLink);

                // Append the paragraph to the container
                commentsContainer.appendChild(paragraphElement);
            }

            if (comments.length > 0) {
                comments.forEach(comment => {
                    // Create card elements for each comment
                    const card = document.createElement('div');
                    card.className = 'card mb-3';
                    const cardBody = document.createElement('div');
                    cardBody.className = 'card-body';

                    const strong = document.createElement('strong');
                    strong.textContent = comment[0].username || 'Unknown User';
                    const p1 = document.createElement('p');
                    p1.appendChild(strong);
                    p1.textContent += ' said:';

                    const p2 = document.createElement('p');
                    p2.textContent = comment[0].text || '';

                    const small = document.createElement('small');
                    small.className = 'text-muted';
                    small.textContent = 'Posted on ' + (comment[0].time || 'Unknown Time');

                    // the whole div on the right side of the comments
                    const voteDiv = document.createElement('div');
                    voteDiv.className = 'col-1 d-flex flex-column align-items-center justify-content-center';
                    voteDiv.style.cssFloat = 'right';

                    // Upvote button
                    const upvoteButton = document.createElement('button');
                    upvoteButton.className = 'btn btn-link p-0 mb-0';
                    upvoteButton.innerHTML = '<b>▲</b>';
                    upvoteButton.onclick = () => upvote(dealId, comment[0]['comment_id']);

                    const lockedIcon = document.createElement('a');
                    lockedIcon.href = '/login';
                    lockedIcon.className = 'btn btn-link p-0 mb-0';
                    lockedIcon.innerHTML = '<b>🔒</b>';

                    // Vote count
                    const voteCount = document.createElement('span');
                    voteCount.id = `vote-count-${comment[0]['comment_id']}`;
                    voteCount.textContent = comment[0].upvotes - comment[0].downvotes;

                    // Downvote button
                    const downvoteButton = document.createElement('button');
                    downvoteButton.className = 'btn btn-link p-0 mt-0';
                    downvoteButton.innerHTML = '<b>▼</b>';
                    downvoteButton.onclick = () => downvote(dealId, comment[0]['comment_id']);

                    // Append the voting buttons and count to the voteDiv
                    data.user_authenticated ? voteDiv.appendChild(upvoteButton) : voteDiv.appendChild(lockedIcon);
                    voteDiv.appendChild(voteCount);
                    data.user_authenticated ? voteDiv.appendChild(downvoteButton) : voteDiv.appendChild(lockedIcon.cloneNode(true));
                    
                    cardBody.appendChild(voteDiv);
                    cardBody.appendChild(p1);
                    cardBody.appendChild(p2);
                    cardBody.appendChild(small);

                    if (comment[1].length > 0) {
                        comment[1].forEach(subComment => {
                            // Create card elements for each comment
                            const subCard = document.createElement('div');
                            subCard.className = 'card mb-3';
                            const subCardBody = document.createElement('div');
                            subCardBody.className = 'card-body';

                            const subID = document.createElement('strong');
                            subID.textContent = subComment.username || 'Unknown User';
                            const subP1 = document.createElement('p');
                            subP1.appendChild(subID);
                            subP1.textContent += ' said:';

                            const subP2 = document.createElement('p');
                            subP2.textContent = subComment.text || '';

                            const subSmall = document.createElement('small');
                            subSmall.className = 'text-muted';
                            subSmall.textContent = 'Posted on ' + (subComment.time || 'Unknown Time');

                            // the whole div on the right side of the comments
                            const subVoteDiv = document.createElement('div');
                            subVoteDiv.className = 'col-1 d-flex flex-column align-items-center justify-content-center';
                            subVoteDiv.style.cssFloat = 'right';

                            // Upvote button
                            const subUpvoteButton = document.createElement('button');
                            subUpvoteButton.className = 'btn btn-link p-0 mb-0';
                            subUpvoteButton.innerHTML = '<b>▲</b>';
                            subUpvoteButton.onclick = () => upvote(dealId, subComment['comment_id']);

                            const subLockedIcon = document.createElement('a');
                            subLockedIcon.href = '/login';
                            subLockedIcon.className = 'btn btn-link p-0 mb-0';
                            subLockedIcon.innerHTML = '<b>🔒</b>';

                            // Vote count
                            const subVoteCount = document.createElement('span');
                            subVoteCount.id = `vote-count-${subComment['comment_id']}`;
                            subVoteCount.textContent = subComment.upvotes - subComment.downvotes;

                            // Downvote button
                            const subDownvoteButton = document.createElement('button');
                            subDownvoteButton.className = 'btn btn-link p-0 mt-0';
                            subDownvoteButton.innerHTML = '<b>▼</b>';
                            subDownvoteButton.onclick = () => downvote(dealId, subComment['comment_id']);

                            // Append the voting buttons and count to the voteDiv
                            data.user_authenticated ? subVoteDiv.appendChild(subUpvoteButton) : subVoteDiv.appendChild(subLockedIcon);
                            subVoteDiv.appendChild(subVoteCount);
                            data.user_authenticated ? subVoteDiv.appendChild(subDownvoteButton) : subVoteDiv.appendChild(subLockedIcon.cloneNode(true));
                            
                            subCardBody.appendChild(subVoteDiv);
                            subCardBody.appendChild(subP1);
                            subCardBody.appendChild(subP2);
                            subCardBody.appendChild(subSmall);
                            subCard.appendChild(subCardBody);
                            cardBody.appendChild(subCard);
                        });
                    }
                    card.appendChild(cardBody);
                    commentsContainer.appendChild(card);
                });
            } else {
                const noComments = document.createElement('p');
                noComments.className = 'mt-4';
                noComments.textContent = 'No comments yet.';
                commentsContainer.appendChild(noComments);
            }

            // Hide the deal-details container
            document.getElementById('deal-details-container').style.display = 'none';

            // Show the comments container
            document.getElementById('comments-container').style.display = 'block';
        })
        .catch(error => console.error('Error fetching comments:', error));
}

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
