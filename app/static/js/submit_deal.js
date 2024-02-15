document.addEventListener('DOMContentLoaded', function() {
    var allDayCheckbox = document.getElementById('all-day-checkbox');
    var startTimeInput = document.getElementById('start-time');
    var endTimeInput = document.getElementById('end-time');

    // Function to toggle the disabled state of start and end time inputs
    function toggleTimeInputs() {
        var disabled = allDayCheckbox.checked;
        startTimeInput.disabled = disabled;
        endTimeInput.disabled = disabled;
    }

    // Add event listener to the All Day checkbox
    allDayCheckbox.addEventListener('change', toggleTimeInputs);

    // Call the function on page load to set the initial state
    toggleTimeInputs();
});