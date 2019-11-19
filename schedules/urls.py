from schedules.constants import *
from paw.methods import Url
from . import views

app_name = 'schedules'
urlpatterns = []
url_manager = Url(urlpatterns, views)

url_manager.add_url(EXPRESSION_INDEX, INDEX)
url_manager.add_url(EXPRESSION_ADD_CLASS, ADD_CLASS)
url_manager.add_url(EXPRESSION_EDIT_CLASS, EDIT_CLASS)
url_manager.add_url(EXPRESSION_ADD_SECTION, ADD_SECTION)
url_manager.add_url(EXPRESSION_ASSIGN_BOOK, ASSIGN_BOOK)
url_manager.add_url(EXPRESSION_VIEW_SECTION, VIEW_SECTION)
url_manager.add_url(EXPRESSION_DELETE_CLASS, DELETE_CLASS)
url_manager.add_url(EXPRESSION_REASSIGN_BOOK, REASSIGN_BOOK)
url_manager.add_url(EXPRESSION_VIEW_SCHEDULE, VIEW_SCHEDULE)
url_manager.add_url(EXPRESSION_DELETE_PERIOD, DELETE_PERIOD)
url_manager.add_url(EXPRESSION_UPDATE_COURSE, UPDATE_COURSE)
url_manager.add_url(EXPRESSION_UPDATE_SECTION, UPDATE_SECTION)
url_manager.add_url(EXPRESSION_DELETE_SECTION, DELETE_SECTION)
url_manager.add_url(EXPRESSION_SCHOOL_PERIODS, SCHOOL_PERIODS)
url_manager.add_url(EXPRESSION_ADD_ALL_CLASSES, ADD_ALL_CLASSES)
url_manager.add_url(EXPRESSION_GET_LAST_PERIOD, GET_LAST_PERIOD)
url_manager.add_url(EXPRESSION_EDIT_LESSON_HOUR, EDIT_LESSON_HOUR)
url_manager.add_url(EXPRESSION_SECTIONS_COURSES, SECTIONS_COURSES)
url_manager.add_url(EXPRESSION_ADD_PERIOD_PROFILE, ADD_PERIOD_PROFILE)
url_manager.add_url(EXPRESSION_SCHOOL_PERIOD_SCHOOL_ID, SCHOOL_PERIODS)
url_manager.add_url(EXPRESSION_VIEW_SECTION_PERIOD, VIEW_SECTION_PERIOD)
url_manager.add_url(EXPRESSION_ADD_NEW_TIME_PERIOD, ADD_NEW_TIME_PERIOD)
url_manager.add_url(EXPRESSION_DELETE_ASSIGNED_BOOK, DELETE_ASSIGNED_BOOK)
url_manager.add_url(EXPRESSION_UPDATE_PERIOD_NUMBER, UPDATE_PERIOD_NUMBER)
url_manager.add_url(EXPRESSION_SECTIONS_COURSES_SCHOOL_ID, SECTIONS_COURSES)
url_manager.add_url(EXPRESSION_UPDATE_PERIOD_PROFILE, UPDATE_PERIOD_PROFILE)
url_manager.add_url(EXPRESSION_UPDATE_PERIOD_END_TIME, UPDATE_PERIOD_END_TIME)
url_manager.add_url(EXPRESSION_VIEW_SECTION_ACTIVITIES, VIEW_SECTION_ACTIVITIES)
url_manager.add_url(EXPRESSION_UPDATE_PERIOD_START_TIME, UPDATE_PERIOD_START_TIME)
url_manager.add_url(EXPRESSION_EDIT_SCHEDULE_PERIOD_PROFILE, EDIT_SCHEDULE_PERIOD_PROFILE)
url_manager.add_url(EXPRESSION_SCHEDULE_MANAGER, SCHEDULE_MANAGER, method_name=INDEX)
