var WEEKLY_SCHEDULE = WEEKLY_SCHEDULE || {};

WEEKLY_SCHEDULE.populateDropdownValues = function(e) {
	var $weekly_schedule_school_year_selected = $('#weekly-template-school-year').find(':selected'),
		$weekly_schedule_school_dropdown_cell = $('#weekly-template-school-dropdown-cell'),
		schools = $weekly_schedule_school_year_selected.data('schools'),
		current_langauge = $('#active-language').text(),
		$select = $('<select></select>', {
			'class':'form-control',
			'name':'school'
		});

	if (schools.length > 0) {
		// Populate dropdown for schools
		for(var item in schools) {
			if (current_langauge == 'ja') {
				school_name = schools[item].name_kanji
			}
			else {
				school_name = schools[item].name
			}
			$select.append($('<option></option>', {
				'value':schools[item].id,
				'text':school_name
			}));
		}
	}
	else {
		$select.append($('<option></option>', {
			'value':'0',
			'text':'There are no schools available for the selected school year.'
		}));
		$select.attr('disabled', 'true');
	}
	$weekly_schedule_school_dropdown_cell.html($select);
};

WEEKLY_SCHEDULE.changeButtonHref = function(e) {
	var $link = $('#view-template-link'),
		school_year_id = $('#weekly-template-school-year').val(),
		school_id = $('#weekly-template-school-dropdown-cell > select').val(),
		href = '/schedules/view_template/'+school_year_id+'/'+school_id;

	$link.attr('href', href);
}

$(document).ready(function(){
	WEEKLY_SCHEDULE.populateDropdownValues();
	WEEKLY_SCHEDULE.changeButtonHref();
	
	$(document)
		.on('change', '#weekly-template-school-year', WEEKLY_SCHEDULE.populateDropdownValues)
		.on('change', '#weekly-template-table select', WEEKLY_SCHEDULE.changeButtonHref);
});


