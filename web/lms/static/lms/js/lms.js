$(document).ready(function() {
  var lastScrollTop = 0;
  
  // Close dropdown on document scroll up
  $(window).scroll(function() {
    var scrollPosition = $(this).scrollTop();
    var targetPosition = 250; // Replace with your desired scroll position
    
    if (scrollPosition <= targetPosition) {
      $('.reminders-dropdown-menu').removeClass('show');
      $('.files-dropdown-menu').removeClass('show');
      $('.correspondence-dropdown-menu').removeClass('show');
      $('.files-dropdown-menu').removeClass('show');
      $('.history-dropdown-menu').removeClass('show');
    }
    
    
  });
  // $('#scrollToBottomButton').click(function() {
  //   $('html, body').animate({scrollTop: $(document).height()}, 'slow');
  // });
  $('#remindersDropdownMenuButton').click(function() {
    $('html, body').animate({scrollTop: $(document).height()}, 'slow');
  });
 
});

// UI
$LMS.on('mouseenter', '.tooltip-wrap', function (e) {
  const tooltip_wrap = $(e.target)
  const tooltip = $(e.target).find('.tooltip')
  const tooltipAction = tooltip.find('.tooltip-action')
  
  // Title 'Close ____' when the following dropdown is open
  if (tooltip_wrap.data('bs-toggle') == 'dropdown' && tooltip_wrap.hasClass('show')) {
    tooltipAction.html(tooltipAction.attr('titleOnClose'))
  } else {
    tooltipAction.html(tooltipAction.attr('title'))
  }
})
