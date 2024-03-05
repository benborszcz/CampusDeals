function convertMilitaryToStandardTime(militaryTime) {
    if (militaryTime.toLowerCase() === "open" || militaryTime.toLowerCase() === "close") {
      return militaryTime;
    }

    // Extract hours and minutes
    var timeArray = militaryTime.split(":");
    var hours = parseInt(timeArray[0]);
    var minutes = timeArray[1];

    // Determine AM or PM
    var period = (hours < 12) ? "AM" : "PM";

    // Convert to 12-hour format
    hours = (hours > 12) ? hours - 12 : hours;
    hours = (hours == 0) ? 12 : hours;

    // Format the time
    var standardTime = hours + ":" + minutes + " " + period;

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

function loadDeal(dealId) {
  // Make an AJAX request to fetch deal details
  console.log('/deal_details/' + dealId);
  fetch('/deal_details/' + dealId)
      .then(response => response.json())
      .then(data => {
          // Populate deal details
          console.log("details retrieved");
          document.getElementById('deal-title').textContent = data.title;
          document.getElementById('establishment-name').textContent = data.establishment.name;
          document.getElementById('deal-description').textContent = data.description;
          document.getElementById('deal-type').textContent = data.deal_details.deal_type;
          document.getElementById('start-time-value').textContent = data.deal_details.start_time;
          document.getElementById('end-time-value').textContent = data.deal_details.end_time;
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
          data.tags.forEach(tag => {  // Adjusted here
              const span = document.createElement('span');
              span.className = 'badge badge-secondary';
              span.textContent = tag;
              tagsContainer.appendChild(span);
          });

          // Show the deal-details container
          document.getElementById('deal-details-container').style.display = 'block';
      })
      .catch(error => {
          console.error('Error fetching deal details:', error);
      });
}