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
    return standardTime;
}

function toRelativeTime(utcString) {
    const currentTime = new Date();
    const givenTime = new Date(utcString);
    const timeDifference = currentTime - givenTime; // Difference in milliseconds
  
    const minute = 60 * 1000; // milliseconds
    const hour = 60 * minute;
    const day = 24 * hour;
    const month = 30 * day; // Approximation
    const year = 365.25 * day;
  
    let relativeTime = '';
    let timeUnit = 0;
    let timeLabel = '';
  
    if (Math.abs(timeDifference) < hour) {
      timeUnit = Math.round(Math.abs(timeDifference) / minute);
      timeLabel = 'minute';
    } else if (Math.abs(timeDifference) < day) {
      timeUnit = Math.round(Math.abs(timeDifference) / hour);
      timeLabel = 'hour';
    } else if (Math.abs(timeDifference) < month) {
      timeUnit = Math.round(Math.abs(timeDifference) / day);
      timeLabel = 'day';
    } else if (Math.abs(timeDifference) < year) {
      timeUnit = Math.round(Math.abs(timeDifference) / month);
      timeLabel = 'month';
    } else {
      timeUnit = Math.round(Math.abs(timeDifference) / year);
      timeLabel = 'year';
    }
  
    // Pluralize label
    if (timeUnit !== 1) {
      timeLabel += 's';
    }
    relativeTime = `${timeUnit} ${timeLabel} ago`;
  
    return relativeTime;
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
            document.getElementById('establishment-name').textContent = data.establishment.name;

            // Google Maps directions link
            const googleMapsLink = document.getElementById('google-maps-link');
            googleMapsLink.innerHTML = `<a href="https://www.google.com/maps/dir/?api=1&destination=${data.establishment.latitude},${data.establishment.longitude}" target="_blank">${data.establishment.address} Directions</a>`;

            // Populate deal time details
            const dealTimeDetails = document.getElementById('deal-time-details');
            dealTimeDetails.textContent = `${data.deal_details.days_active.join(", ")}, ${convertMilitaryToStandardTime(data.deal_details.start_time)} - ${convertMilitaryToStandardTime(data.deal_details.end_time)}`;


            var mapContainer = L.DomUtil.get('map2');
            if (mapContainer != null) {
                mapContainer._leaflet_id = null;  // Reset the id to make sure Leaflet allows a new map to be initialized
            }

            var map = L.map('map2', {
                center: [data.establishment.latitude, data.establishment.longitude],
                zoom: 18,
                maxZoom: 19, // Global maximum zoom level for the map
                minZoom: 10
            });
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors',
                maxZoom: 19,
                minZoom: 10
            }).addTo(map);
    
    
            // Add markers and popups with URLs
            L.marker([data.establishment.latitude, data.establishment.longitude]).addTo(map)
                .bindPopup(`
                    <div style="text-decoration: none;">
                        <strong>${data.establishment.shortname}</strong> - <span style="font-size: smaller;">${data.deal_details.deal_name}</span>
                        <br>
                        <div>
                            <span style="font-size: x-small;">${data.deal_details.deal_description}</span>
                        </div>
                    </div>
                `, { maxWidth: 200 });

            // Populate tags
            const tagsContainer = document.getElementById('tags-container');
            const c = document.createElement('c');
            tagsContainer.innerHTML = '';
            if (data.tags) {
                data.tags.forEach(tag => {  // Adjusted here
                    const span = document.createElement('span');
                    span.className = 'badge badge-secondary';
                    span.id = 'badge';
                    span.textContent = tag;
                    c.appendChild(span);
                });
            }
            tagsContainer.appendChild(c);
            // Populate deal items
            const dealItemsDetails = document.getElementById('deal-items-details');
            dealItemsDetails.innerHTML = ''; // Clear existing items
            data.deal_details.deal_items.forEach(item => {
                const c1 = document.createElement('c');
                const bItem = document.createElement('b');
                bItem.textContent = item.item + ' - ';
                c1.appendChild(bItem);
                const bPriceOrDiscount = document.createElement('b');
                bPriceOrDiscount.id = 'priceOrDiscount';
                bPriceOrDiscount.textContent = item.pricing.discount === 'N/A' ? item.pricing.price : item.pricing.discount;
                c1.appendChild(bPriceOrDiscount);
                c1.appendChild(document.createElement('br'))
                dealItemsDetails.appendChild(c1);
            });

            document.getElementById('created-at').textContent = toRelativeTime(data.created_at);

            // Show the deal-details container
            document.getElementById('deal-details-container').style.display = 'block';

            // Hide the comments container
            document.getElementById('comments-container').style.display = 'none';
        })
        .catch(error => {
            console.error('Error fetching deal details:', error);
        });
}