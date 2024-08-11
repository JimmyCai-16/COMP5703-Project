/**
 * Format date into format Sep 24, 2023
 */
function formatTaskDueDate(isoDateString) {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const date = new Date(isoDateString);

  const day = String(date.getDate()).padStart(2, '0');
  const month = months[date.getMonth()];
  const year = date.getFullYear();

  let result = `${month} ${day}`

  if (year != new Date().getFullYear()) {
    result += `, ${year}`;
  }

  return result;
}

/**
 * Format date tooltip for task due date
 */
function taskDueDateToolTip(isoDateString) {
  const dueDate = new Date(isoDateString);
  const dueDay =  parseInt(String(dueDate.getDate()).padStart(2, '0'));
  const dueMonth = dueDate.getMonth();
  const dueYear = dueDate.getFullYear();
  const dueTime = dueDate.getTime();

  let result = ''

  const todayDate = new Date();
  const todayYear = todayDate.getFullYear();
  const todayMonth = todayDate.getMonth();
  const todayDay = parseInt(String(todayDate.getDate()).padStart(2, '0'));
  todayDate.setHours(0, 0, 0, 0)
  const todayTime = todayDate.getTime();

  if (dueYear > todayYear) {
    result = 'This task is due later'
  } else if (dueYear < todayYear) {
    result = 'This task is overdue'
  } else {
    if (dueMonth > todayMonth) {
      result = 'This task is due later'
      const monthsDistance =  dueMonth - todayMonth;
      if (monthsDistance > 1 && monthsDistance <= 3) {
        result = `This task is due ${monthsDistance} months later`
      } else {
        result = 'This task is due next month'
        // Due early next month and current day is end of the month
        const difference_ms = Math.abs(dueTime - todayTime);
        const days_difference = Math.floor(difference_ms / (1000 * 60 * 60 * 24));
        if (days_difference < 10) {
          result = `This task is due in ${days_difference} days`
        }
      }
    } else if (dueMonth < todayMonth) {
      result = 'This task is overdue'
    } else {
      // Same month
      if (dueDay > todayDay) {
        result = `This task is due in ${dueDay - todayDay} days`
        if (dueDay - todayDay === 1 ) {
          result = 'This task is due tomorrow'
        }
      } else if (dueDay < todayDay) {
        result = 'This task is overdue'
      } else {
        result = 'This task is due today'
      }
    }
  }


  return result;
}