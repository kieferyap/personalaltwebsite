var WEEKLY_SCHEDULE = WEEKLY_SCHEDULE || {};

WEEKLY_SCHEDULE.clickEditButton = function(e) {
	var $this = $(e.target);
	$('#edit-template-section-period-id').val($this.data('template-section-period-id'));
	$('#edit-template-section-select').val($this.data('section'));
};

$(document).ready(function(){
	$(document)
		.on('mousedown', '.edit-class-button', WEEKLY_SCHEDULE.clickEditButton);
});
