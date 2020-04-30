import time, os
import selenium, random
from lessons.models import *
from paw.constants.tests import *
from paw.constants.models import *
from lessons.constants import *
from datetime import datetime, timedelta
from selenium.webdriver.common.keys import Keys
from home.tests.tests import HomeTestMethods
from selenium.webdriver.common.action_chains import ActionChains

class DashboardTestCases(HomeTestMethods):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    # Actions
    def __download_lesson_plan_today(self):
        button = self.browser.find_element_by_class_name('btn-primary')
        button.click()
        time.sleep(MODAL_TRANSITION_WAIT_TIME)

    def __download_weekly_lesson_plan(self):
        button = self.browser.find_element_by_class_name('btn-print-week')
        button.click()
        time.sleep(MODAL_TRANSITION_WAIT_TIME)

    def __go_to_lesson_plan(self):
        button = self.browser.find_element_by_class_name('btn-smaller')
        button.click()
        time.sleep(PAGE_LOADING_WAIT_TIME)

    # Assertions
    def __assert_no_classes(self):
        current_date = datetime.now()
        tomorrow = datetime.now() + timedelta(days=1)
        content = self.browser.find_element_by_id('paw-main-content').text
        self.assertIn('Today, %s %s %s'%(current_date.strftime('%B'), current_date.strftime('%e').strip(), current_date.strftime('(%a)')), content)
        self.assertIn('Tomorrow, %s %s %s'%(tomorrow.strftime('%B'), tomorrow.strftime('%e').strip(), tomorrow.strftime('(%a)')), content)
        for i in range(0, 7):
            date = current_date + timedelta(days=i)
            month = int(date.strftime('%m'))
            day = int(date.strftime('%d'))
            self.assertIn('%d/%d'%(month, day), content)

    def __assert_day_existence(self, materials, activities, sections):
        content = self.browser.find_element_by_id('paw-main-content').text
        self.assertIn(materials, content)
        self.assertIn(activities, content)
        for section in sections:
            self.assertIn('%s %s'%(section['section_name'], section['lesson_name']), content)

    def __assert_schedule_week(self):
        content = self.browser.find_element_by_id('paw-main-content').text
        current_date = datetime.now()
        for i in range(0,7):
            scheduled_date = current_date + timedelta(days=i)
            period_type = 'Normal Schedule'
            weekday = scheduled_date.weekday()
            if weekday == 0: # Monday
                period_type = 'Monday Schedule'
            elif weekday == 2: # Wednesday
                period_type = 'Wednesday Schedule'
            month = int(scheduled_date.strftime('%m'))
            day = int(scheduled_date.strftime('%d'))
            self.assertIn('%d/%d\n%s Dolphin Elementary School\n%s\n4-1\n4-2\n4-3'%(month, day, scheduled_date.strftime('%a'), period_type), content)

    # Tests
    # python3 manage.py test home.tests.test_dashboard.DashboardTestCases.test_dashboard_display
    def test_dashboard_display(self):
        super().go_to_dashboard()
        self.__assert_no_classes()

    def test_404(self):
        super().go_to_404_page()
    
    def test_500(self):
        super().go_to_500_page()

    def test_filled_dashboard_today_tomorrow(self):
        super().go_to_dashboard_with_classes_for_today_and_tomorrow()
        self.__assert_day_existence(
            materials='CD, Ohajiki Marbles, Cats', 
            activities='Hello Song; Rainbow Song; Vocabulary Drilling; Keyword Game; Interview Game; Signature Count; Vocabulary Volunteer', 
            sections=[{
                    'section_name': '3-1',
                    'lesson_name': 'Lesson 1, Hour 1'
                }, {
                    'section_name': '3-2',
                    'lesson_name': 'Lesson 1, Hour 1'
                }
            ])
        self.__assert_day_existence(
            materials='CD, Ohajiki Marbles, Cats', 
            activities='Hello Song; Rainbow Song; Vocabulary Drilling; Keyword Game; Interview Game; Signature Count; Vocabulary Volunteer', 
            sections=[{
                    'section_name': '2-A',
                    'lesson_name': 'Lesson 1, Hour 1'
                }, {
                    'section_name': '2-B',
                    'lesson_name': 'Lesson 1, Hour 1'
                }
            ])

    def test_filled_dashboard_week(self):
        super().go_to_dashboard_with_classes_for_the_week()
        self.__assert_schedule_week()

    def test_print_schedule_today(self):
        super().go_to_dashboard_with_classes_for_the_week()
        self.__download_lesson_plan_today()
        super().assert_download_did_not_fail()

    def test_print_schedule_week(self):
        super().go_to_dashboard_with_classes_for_the_week()
        self.__download_weekly_lesson_plan()
        super().assert_download_did_not_fail()

    def test_view_lesson_plan(self):
        super().go_to_dashboard_with_classes_for_the_week()
        self.__go_to_lesson_plan()
        
        content = self.browser.find_element_by_id('paw-main-content').text
        self.assertIn("Dolphin Elementary School, Class 4-1", content)
        self.assertIn("Let's Try 1, Lesson 1, Hour 1", content)

    def test_alt_meeting_work_day(self):
        super().go_to_dashboard_with_alt_meeting_work_day()
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        content = self.browser.find_element_by_id('paw-main-content').text
        self.assertIn('Today, %s %s %s ALT Meeting'%(today.strftime('%B'), today.strftime('%e').strip(), today.strftime('(%a)')), content)
        self.assertIn('Tomorrow, %s %s %s Work day'%(tomorrow.strftime('%B'), tomorrow.strftime('%e').strip(), tomorrow.strftime('(%a)')), content)

    # python3 manage.py test home.tests.test_dashboard.DashboardTestCases.test_check_in_out
    def test_check_in_out(self):
        today = datetime.now()
        weekday = today.weekday()
        hour = today.hour
        is_check_in = hour < 9

        if weekday in [1, 3]:
            self.browser.get('%s' % ('https://forms.gle/7qBeDGS6thm4DyTbA'))

            # First page
            # Email address
            time.sleep(2)
            element = self.browser.find_element_by_css_selector('input')
            element.send_keys('kiefer.yap@interacmail.com')
            print("First page: entered the name")

            # Go to next page
            time.sleep(0.5)
            button = self.browser.find_element_by_css_selector('span.appsMaterialWizButtonPaperbuttonLabel')
            button.click()
            print("First page: clicked the Next button")

            # Second page
            time.sleep(1)
            dropdown = self.browser.find_element_by_css_selector('.quantumWizMenuPaperselectOptionList')
            dropdown.click()

            time.sleep(0.5)
            actions = ActionChains(self.browser) 
            actions.send_keys(Keys.DOWN)
            actions.perform()
            
            time.sleep(0.5)
            actions = ActionChains(self.browser) 
            actions.send_keys(Keys.DOWN)
            actions.perform()

            time.sleep(0.5)
            actions.send_keys(Keys.ENTER)
            actions.perform()
            print("Second page: completed the dropdown")

            time.sleep(0.5)
            actions = ActionChains(self.browser)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.SPACE)
            actions.perform()
            print("Second page: clicked the Next button")

            # Third page
            time.sleep(1)
            dropdown = self.browser.find_element_by_css_selector('.quantumWizMenuPaperselectOptionList')
            dropdown.click()

            time.sleep(0.5)
            actions = ActionChains(self.browser) 
            actions.send_keys(Keys.DOWN)
            actions.perform()
            time_hour = '8'
            time_minute = '00'

            if not is_check_in:
                time.sleep(0.5)
                actions.send_keys(Keys.DOWN)
                actions.perform()
                time_hour = '15'
                time_minute = '20'

            time.sleep(0.5)
            actions.send_keys(Keys.ENTER)
            actions.perform()
            print("Third page: completed the dropdown")

            time.sleep(0.5)
            actions = ActionChains(self.browser)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.SPACE)
            actions.perform()
            print("Third page: clicked the Next button")

            # Page 4: Enter the time
            time.sleep(2)
            actions = ActionChains(self.browser)
            actions.send_keys(Keys.TAB)
            actions.send_keys(time_hour)
            actions.send_keys(Keys.TAB)
            actions.send_keys(time_minute)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.SPACE)
            actions.perform()
            print("Fourth page: entered the time and clicked the next button")

            if is_check_in:
                time.sleep(2)
                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)
                print("Fifth page: completed all checkboces")

            # Page 5: Submit button
            time.sleep(1)
            actions = ActionChains(self.browser)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.SPACE)
            actions.perform()
            print("Last page: completed")

            time.sleep(500)
        

    # python3 manage.py test home.tests.test_dashboard.DashboardTestCases.test_cron_health_check
    def test_cron_health_check(self):
        # today = datetime.now() + timedelta(hours=9)
        today = datetime.now()
        weekday = today.weekday()

        # time.sleep(random.randrange(8)+3)

        # Login
        # self.browser.get('%s' % ('https://mail.google.com'))
        
        # self.browser.set_window_size(1920,1080)
        # element = self.browser.find_element_by_css_selector('input')
        # element.send_keys('kiefer.yap@interacmail.com')
        # element.send_keys(Keys.ENTER)

        # self.browser.implicitly_wait(5)
        # time.sleep(5)
        # element = self.browser.find_element_by_css_selector('input[type=password]')
        # element.send_keys('dragonite123test')
        # element.send_keys(Keys.ENTER)
        # self.browser.implicitly_wait(5)
        # time.sleep(5)
        
        if weekday < 5:
            self.browser.get('%s' % ('https://forms.gle/3bKtcvcSnabo3KGn6'))

            # First page
            # Email address
            time.sleep(2)
            element = self.browser.find_element_by_css_selector('input')
            element.send_keys('kiefer.yap@interacmail.com')
            print("First page: entered the name")

            # Go to next page
            time.sleep(0.5)
            button = self.browser.find_element_by_css_selector('span.appsMaterialWizButtonPaperbuttonLabel')
            button.click()
            print("First page: clicked the Next button")

            # Second page
            time.sleep(0.5)
            actions = ActionChains(self.browser) 
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.TAB)
            temperature = ['35.7', '35.8', '35.9', '36.0', '36.1', '36.2']
            temptext = str(temperature[random.randrange(6)])
            actions.send_keys(temptext)

            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.SPACE)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.SPACE)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.SPACE)

            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.SPACE)
            actions.perform()
            print("Second page: performed actions for temperature and the triple checkbox.")

            time.sleep(1)

            dropdown = self.browser.find_element_by_css_selector('.quantumWizMenuPaperselectOptionList')
            dropdown.click()

            time.sleep(0.5)
            actions = ActionChains(self.browser) 
            actions.send_keys(Keys.DOWN)
            actions.perform()
            
            if weekday in [1, 3]: # Tuesdays/Thursdays
                time.sleep(0.5)
                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.DOWN)
                actions.perform()

            time.sleep(0.5)
            actions.send_keys(Keys.ENTER)
            actions.perform()
            print("Second page: completed the dropdown")

            time.sleep(0.5)
            actions = ActionChains(self.browser)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.SPACE)
            actions.perform()
            print("Second page: clicked the Next button")

            # Page 4: Workday
            if weekday in [1, 3]:
                # Page 3: First confirmation
                time.sleep(1)
                dropdown = self.browser.find_element_by_css_selector('.quantumWizMenuPaperselectOptionList')
                dropdown.click()

                time.sleep(0.5)
                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.DOWN)
                actions.perform()

                time.sleep(0.5)
                actions.send_keys(Keys.ENTER)
                actions.perform()
                print("Third page: completed the dropdown")

                time.sleep(0.5)
                actions = ActionChains(self.browser)
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                print("Third page: clicked the Next button")

                time.sleep(2)
                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)

                actions = ActionChains(self.browser) 
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.TAB)
                actions.send_keys(Keys.SPACE)
                actions.perform()
                time.sleep(0.5)
                print("Fourth page: completed all checkboces")

            # Page 4
            time.sleep(3)
            actions = ActionChains(self.browser) 
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.TAB)
            actions.send_keys(Keys.SPACE)
            actions.perform()

            # Recaptcha
            time.sleep(8)
            
            from PIL import Image
            import io
            from io import BytesIO
            from os.path import expanduser

            # Crop image
            element = self.browser.find_element_by_css_selector('iframe[title="recaptcha challenge"]')
            location = element.location
            size = element.size

            left = int(location['x'])
            top = int(location['y'])
            right = int(location['x'] + size['width'])
            bottom = int(location['y'] + size['height'])

            screenshot_png = self.browser.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot_png))
            image = image.crop((left, top, right, bottom))
            image = image.copy()
            image_file = io.BytesIO()
            image.save(image_file, "PNG")
            image_file.seek(0)

            path  = expanduser('~/')
            image.save(path + 'F1-info.png')

            # Send image to captcha-busting service
            from home.tests.dbc import deathbycaptcha

            username = "keeperaft"
            password = "testDragonite456"
            client = deathbycaptcha.SocketClient(username, password)

            try:
                balance = client.get_balance()
                print("Balance", balance)
            except deathbycaptcha.AccessDeniedException:
                print("Access denied")
                # Access to DBC API denied, check your credentials and/or balance


            # captcha = client.decode(image_file, timeout)
            # time.sleep(20)
            # print(client.get_balance(), captcha, "<<<<")

            print("Last page: Tab-Tab-Space. Not sure if the captcha came out though, so check your mail.")
            
            time.sleep(500)


