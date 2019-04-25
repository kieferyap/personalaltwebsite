from home.constants import *
from paw.methods import Url
from . import views

app_name = 'home'
urlpatterns = []
url_manager = Url(urlpatterns, views)

url_manager.add_url(EXPRESSION_INDEX, INDEX)
url_manager.add_url(EXPRESSION_PRINT_DAY, PRINT_DAY)
url_manager.add_url(EXPRESSION_PRINT_WEEK, PRINT_WEEK)
url_manager.add_url(EXPRESSION_INDEX_BASE, INDEX)
url_manager.add_url(EXPRESSION_SIGNUP, SIGNUP)
url_manager.add_url(EXPRESSION_DASHBOARD, INDEX)
url_manager.add_url(EXPRESSION_REIMBURSEMENTS, REIMBURSEMENTS)
url_manager.add_url(EXPRESSION_CHECK_REIMBURSEMENTS, CHECK_REIMBURSEMENTS)
url_manager.add_url(EXPRESSION_TIMESHEETS, TIMESHEETS)
url_manager.add_url(EXPRESSION_SETTINGS, SETTINGS)
url_manager.add_url(EXPRESSION_UPDATE_PROFILE, UPDATE_PROFILE)
url_manager.add_url(EXPRESSION_LOGIN, LOGIN, method_name=LOGIN_VIEW)
url_manager.add_url(EXPRESSION_LOGOUT, LOGOUT, method_name=LOGOUT_VIEW)
url_manager.add_url(EXPRESSION_ABOUT, ABOUT)
url_manager.add_url(EXPRESSION_SERVER_ERROR, TEST_SERVER_ERROR)
url_manager.add_url(EXPRESSION_LANGUAGE, LANGUAGE)
url_manager.add_url(EXPRESSION_GENERATE_TIMESHEET_PDF, GENERATE_TIMESHEET_PDF)
url_manager.add_url(EXPRESSION_CHANGE_PASSWORD, CHANGE_PASSWORD)
url_manager.add_url(EXPRESSION_UPDATE_TIMESHEET_FIELDS, UPDATE_TIMESHEET_FIELDS)
