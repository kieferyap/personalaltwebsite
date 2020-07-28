var WEEKLY_SCHEDULE = WEEKLY_SCHEDULE || {};

WEEKLY_SCHEDULE.clickAddButton = function(e) { 
	var $this = $(e.target); 
	$('#add-class-school-period-id').val($this.data('school-period-id')); 
	$('#weekday-number').val($this.data('weekday')); 
}; 

WEEKLY_SCHEDULE.clickEditButton = function(e) {
	var $this = $(e.target);
	$('#edit-template-section-period-id').val($this.data('template-section-period-id'));
	$('#edit-template-section-select').val($this.data('section'));
};

$(document).ready(function(){
	$(document)
		.on('mousedown', '.add-class-button', WEEKLY_SCHEDULE.clickAddButton) 
		.on('mousedown', '.edit-class-button', WEEKLY_SCHEDULE.clickEditButton);
});
