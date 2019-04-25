import calendar
from collections import OrderedDict
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST

from home.constants import *
from home.models import *
from paw.constants.base import *

from home.pdf import print_timesheet_pdf, print_day_pdf, print_week_pdf
from paw.constants.base import MODAL_ID
from paw.constants.base import NAME, URL, IS_SELECTED, HOME
from paw.methods import render_page, school_year_required
from schoolyears.models import SchoolYear, YearlySchedule, SchoolRoute


def home_render_page(request,
                     page='index',
                     context={},
                     selected_sidebar=DASHBOARD):
    dashboard = {
        NAME: NAME_DASHBOARD,
        URL: DASHBOARD,
        IS_SELECTED: False,
        MODAL_ID: None,
    }
    timesheets = {
        NAME: NAME_TIMESHEETS,
        URL: TIMESHEETS,
        IS_SELECTED: False,
        MODAL_ID: None,
    }

    if request.user.is_superuser:
        reimbursements = {
            NAME: NAME_REIMBURSEMENTS,
            URL: REIMBURSEMENTS,
            IS_SELECTED: False,
            MODAL_ID: None,
        }

    settings = {
        NAME: NAME_SETTINGS,
        URL: SETTINGS,
        IS_SELECTED: False,
        MODAL_ID: None,
    }
    about = {
        NAME: NAME_ABOUT,
        URL: ABOUT,
        IS_SELECTED: False,
        MODAL_ID: None,
    }

    sidebar = OrderedDict()
    sidebar[DASHBOARD] = dashboard
    sidebar[TIMESHEETS] = timesheets
    if request.user.is_superuser:
        sidebar[REIMBURSEMENTS] = reimbursements
    sidebar[SETTINGS] = settings
    sidebar[ABOUT] = about
    sidebar[selected_sidebar][IS_SELECTED] = True

    return render_page(request,
                       page,
                       context,
                       sidebar=sidebar,
                       selected_menu=HOME)

def index(request):
    context = {}
    # Get today's info: school, period type, classes, materials
    today = YearlySchedule.objects.get_schedule_information_for_day(datetime.now())

    # Get the next work day's info: school, period type, classes, materials
    tomorrow = YearlySchedule.objects.get_schedule_information_for_day(datetime.now() + timedelta(days=1))
    
    # Get this week's info: schools (+ALT Meeting), period types, classes
    week = []
    for i in range(0, 7):
        week.append(YearlySchedule.objects.get_schedule_information_for_day(datetime.now() + timedelta(days=i)))
    
    context['today'] = today
    context['tomorrow'] = tomorrow
    context['week'] = week

    return home_render_page(request,
                       page='index',
                       context=context,
                       selected_sidebar=DASHBOARD)

def print_day(request):
    return print_day_pdf(request.POST['date'])
    
def print_week(request):
    return print_week_pdf(request.POST['date'])

@school_year_required
def timesheets(request):
    context = {}

    # Hardcode the timesheet details... for now: 
    # Employee code, ALT name, BOE, Person in charge of sales, Interac Fax and Telephone
    user = OrderedDict()
    user_profile = Profile.objects.get(user=request.user)
    user['LC Code'] = {'id': user_profile.id, 
        'database_key': 'employee_code', 
        'value': user_profile.employee_code
    }
    user['ALT Name'] = {'id': user_profile.id, 
        'database_key': 'alt_name', 
        'value': user_profile.alt_name
    }
    user['Board of Education'] = {'id': user_profile.id, 
        'database_key': 'board_of_education', 
        'value': user_profile.board_of_education
    }
    user['Person in charge of sales'] = {'id': user_profile.id, 
        'database_key': 'sales_person', 
        'value': user_profile.sales_person
    }
    user['Fax'] = {'id': user_profile.id, 
        'database_key': 'fax', 
        'value': user_profile.fax
    }
    user['Telephone'] = {'id': user_profile.id, 
        'database_key': 'telephone', 
        'value': user_profile.telephone
    }

    context['all_school_years'] = SchoolYear.objects.get_school_years_and_schools()
    context['user_info'] = user

    return home_render_page(request,
                       page=TIMESHEETS,
                       context=context,
                       selected_sidebar=TIMESHEETS)

@school_year_required
def reimbursements(request):
    context = {}
    context['all_school_years'] = SchoolYear.objects.order_by('is_active', 'start_date').reverse()
    return home_render_page(request,
                       page=REIMBURSEMENTS,
                       context=context,
                       selected_sidebar=REIMBURSEMENTS)


@require_POST
def check_reimbursements(request):
    school_year_id = request.POST['school-year']
    school_year = SchoolYear.objects.get(id=school_year_id)
    route_choices = SchoolRoute.objects.filter(school_year=school_year)

    if route_choices.count() == 0:
        messages.error(request, MSG_ERR_NO_ROUTES_AVAILABLE)
        return redirect('/reimbursements')

    context = {}
    all_routes = []

    # Get amount of days per month
    month_raw = request.POST['month']
    month_array = month_raw.split('-', 1)
    year = int(month_array[0])
    month = int(month_array[1])
    day_count = calendar.monthrange(year, month)
    day = 0
    total_cost = 0

    # Per day, look for schedule entries and append them
    for day_index in range(day_count[1]): # day_count[0] is the weekday of the first day
        day += 1
        datetime_object = datetime.strptime(str(year)+'-'+str(month)+'-'+str(day), "%Y-%m-%d")

        all_routes.append({
            'date': datetime_object, 
            'routes': SchoolRoute.objects.get_all_routes_of_day_with_school_year(
                datetime_object=datetime_object,
                school_year=school_year
            )
        })

    profile_instance = Profile.objects.filter(user=request.user).values('interac_email')
    context['interac_email'] = profile_instance[0]['interac_email']
    context['selected_year'] = year
    context['selected_month_name'] = calendar.month_name[month]
    context['selected_month'] = month
    context['all_routes'] = all_routes
    context['total_cost'] = total_cost
    context['route_choices'] = route_choices

    return home_render_page(request,
                       page=CHECK_REIMBURSEMENTS,
                       context=context,
                       selected_sidebar=REIMBURSEMENTS)

def settings(request):
    context = {}
    context['user_profile'] = Profile.objects.get(user=request.user)
    context['password_change_form'] = PasswordChangeForm(request.user)

    return home_render_page(request,
       page=SETTINGS,
       context=context,
       selected_sidebar=SETTINGS)

def update_timesheet_fields(request):
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def generate_timesheet_pdf(request):
    return print_timesheet_pdf(request)

def about(request):
    return home_render_page(request,
        page='about',
        context={},
        selected_sidebar=ABOUT)

def language(request, language_id):
    valid_languages = ['en', 'ja']
    if language_id in valid_languages:
        request.session[LANGUAGE_SESSION_KEY] = language_id
        return HttpResponse('success')
    return HttpResponse('failure')

def __render_error_page(request, page, status):
    # Menus
    context = {}
    home = {
        NAME: NAME_HOME,
        URL: INDEX,
        IS_SELECTED: False,
    }
    school_years = {
        NAME: NAME_SCHOOL_YEARS,
        URL: SCHOOL_YEARS,
        IS_SELECTED: False,
    }

    lessons = {
        NAME: NAME_LESSONS,
        URL: LESSONS,
        IS_SELECTED: False,
    }

    schedules = {
        NAME: NAME_SCHEDULES,
        URL: SCHEDULES,
        IS_SELECTED: False,
    }

    # Build the menus and the submenus
    context[MENU] = OrderedDict()
    context[MENU][HOME] = home
    context[MENU][SCHEDULES] = schedules
    context[MENU][LESSONS] = lessons
    context[MENU][SCHOOL_YEARS] = school_years
    
    context[MENU][HOME][IS_SELECTED] = True
    context[SIDEBAR] = {}

    return render(request, page, context, status)

def test_server_error(request):
    print(unnamed_var)

def server_error(request):
    return __render_error_page(request, page='500.html', status=500)

def page_not_found(request):
    return __render_error_page(request, page='404.html', status=404)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, MSG_LOGIN_SUCCESS)
        else:
            messages.error(request, MSG_LOGIN_FAILURE)
    return redirect('/index')

def logout_view(request):
    logout(request)
    messages.success(request, MSG_LOGOUT_SUCCESS)
    return redirect('/index')

def signup(request):
    # Remove details after use
    username = ''
    email = ''
    password = ''
    user = User.objects.create_user(username, email, password)
    user.save()
    messages.success(request, _('A new user with the username %s has been successfully created.'%(username)))
    
    return redirect('/index')

@require_POST
def update_profile(request, field=None):
    primary_key = request.POST['id']
    value = request.POST['value']
    profile_instance = Profile.objects.filter(pk=primary_key)
    profile_instance.update(**{field: value})
    return JsonResponse({'is_success': True, 'messages': None})

@require_POST
def change_password(request):
    context = {}
    form = PasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user) 
        messages.success(request, MSG_CHANGE_PASSWORD_SUCCESS)
    else:
        messages.error(request, MSG_CHANGE_PASSWORD_FAILURE)

    context['user_profile'] = Profile.objects.get(user=request.user)
    context['password_change_form'] = PasswordChangeForm(request.user)

    return home_render_page(request,
       page=SETTINGS,
       context=context,
       selected_sidebar=SETTINGS)

