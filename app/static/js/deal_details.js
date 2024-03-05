function convertMilitaryToStandardTime(militaryTime) {
    if (militaryTime.toLowerCase() === "open" || militaryTime.toLowerCase() === "close") {
      return militaryTime;
    }
    console.log(militaryTime);
    // Extract hours and minutes
    var timeArray = militaryTime.split(":");
    var hours = parseInt(timeArray[0]);
    var minutes = parseInt(timeArray[1]); // Parse minutes as an integer

    console.log(hours);

    // Determine AM or PM
    var period = (hours < 12) ? "AM" : "PM";

    // Convert to 12-hour format
    hours = (hours > 12) ? hours - 12 : hours;
    hours = (hours == 0) ? 12 : hours;

    console.log(hours);

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