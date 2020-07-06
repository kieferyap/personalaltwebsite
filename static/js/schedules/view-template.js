var WEEKLY_SCHEDULE = WEEKLY_SCHEDULE || {};

WEEKLY_SCHEDULE.clickAddButton = function(e) {
	// alert("Button clicked");
	var $this = $(e.target);
	$('#add-class-school-period-id').val($this.data('school-period-id'));
};

$(document).ready(function(){
	$(document)
		.on('mousedown', '.add-class-button', WEEKLY_SCHEDULE.clickAddButton);
});
