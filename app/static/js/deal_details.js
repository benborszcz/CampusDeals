function convertMilitaryToStandardTime(militaryTime) {
    if (militaryTime.toLowerCase() === "open" || militaryTime.toLowerCase() === "close") {
      return militaryTime;
    }
    
    // Extract hours and minutes
    var timeArray = militaryTime.split(":");
    var hours = parseInt(timeArray[0]);
    var minutes = parseInt(timeArray[1]); // Parse minutes as an integer

    // Determine AM or PM
    var period = (hours < 12) ? "AM" : "PM";

    // Convert to 12-hour format
    hours = (hours > 12) ? hours - 12 : hours;
    hours = (hours == 0) ? 12 : hours;

    // Format the time
    var standardTime = hours.toString().padStart(2, '0') + ":" + minutes.toString().padStart(2, '0') + " " + period;
    console.log(standardTime);
    return standardTime;
}

document.addEventListener("DOMContentLoaded", function() {
    // Replace military time with standard time for Start Time
    var startTimeElement = document.querySelector("#start-time");
    startTimeElement.innerHTML = "Start Time: " + convertMilitaryToStandardTime("{{ deal.deal_details.start_time }}");

    // Replace military time with standard time for End Time
    var endTimeElement = document.querySelector("#end-time");
    endTimeElement.innerHTML = "End Time: " + convertMilitaryToStandardTime("{{ deal.deal_details.end_time }}");
});

function selectCard(cardElement) {
    // Remove the 'selected-card' class from all cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.classList.remove('selected-card');
    });

    // Add the 'selected-card' class to the clicked card
    cardElement.classList.add('selected-card');
}

function loadDeal(dealId) {
    // Make an AJAX request to fetch deal details
    fetch('/deal_details_dashboard/' + dealId)
        .then(response => response.json())
        .then(data => {
            selectCard(document.getElementById('deal-card-' + dealId));
            document.getElementById('deal-title').textContent = data.title;

            // Populate establishment details as a clickable link
            const establishmentLink = document.getElementById('establishment-link');
            establishmentLink.href = `/establishment_details/${data.establishment.name}`;
            establishmentLink.textContent = data.establishment.name;

            // Google Maps directions link
            const googleMapsLink = document.getElementById('google-maps-link');
            googleMapsLink.innerHTML = `<a href="https://www.google.com/maps/dir/?api=1&destination=${data.establishment.latitude},${data.establishment.longitude}" target="_blank">${data.establishment.address} Directions</a>`;

            // Populate deal time details
            const dealTimeDetails = document.getElementById('deal-time-details');
            dealTimeDetails.textContent = `${data.deal_details.days_active.join(", ")}, ${convertMilitaryToStandardTime(data.deal_details.start_time)} - ${convertMilitaryToStandardTime(data.deal_details.end_time)}`;

            // Populate tags
            const tagsContainer = document.getElementById('tags-container');
            tagsContainer.innerHTML = '';
            if (data.tags) {
                data.tags.forEach(tag => {  // Adjusted here
                    const span = document.createElement('span');
                    span.className = 'badge badge-secondary';
                    span.textContent = tag;
                    tagsContainer.appendChild(span);
                });
            }
            // Populate deal items
            const dealItemsDetails = document.getElementById('deal-items-details');
            dealItemsDetails.innerHTML = ''; // Clear existing items
            data.deal_details.deal_items.forEach(item => {
                const itemDetail = document.createElement('div');
                itemDetail.textContent = `${item.item} - ${item.pricing.discount === 'N/A' ? item.pricing.price : item.pricing.discount}`;
                dealItemsDetails.appendChild(itemDetail);
            });

            // const relativeTime = dateFns.formatDistanceToNow(dateFns.parseISO(data.created_at), { addSuffix: true });
            document.getElementById('created-at').textContent = data.created_at;

            // console.log(relativeTime);  // e.g., "2 days ago" (depending on the current date when you run this)

            // Initialize the map with the deal location
            // initializeMap(data.establishment.latitude, data.establishment.longitude);

            // Other existing code for populating tags, created at, etc.
            // Show the deal-details container
            document.getElementById('deal-details-container').style.display = 'block';

            // Hide the comments container
            document.getElementById('comments-container').style.display = 'none';
        })
        .catch(error => {
            console.error('Error fetching deal details:', error);
        });
}

function loadDealOld(dealId) {
    // Make an AJAX request to fetch deal details
    fetch('/deal_details_dashboard/' + dealId)
        .then(response => response.json())
        .then(data => {
            selectCard(document.getElementById('deal-card-' + dealId));
            // Populate deal details
            document.getElementById('deal-title').textContent = data.title;
            document.getElementById('establishment-name').textContent = data.establishment.name;
            document.getElementById('deal-description').textContent = data.description;
            document.getElementById('deal-type').textContent = data.deal_details.deal_type;
            document.getElementById('start-time').textContent = data.deal_details.start_time;
            document.getElementById('end-time').textContent = data.deal_details.end_time;
            document.getElementById('days-active').textContent = data.deal_details.days_active.join(", ");
            document.getElementById('exclusions').textContent = data.deal_details.exclusions;
            document.getElementById('created-at').textContent = data.created_at;

            // Populate deal items
            const dealItemsList = document.getElementById('deal-items-list');
            dealItemsList.innerHTML = '';
            data.deal_details.deal_items.forEach(item => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.textContent = `${item.item} - ${item.item_type} - Price: ${item.pricing.price} Discount: ${item.pricing.discount}`;
                dealItemsList.appendChild(li);
            });

            // Populate tags
            const tagsContainer = document.getElementById('tags-container');
            tagsContainer.innerHTML = '';
            if (data.tags) {
                data.tags.forEach(tag => {  // Adjusted here
                    const span = document.createElement('span');
                    span.className = 'badge badge-secondary';
                    span.textContent = tag;
                    tagsContainer.appendChild(span);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching deal details:', error);
        });
}