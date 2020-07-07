from collections import OrderedDict
from datetime import datetime as dt

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST

from lessons.forms import LessonPlanForm, CourseDropdownForm
from lessons.models import Lesson
from paw.constants.base import NAME, URL, IS_SELECTED, SCHEDULES, MODAL_ID
from paw.methods import render_page, school_year_required, get_value_of_optional_field_in_post_or_none
from schedules.forms import *
from schedules.models import *
from schedules.constants import *
from schedules.managers import SchoolSectionManager, TemplatePeriodTypeManager
from schoolyears.models import SchoolYear, School, YearlySchedule


def schedule_render_page(request,
                     page='index',
                     context={},
                     selected_sidebar=SCHEDULE_MANAGER):

    # Sidebar
    schedule_manager = {
        NAME: NAME_SCHEDULE_MANAGER,
        URL: 'schedules/'+SCHEDULE_MANAGER,
        IS_SELECTED: False,
        MODAL_ID: None,
    }
    sections_courses = {
        NAME: NAME_SECTIONS_COURSES,
        URL: 'schedules/'+SECTIONS_COURSES,
        IS_SELECTED: False,
        MODAL_ID: None,
    }
    school_periods = {
        NAME: NAME_SCHOOL_PERIODS,
        URL: 'schedules/'+SCHOOL_PERIODS,
        IS_SELECTED: False,
        MODAL_ID: None,
    }
    weekly_template = {
        NAME: NAME_WEEKLY_TEMPLATE,
        URL: 'schedules/'+WEEKLY_TEMPLATE,
        IS_SELECTED: False,
        MODAL_ID: None,
    }

    sidebar = OrderedDict()
    sidebar[SCHEDULE_MANAGER] = schedule_manager
    sidebar[SECTIONS_COURSES] = sections_courses
    sidebar[SCHOOL_PERIODS] = school_periods
    sidebar[WEEKLY_TEMPLATE] = weekly_template
    sidebar[selected_sidebar][IS_SELECTED] = True

    return render_page(request,
                       page,
                       context,
                       sidebar=sidebar,
                       selected_menu=SCHEDULES)

@school_year_required
def index(request):
    context = {}
    context['all_school_years'] = SchoolYear.objects.get_school_years_and_schools()
    return schedule_render_page(request,
                       page=SCHEDULE_MANAGER,
                       context=context,
                       selected_sidebar=SCHEDULE_MANAGER)

def view_schedule(request, school_year_id=None, school_id=None, year=None, month=None):
    if school_year_id is not None and school_id is not None and year is not None and month is not None:
        context = {}
        school_year = get_object_or_404(SchoolYear, pk=school_year_id)
        school = get_object_or_404(School, pk=school_id)

        all_schedules = YearlySchedule.objects.get_school_schedule(school, year, month)
        
        # For the Add Class form
        context['all_year_levels'] = SectionPeriod.objects.get_year_level_dropdown(school) 
        context['all_schedules'] = all_schedules
        context['school'] = school
        context['current_date'] = dt.strptime("%s-%s-01"%(year, month), "%Y-%m-%d")
        context['all_sections'] = SchoolSectionManager().get_sections(school)
        context['all_lesson_plans'] = LessonPlan.objects.filter(is_premade_lesson_plan=True).all().order_by('lesson__course__course_name', 'lesson__lesson_number', 'hour_number')

        return schedule_render_page(request,
                           page=VIEW_SCHEDULE,
                           context=context,
                           selected_sidebar=SCHEDULE_MANAGER)
    else:
        messages.error(request, MSG_ERR_SCHEDULE_INCOMPLETE)
        return redirect('/schedules/schedule_manager')

def delete_class(request, section_period_id):
    section_period = get_object_or_404(SectionPeriod, pk=int(section_period_id))
    lesson_plan = LessonPlan.objects.get(id=section_period.lesson_plan.id)
    section_period.delete()
    lesson_plan.delete()
    messages.success(request, MSG_DELETE_CLASS)
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def add_all_classes(request):
    lesson_plan_id = get_value_of_optional_field_in_post_or_none(request, 'lesson-plan-id')
    lesson_plan_raw = None if lesson_plan_id is None or int(lesson_plan_id) == 0 else get_object_or_404(LessonPlan, pk=int(lesson_plan_id))

    date = dt.strptime(request.POST['date'], "%Y-%m-%d")
    period_count = int(request.POST['period-count'])
    period_section = []

    lesson_number = 1
    hour_number = 1

    for i in range(1, period_count+1):
        section_id = int(request.POST['section-'+str(i)])
        if section_id != 0:
            section = get_object_or_404(Section, pk=section_id)

            school_period_id = request.POST['period-'+str(i)]
            school_period = get_object_or_404(SchoolPeriod, pk=int(school_period_id))

            if lesson_plan_raw is None:
                lesson_plan = LessonPlan(
                    lesson=None,
                    hour_number=None,
                    greeting=None,
                    warmup=None,
                    presentation=None,
                    practice=None,
                    production=None,
                    cooldown=None,
                    assessment=None,
                    is_premade_lesson_plan=False,
                )
                lesson_plan.save()
                last_period = SectionPeriod.objects.filter(section=section)
                if last_period.exists():
                    last_period = last_period.latest('date')
                    lesson_number = last_period.lesson_number
                    hour_number = last_period.hour_number+1
            else:
                lesson_plan = lesson_plan_raw
                lesson_number = 1
                if lesson_plan.lesson is not None:
                    lesson_number = lesson_plan.lesson.lesson_number
                hour_number = lesson_plan.hour_number
                lesson_plan.pk = None
                lesson_plan.is_premade_lesson_plan = False
                lesson_plan.save()

            new_section_period = SectionPeriod(
                date=date,
                section=section,
                school_period=school_period,
                lesson_plan=lesson_plan,
                lesson_number=lesson_number,
                hour_number=hour_number,
                notes='',
            )
            new_section_period.save()

    messages.success(request, MSG_ADD_CLASS)
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def add_class(request):
    lesson_plan_id = get_value_of_optional_field_in_post_or_none(request, 'lesson_plan')
    section_id = get_value_of_optional_field_in_post_or_none(request, 'section')

    if section_id is None:
        messages.error(request, MSG_ERR_CANNOT_ADD_CLASS_WITHOUT_SECTION)

    lesson_plan = None if lesson_plan_id is None or int(lesson_plan_id) == 0 else get_object_or_404(LessonPlan, pk=int(lesson_plan_id))
    school_period = get_object_or_404(SchoolPeriod, pk=int(request.POST['school_period_id']))
    school_section = get_object_or_404(SchoolSection, pk=int(request.POST['year_level']))
    section = get_object_or_404(Section, pk=int(section_id))
    date = dt.strptime(request.POST['date'], "%Y-%m-%d")
    notes = request.POST['notes']

    lesson_number = 1
    hour_number = 1

    if lesson_plan is None:
        lesson_plan = LessonPlan(
            lesson=None,
            hour_number=None,
            greeting=None,
            warmup=None,
            presentation=None,
            practice=None,
            production=None,
            cooldown=None,
            assessment=None,
            is_premade_lesson_plan=False,
        )
        lesson_plan.save()
        last_period = SectionPeriod.objects.filter(section=section)
        if last_period.exists():
            last_period = last_period.latest('date')
            lesson_number = last_period.lesson_number
            hour_number = last_period.hour_number+1
    elif lesson_plan.is_premade_lesson_plan == False:
        source_section_period = SectionPeriod.objects.get(lesson_plan=lesson_plan)
        if source_section_period is not None:
            lesson_number = source_section_period.lesson_number
            hour_number = source_section_period.hour_number
        lesson_plan.pk = None
        lesson_plan.save()
    else:
        lesson_number = 1
        if lesson_plan.lesson is not None:
            lesson_number = lesson_plan.lesson.lesson_number
        hour_number = lesson_plan.hour_number
        lesson_plan.pk = None
        lesson_plan.is_premade_lesson_plan = False
        lesson_plan.save()

    new_section_period = SectionPeriod(
        date=date,
        section=section,
        school_period=school_period,
        lesson_plan=lesson_plan,
        lesson_number=lesson_number,
        hour_number=hour_number,
        notes=notes,
    )
    new_section_period.save()
    messages.success(request, MSG_ADD_CLASS)
    return JsonResponse({'is_success': True, 'messages': None})

def view_section_period(request, section_period_id=None):
    context = {}
    date = None
    school_name = None
    period = None
    course = None
    lesson_number = None
    hour_number = None
    section_name = None
    school_id = None
    school_year_id = None
    edit_lesson_hour_form = LessonHourForm()

    if section_period_id is not None:
        section_period = get_object_or_404(SectionPeriod, pk=section_period_id)
        edit_lesson_hour_form = LessonHourForm(instance=section_period)
        
        all_lessons = Lesson.objects.none()
        school_section_courses = SchoolSectionCourse.objects.filter(school_section=section_period.section.school_section)
        for school_section in school_section_courses:
            course = school_section.course
            all_lessons = all_lessons.union(Lesson.objects.filter(course=course))
            
        lesson_plan = section_period.lesson_plan
        lesson_plan.edit_hour_form = LessonPlanForm(instance=lesson_plan, lessons=all_lessons)
        
        date = section_period.date
        period = section_period.school_period.period_number
        course = None if lesson_plan.lesson is None else lesson_plan.lesson.course.course_name
        lesson_number = section_period.lesson_number
        hour_number = section_period.hour_number

        school_section = section_period.section.school_section
        if school_section.is_special_needs:
            section_name = 'SN-'+str(section_period.section.section_name)
        else:
            section_name = str(school_section.year_level)+'-'+str(section_period.section.section_name)
        
        school = section_period.school_period.school_period_type.school
        school_name = school.name
        school_id = school.id
        school_year_id = school.school_year.id

    context['date'] = date
    context['school_name'] = school_name
    context['section_name'] = section_name
    context['period'] = period
    context['course'] = course
    context['lesson_number'] = lesson_number
    context['hour_number'] = hour_number
    context['hour'] = lesson_plan
    context['edit_lesson_hour_form'] = edit_lesson_hour_form
    context['section_period_id'] = section_period_id
    context['school_id'] = school_id
    context['school_year_id'] = school_year_id

    return schedule_render_page(request,
           page=VIEW_SECTION_PERIOD,
           context=context,
           selected_sidebar=SCHEDULE_MANAGER)

@require_POST
def edit_class(request):
    section_period = get_object_or_404(SectionPeriod, pk=int(request.POST['section_period_id']))
    
    lesson_plan_id = get_value_of_optional_field_in_post_or_none(request, 'lesson_plan')
    section_id = get_value_of_optional_field_in_post_or_none(request, 'section')
    notes = request.POST['notes']
    
    if section_id is None:
        messages.error(request, MSG_ERR_CANNOT_ADD_CLASS_WITHOUT_SECTION)

    section_period.section = get_object_or_404(Section, pk=int(section_id))
    lesson_plan = None if lesson_plan_id is None or int(lesson_plan_id) == 0 else get_object_or_404(LessonPlan, pk=int(lesson_plan_id))
    lesson_number = 1
    hour_number = 1
    if lesson_plan is None:
        lesson_plan = LessonPlan(
            lesson=None,
            hour_number=None,
            greeting=None,
            warmup=None,
            presentation=None,
            practice=None,
            production=None,
            cooldown=None,
            assessment=None,
            is_premade_lesson_plan=False,
        )
        lesson_plan.save()
        last_period = SectionPeriod.objects.filter(section=section_period.section)
        if last_period.exists():
            last_period = last_period.latest('date')
            lesson_number = last_period.lesson_number
            hour_number = last_period.hour_number+1
    elif lesson_plan.is_premade_lesson_plan == False:
        source_section_period = SectionPeriod.objects.get(lesson_plan=lesson_plan)
        if source_section_period is not None:
            lesson_number = source_section_period.lesson_number
            hour_number = source_section_period.hour_number
        lesson_plan.pk = None
        lesson_plan.save()
    else:
        lesson_number = 1
        if lesson_plan.lesson is not None:
            lesson_number = lesson_plan.lesson.lesson_number
        hour_number = lesson_plan.hour_number
        lesson_plan.pk = None
        lesson_plan.is_premade_lesson_plan = False
        lesson_plan.save()

    section_period.hour_number = hour_number
    section_period.lesson_number = lesson_number
    section_period.lesson_plan = lesson_plan
    section_period.notes = notes
    section_period.save()
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def edit_lesson_hour(request):
    section_period = get_object_or_404(SectionPeriod, pk=int(request.POST['section_period_id']))
    section_period.lesson_number = int(request.POST['lesson_number'])
    section_period.hour_number = int(request.POST['hour_number'])
    section_period.save()
    messages.success(request, MSG_EDIT_LESSON_HOUR)
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def edit_schedule_period_profile(request):
    school_period_type = get_object_or_404(SchoolPeriodType, pk=int(request.POST['school_period_type']))
    section_period_type = get_object_or_404(SectionPeriodType, pk=int(request.POST['id']))
    section_period_type.school_period_type = school_period_type
    section_period_type.save()
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def edit_template_period_profile(request):
    template_period_type = get_object_or_404(TemplatePeriodType, pk=int(request.POST['id']))
    school_period_type = get_object_or_404(SchoolPeriodType, pk=int(request.POST['school_period_type']))
    template_period_type.school_period_type = school_period_type
    template_period_type.save()
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def edit_lesson_plans(request):
    date = request.POST['date']
    lesson_plan_id = request.POST['lesson-plan-id']

    sections = SectionPeriod.objects.filter(date=date)
    for section in sections:
        lesson_plan = get_object_or_404(LessonPlan, pk=int(lesson_plan_id))
        lesson_plan.pk = None
        lesson_plan.save()
        section.lesson_plan = lesson_plan
        section.save()

    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def assign_book(request):
    school_section = get_object_or_404(SchoolSection, pk=int(request.POST['school_section_id']))
    course = get_object_or_404(Course, pk=int(request.POST['book']))
    new_school_section_course = SchoolSectionCourse(
        school_section=school_section,
        course=course
    )
    new_school_section_course.save()
    messages.success(request, MSG_ASSIGN_BOOK)
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def reassign_book(request):
    school_section_course = get_object_or_404(SchoolSectionCourse, pk=int(request.POST['school_section_course_id']))
    school_section_course.course = get_object_or_404(Course, pk=int(request.POST['book']))
    school_section_course.school_section = get_object_or_404(SchoolSection, pk=int(request.POST['school_section_id']))
    school_section_course.save()
    messages.success(request, MSG_REASSIGN_BOOK)
    return JsonResponse({'is_success': True, 'messages': None})

def delete_assigned_book(request, school_section_course_id, school_section_id):
    school_section_course = get_object_or_404(SchoolSectionCourse, pk=int(school_section_course_id))
    school_section_course.delete()
    messages.success(request, MSG_DELETE_ASSIGNED_BOOK)
    return redirect('/schedules/view_section/'+school_section_id)

@school_year_required
def sections_courses(request, school_id=None):
    context = {}
    all_school_sections = None
    school_name = None
    school_year_id = None
    
    if school_id is not None:
        school_id = int(school_id)
        if school_id == 0:
            messages.error(request, MSG_ERR_SELECT_SCHOOL)

        school = School.objects.get(pk=school_id)
        school_year_id = school.school_year.id
        school_name = school.name

        if SchoolSection.objects.filter(school=school).count() == 0:
            SchoolSection.objects.add_default_school_sections(school)
        
        all_school_sections = SchoolSection.objects.filter(school=school).order_by('year_level')
        for school_section in all_school_sections:
            school_section.courses = SchoolSectionCourse.objects.filter(school_section=school_section)
            school_section.set_total_students()

    context['school_name'] = school_name
    context['school_id'] = school_id
    context['school_year_id'] = school_year_id
    context['all_school_years'] = SchoolYear.objects.get_school_years_and_schools()
    context['all_school_sections'] = all_school_sections
    
    return schedule_render_page(request,
        page=SECTIONS_COURSES,
        context=context,
        selected_sidebar=SECTIONS_COURSES)

@school_year_required
def weekly_template(request):
    context = {}
    context['all_school_years'] = SchoolYear.objects.get_school_years_and_schools()
    return schedule_render_page(request,
                       page=WEEKLY_TEMPLATE,
                       context=context,
                       selected_sidebar=WEEKLY_TEMPLATE)

def view_template(request, school_year_id=None, school_id=None):
    if school_year_id is not None and school_id is not None:
        context = {}
        school_year = get_object_or_404(SchoolYear, pk=school_year_id)
        school = get_object_or_404(School, pk=school_id)

        templates = []
        for weekday in range(0,5):
            templates.append(TemplatePeriodTypeManager().get_template_info(school, weekday))

        context['all_sections'] = SchoolSectionManager().get_sections(school)
        context['school'] = school
        context['all_days'] = templates
        context['all_classes'] = SectionPeriod.objects.get_year_level_dropdown(school) 

        return schedule_render_page(request,
                           page=VIEW_TEMPLATE,
                           context=context,
                           selected_sidebar=WEEKLY_TEMPLATE)
    else:
        messages.error(request, MSG_ERR_SCHEDULE_INCOMPLETE)
        return redirect('/schedules/schedule_manager')

def view_section_activities(request, section_id=None):
    context = {}
    section = get_object_or_404(Section, pk=section_id)
    
    context['section'] = section
    context['all_activities'] = section.get_finished_activities_of_a_section()
    return schedule_render_page(request,
        page=VIEW_SECTION_ACTIVITIES,
        context=context,
        selected_sidebar=SECTIONS_COURSES)

def view_section(request, school_section_id=None):
    context = {}
    all_sections = None
    all_section_classes = None
    school_name = None
    year_level = None
    school_id = None
    courses = None
    next_section = 1
    is_special_needs = False

    if school_section_id is not None:
        school_section = get_object_or_404(SchoolSection, pk=school_section_id)
        school_name = school_section.school.name
        school_id = school_section.school.id
        year_level = school_section.year_level
        is_special_needs = school_section.is_special_needs
        courses = SchoolSectionCourse.objects.filter(school_section=school_section).select_related('course').order_by('course__course_name')
        for course in courses:
            course.edit_book_form = CourseDropdownForm(initial={'book':course.id})
        all_sections = Section.objects.filter(school_section=school_section).order_by('section_name')
        next_section = all_sections.count()+1
        if school_section.school.school_type != ELEMENTARY_SCHOOL:
            next_section = chr(64+next_section)
        all_section_classes = school_section.get_finished_activities_of_each_section()
    else:
        messages.error(request, MSG_ERR_SECTION_DNE)

    context['add_section_form'] = SectionForm()
    context['school_section_id'] = school_section_id
    context['next_section'] = next_section
    context['all_sections'] = all_sections
    context['all_section_classes'] = all_section_classes
    context['school_name'] = school_name
    context['year_level'] = year_level
    context['school_id'] = school_id
    context['courses'] = courses
    context['is_special_needs'] = is_special_needs
    context['assign_course_form'] = CourseDropdownForm()

    return schedule_render_page(request,
        page=VIEW_SECTION,
        context=context,
        selected_sidebar=SECTIONS_COURSES)

@require_POST
def add_section(request):
    school_section_id = get_value_of_optional_field_in_post_or_none(request, 'school_section_id')
    school_section = get_object_or_404(SchoolSection, pk=int(school_section_id)) 
    if Section.objects.filter(school_section=school_section).count() >= 8: 
        return JsonResponse({'is_success': False, 'messages': {'Error': MSG_ERR_TOO_MANY_SECTIONS}}) 

    section_name = get_value_of_optional_field_in_post_or_none(request, 'section_name')
    teacher_name = get_value_of_optional_field_in_post_or_none(request, 'teacher_name')
    student_count = get_value_of_optional_field_in_post_or_none(request, 'student_count')
    notes = get_value_of_optional_field_in_post_or_none(request, 'notes')

    new_section = Section(
        school_section=school_section,
        section_name=str(section_name),
        teacher_name=teacher_name,
        student_count=int(student_count),
        notes=notes,
    )
    new_section.save()

    all_school_sections = Section.objects.filter(school_section=school_section)
    school_section.section_count = all_school_sections.count()
    school_section.save()

    messages.success(request, MSG_ADD_SECTION)
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def update_section(request, field=None):
    primary_key = request.POST['id']
    value = request.POST['value']
    school_instance = Section.objects.filter(pk=primary_key)
    school_instance.update(**{field: value})
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def update_course(request):
    section = get_object_or_404(SchoolSection, pk=int(request.POST['id']))
    if request.POST['value'] == 0:
        return JsonResponse({'is_success': False, 'messages': {'Error': MSG_ERR_UPDATE_COURSE}})

    new_course = get_object_or_404(Course, pk=int(request.POST['value']))
    section.course = new_course
    section.save()

    return JsonResponse({'is_success': True, 'messages': None})

def delete_section(request, section_id=None):
    section = get_object_or_404(Section, pk=int(section_id))
    school_section = section.school_section

    if school_section.section_count == 1:
        messages.error(request, MSG_ERR_DELETE_LAST_SECTION)
        return redirect('/schedules/view_section/'+str(school_section.id))

    section.delete()

    remaining_sections = Section.objects.filter(school_section=school_section).order_by('section_name')
    is_elementary_school = school_section.school.school_type == ELEMENTARY_SCHOOL
    for index, section in enumerate(remaining_sections):
        if is_elementary_school:
            new_section_name = str(index+1)
        else:
            new_section_name = chr(index+65)
        section.section_name = new_section_name
        section.save()

    school_section.section_count = index+1
    school_section.save()
    messages.success(request, MSG_DELETE_SECTION)
    return redirect('/schedules/view_section/'+str(school_section.id))

@school_year_required
def school_periods(request, school_id=None):
    context = {}
    context['all_school_years'] = SchoolYear.objects.get_school_years_and_schools()
    context['add_period_form'] = SchoolPeriodTypeForm()
    school_name = None
    all_periods = None
    school_year_id = None

    if school_id != None:
        school_id = int(school_id)
        if school_id == 0:
            messages.error(request, MSG_ERR_SELECT_SCHOOL)
        else:
            school = get_object_or_404(School, pk=school_id)
            school_year_id = school.school_year.id
            all_periods = SchoolPeriodType.objects.get_periods_and_profiles(school)
            school_name = school.name

    context['school_id'] = school_id
    context['school_name'] = school_name
    context['school_year_id'] = school_year_id
    context['all_periods'] = all_periods

    return schedule_render_page(request,
        page=SCHOOL_PERIODS,
        context=context,
        selected_sidebar=SCHOOL_PERIODS)

@require_POST
def add_period_profile(request):
    context = {}
    school_id = request.POST['school_id']
    school = get_object_or_404(School, pk=school_id) 
 
    if SchoolPeriodType.objects.filter(school=school).count() >= MAX_PERIOD_PROFILES: 
        return JsonResponse({'is_success': False, 'messages': {'Error': MSG_ERR_TOO_MANY_PERIOD_PROFILES}}) 

    period_name = request.POST['period_name']
    period_type = request.POST['period_type']

    new_entry = SchoolPeriodType(
        school=school,
        period_name=period_name,
        period_type=period_type
    )
    new_entry.save()
    messages.success(request, MSG_ADD_PERIOD_PROFILE)
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def update_period_profile(request):
    period_type_id = request.POST['period_type_id']
    period_name = request.POST['period_name']
    period_type = request.POST['period_type']

    period_instance = get_object_or_404(SchoolPeriodType, pk=period_type_id)
    period_instance.period_name = period_name
    period_instance.period_type = period_type
    period_instance.save()
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def add_new_time_period(request):
    period_type_id = request.POST['period_type_id']
    period_type = get_object_or_404(SchoolPeriodType, pk=period_type_id) 
 
    if SchoolPeriod.objects.filter(school_period_type=period_type).count() >= MAX_TIME_PERIODS: 
        return JsonResponse({'is_success': False, 'messages': MSG_ERR_TOO_MANY_TIME_PERIODS}) 

    period_number = request.POST['period_number']
    start_time = request.POST['start_time']
    end_time = request.POST['end_time']

    new_school_time_period = SchoolPeriod(
        school_period_type=period_type,
        period_number=period_number,
        start_time=start_time,
        end_time=end_time
    )
    new_school_time_period.save()

    return JsonResponse({'is_success': True, 'messages': {'period_id': new_school_time_period.id}})

@require_POST
def update_period_start_time(request):
    SchoolPeriod.objects.update_period_time(
        primary_key=request.POST['id'],
        value=request.POST['value'],
        is_start_time=True)
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def update_period_end_time(request):
    SchoolPeriod.objects.update_period_time(
        primary_key=request.POST['id'],
        value=request.POST['value'],
        is_start_time=False)
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def update_period_number(request):
    primary_key = request.POST['id']
    value = request.POST['value']
    school_period_instance = get_object_or_404(SchoolPeriod, pk=primary_key)
    school_period_instance.period_number = value
    school_period_instance.save()
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def delete_period(request):
    period_id = request.POST['id']
    school_period = get_object_or_404(SchoolPeriod, pk=period_id)
    school_period.delete()
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def get_last_period(request):
    section_id = request.POST['section_id']
    date = request.POST['date']
    section = get_object_or_404(Section, pk=section_id)

    last_hour = SectionPeriod.objects.get_last_lesson_hour(section, date)
    if last_hour is not None:
        return JsonResponse({'is_success': True, 'messages': {'lesson': last_hour.lesson_number, 'hour': last_hour.hour_number, 'date': last_hour.date}})
    else:
        return JsonResponse({'is_success': True, 'messages': {'lesson': 0, 'hour': 0, 'date': None}})

@require_POST
def add_template_class(request):
    weekday = int(request.POST['weekday'])
    school_period = get_object_or_404(SchoolPeriod, pk=int(request.POST['school_period_id']))
    section = get_object_or_404(Section, pk=int(request.POST['section']))

    new_template_section_period = TemplateSectionPeriod(
        weekday=weekday,
        school_period=school_period,
        section=section
    )
    new_template_section_period.save()

    return JsonResponse({'is_success': True, 'messages': 'The class has been successfully added to the template'})


@require_POST
def edit_template_class(request):
    template_section_period = get_object_or_404(TemplateSectionPeriod, pk=int(request.POST['template_section_period_id']))
    template_section_period.section = get_object_or_404(Section, pk=int(request.POST['section_id']))
    template_section_period.save()
    return JsonResponse({'is_success': True, 'messages': 'The class has been successfully edited.'})

@require_POST
def delete_template_class(request, template_section_period_id):
    template_section_period = get_object_or_404(TemplateSectionPeriod, pk=int(template_section_period_id))
    template_section_period.delete()
    messages.success(request, MSG_DELETE_CLASS)
    return JsonResponse({'is_success': True, 'messages': None})

def add_from_template(request, section_period_type_id):
    section_period_type = get_object_or_404(SectionPeriodType, pk=int(section_period_type_id))
    section_period_date = section_period_type.date
    weekday = section_period_date.weekday()
    school = section_period_type.school

    template_period_type = TemplatePeriodType.objects.filter(weekday=weekday, school=school).first()
    school_periods = SchoolPeriod.objects.filter(school_period_type=template_period_type.school_period_type)
    are_classes_empty = True

    for school_period in school_periods:
        template_section_period = TemplateSectionPeriod.objects.filter(weekday=weekday, school_period=school_period).first()
        next_lesson_plan = None
        next_lesson_number = 1
        next_hour_number = 1

        if template_section_period is not None:
            are_classes_empty = False
            is_default_lesson_plan = True
            last_class_held = SectionPeriod.objects.filter(section=template_section_period.section).last()

            if last_class_held:
                lesson_number = last_class_held.lesson_number
                hour_number = last_class_held.hour_number
                next_lesson_number = lesson_number
                course = None

                if last_class_held.lesson_plan.lesson is not None:
                    course = last_class_held.lesson_plan.lesson.course

                if course is not None:
                    next_hour_number = hour_number + 1
                    print(last_class_held, next_hour_number)
                    next_lesson_plan = LessonPlan.objects.filter(lesson__course=course, lesson__lesson_number=lesson_number, hour_number=next_hour_number, is_premade_lesson_plan=True).first()

                    if next_lesson_plan is None:
                        next_lesson_number = lesson_number + 1
                        next_hour_number = 1
                        next_lesson_plan = LessonPlan.objects.filter(lesson__course=course, lesson__lesson_number=next_lesson_number, hour_number=1, is_premade_lesson_plan=True).first()

            if next_lesson_plan is None:
                next_lesson_plan = LessonPlan(
                    lesson=None,
                    hour_number=1,
                    greeting=None,
                    warmup=None,
                    presentation=None,
                    practice=None,
                    production=None,
                    cooldown=None,
                    assessment=None,
                    is_premade_lesson_plan=False,
                )

            next_lesson_plan.is_premade_lesson_plan = False            
            next_lesson_plan.pk = None
            next_lesson_plan.save()

            new_section_period = SectionPeriod(
                date=section_period_date,
                section=template_section_period.section,
                school_period=school_period,
                lesson_plan=next_lesson_plan,
                lesson_number=next_lesson_number,
                hour_number=next_hour_number,
                notes='',
            )
            new_section_period.save()

    if are_classes_empty:
        messages.error(request, "There are no classes in the template.")
    else:
        messages.success(request, "The classes have been added from the template.")
    return JsonResponse({'is_success': True, 'messages': None})