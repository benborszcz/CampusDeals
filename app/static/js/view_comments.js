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

            // creates add comment form if user is logged in
            commentSubmission(csrfToken, commentsContainer, dealId, null, data.user_authenticated);

            if (comments.length > 0) {
                comments.forEach(comment => {
                    // Create card elements for each comment
                    const card = document.createElement('div');
                    card.className = 'card mb-3';
                    const cardBody = document.createElement('div');
                    cardBody.className = 'card-body';

                    createCommentElement(cardBody, comment[0], data, dealId, null);

                    if (comment[1].length > 0) {
                        comment[1].forEach(subComment => {
                            // Create card elements for each comment
                            const subCard = document.createElement('div');
                            subCard.className = 'card mb-3';
                            const subCardBody = document.createElement('div');
                            subCardBody.className = 'card-body';
                            createCommentElement(subCardBody, subComment, data, dealId, comment[0]['comment_id']);
                            // creates add comment form if user is logged in
                            subCard.appendChild(subCardBody);
                            cardBody.appendChild(subCard);
                        });
                    }
                    // creates add reply form if user is logged in
                    commentSubmission(csrfToken, cardBody, dealId, comment[0]['comment_id'], data.user_authenticated);
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

function createCommentElement (cardBody, comment, data, dealId, parentId) {
    // Profile picture
    const img = document.createElement('img');
    img.className = 'profile-pic-small';
    img.src = comment.profile_picture ? comment.profile_picture : defaultProfilePic;
    img.alt = comment.profile_picture ? "User profile picture" : "Default profile picture";
    
    // Username
    const strong = document.createElement('strong');
    strong.textContent = comment.username || 'Unknown User';
    const p1 = document.createElement('p');
    p1.appendChild(strong);
    p1.textContent += ' said:';

    // The actual comment text
    const p2 = document.createElement('p');
    p2.textContent = comment.text || '';

    // Post time
    const small = document.createElement('small');
    small.className = 'text-muted';
    small.textContent = 'Posted on ' + (comment.time || 'Unknown Time');

    // The whole div for voting on the right side of the comments
    const voteDiv = document.createElement('div');
    voteDiv.className = 'col-1 d-flex flex-column align-items-center justify-content-center';
    voteDiv.style.cssFloat = 'right';

    // Upvote button
    const upvoteButton = document.createElement('button');
    upvoteButton.className = 'btn btn-link p-0 mb-0';
    upvoteButton.innerHTML = '<b>▲</b>';
    upvoteButton.onclick = () => voteComment(dealId, comment['comment_id'], true, parentId);

    // Locked icon if not logged in
    const lockedIcon = document.createElement('a');
    lockedIcon.href = '/login';
    lockedIcon.className = 'btn btn-link p-0 mb-0';
    lockedIcon.innerHTML = '<b>🔒</b>';

    // Vote count
    const voteCount = document.createElement('span');
    voteCount.id = `vote-count-${comment['comment_id']}`;
    voteCount.textContent = comment.upvotes - comment.downvotes;

    // Downvote button
    const downvoteButton = document.createElement('button');
    downvoteButton.className = 'btn btn-link p-0 mt-0';
    downvoteButton.innerHTML = '<b>▼</b>';
    downvoteButton.onclick = () => voteComment(dealId, comment['comment_id'], false, parentId);

    // Append the voting buttons and count to the voteDiv
    data.user_authenticated ? voteDiv.appendChild(upvoteButton) : voteDiv.appendChild(lockedIcon);
    voteDiv.appendChild(voteCount);
    data.user_authenticated ? voteDiv.appendChild(downvoteButton) : voteDiv.appendChild(lockedIcon.cloneNode(true));
    
    cardBody.appendChild(voteDiv);
    cardBody.appendChild(img);
    cardBody.appendChild(p1);
    cardBody.appendChild(p2);
    cardBody.appendChild(small);
}

function voteComment(dealId, commentId, isUpvote, parentId) {
    fetch('/deal/' + dealId + '/comment/' + (parentId ? parentId + '/subcomment/' : '') + commentId + (isUpvote ? '/upvote' : '/downvote'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 'deal_id': dealId, 'comment_id': commentId, ...(parentId && { 'parent_id': parentId }) }),
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const voteDirection = isUpvote ? 1 : -1;
            const voteCountElement = document.getElementById('vote-count-' + commentId);
            voteCountElement.textContent = parseInt(voteCountElement.textContent) + voteDirection;
        } else {
            console.error(`Failed to ${isUpvote ? 'upvote' : 'downvote'}`);
        }
    })
    .catch(error => console.error('Error:', error));
}

function commentSubmission(csrfToken, container, dealId, parentId, user_authenticated) {
    if (user_authenticated) {
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
        textarea.placeholder = 'Write your ' + (parentId ? 'reply' : 'comment') + ' here';
        textarea.name = 'comment';

        const button = document.createElement('button');
        button.type = 'submit';
        button.className = 'btn btn-primary';
        button.id = 'submitButton'
        button.textContent = 'Submit ' + (parentId ? 'Reply' : 'Comment');

        div.appendChild(textarea);
        form.appendChild(csrfInput);
        form.appendChild(div);
        form.appendChild(button);
        container.appendChild(form);

        // Event listener for comment submission
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default form submission
            const formData = new FormData(form);

            // Submit form data asynchronously
            fetch('/view-comments-dashboard/' + dealId + (parentId ? '/' + parentId : ''), {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(result => {
                loadComments(result.messages, dealId);
            })
            .catch(error => console.error('Error submitting ' + (parentId ? 'reply' : 'comment') + ':', error));
        });
    } else {
        // only appends log in for the first comment form
        if (!parentId) {
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
            container.appendChild(paragraphElement);
        }
    }
}
