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