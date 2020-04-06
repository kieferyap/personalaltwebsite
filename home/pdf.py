import calendar
import datetime as dt
import math
import os
from collections import OrderedDict
from datetime import datetime, timedelta

import reportlab
from PIL import Image
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.contrib.staticfiles.templatetags.staticfiles import static
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame, KeepInFrame, SimpleDocTemplate, Table, Spacer, TableStyle, PageBreak, KeepTogether
from reportlab.platypus.flowables import HRFlowable


from lessons.constants import PORTRAIT, FRONT_BACK, PICTURE_LABEL, PICTURE_ONLY, TARGET_LANGUAGE_BLUE
from lessons.models import LessonPlan, FlashcardLesson, TargetLanguage
from schoolyears.constants import KEY_MTG
from schoolyears.models import SchoolYear, School, SpecialYearlySchedule, YearlySchedule


def print_lesson_plan_pdf(lesson_plan_id):
    styles = __prepare_styles_and_font()

    lesson_plan = get_object_or_404(LessonPlan, pk=lesson_plan_id)
    lesson_plan_info = lesson_plan.get_all_info_from_all_activities()

    handouts_raw = lesson_plan_info['handouts']
    handouts_string = ''
    handout_index = 0
    handout_count = len(handouts_raw)

    for handout in handouts_raw:
        handouts_string += handout['filename']
        if handout_index < handout_count - 1:
            handout_index += 1
            handouts_string += ', '

    flashcards_raw = lesson_plan_info['flashcards']
    flashcards_arr = []

    for flashcard in flashcards_raw:
        flashcards_arr.append(flashcard['flashcard'])

    book = None
    course_code = None
    lesson_number = None
    hour_number = None
    if lesson_plan.lesson is not None:
        book = lesson_plan.lesson.course.course_name
        course_code = lesson_plan.lesson.course.course_code
        lesson_number = lesson_plan.lesson.lesson_number
        hour_number = lesson_plan.hour_number

    lesson_plan = {
        'materials': ', '.join(lesson_plan_info['materials']),
        'flashcards': ', '.join(flashcards_arr),
        'handouts': handouts_string,
        'greeting': lesson_plan.greeting,
        'warmup': lesson_plan.warmup,
        'presentation': lesson_plan.presentation,
        'practice': lesson_plan.practice,
        'production': lesson_plan.production,
        'cooldown': lesson_plan.cooldown,
        'assessment': lesson_plan.assessment,
        'book': book,
        'course_code': course_code,
        'lesson_number': lesson_number,
        'hour_number': hour_number,
    }

    filename = 'lesson-plan.pdf'
    if course_code:
        filename = 'lesson-plan-%s-lesson-%d-hour-%d.pdf' % (slugify(lesson_plan['course_code']), lesson_plan['lesson_number'], lesson_plan['hour_number'])
    
    document = SimpleDocTemplate('/tmp/%s' % (filename), leftMargin=25, rightMargin=25, topMargin=30, bottomMargin=30)
    story = []

    # Lesson Plan Header
    lesson_plan_header = 'Lesson Plan'
    if book and lesson_number and hour_number:
        lesson_plan_header = 'Lesson Plan for %s, Lesson %d, Hour %d' % (lesson_plan['book'], lesson_plan['lesson_number'], lesson_plan['hour_number'])
    story.append(Paragraph(lesson_plan_header, styles['header-left']))   
    story.append(Spacer(1,12))
    story.append(HRFlowable(color=colors.black, width="100%"))

    __print_lesson_plan_contents(story, lesson_plan, styles)
    document.build(story)
    
    return __generate_pdf_download(filename)

def download_flashcard_pdf(flashcard, picture=None):
    (pdf_object, response) = __generate_pdf_object_and_response(filename=slugify('flashcard-'+flashcard.label.lower()))
    picture = ImageReader(Image.open(picture)) if picture is not None else None
    __print_flashcard(pdf_object, flashcard, picture)
    pdf_object.save()
    return response

def download_all_flashcards_pdf(lesson):
    (pdf_object, response) = __generate_pdf_object_and_response(filename=slugify('flashcard-lesson-'+str(lesson.lesson_number)))

    flashcard_lessons = FlashcardLesson.objects.filter(lesson=lesson).order_by('flashcard__label')
    for flashcard_lesson in flashcard_lessons:
        __print_flashcard(pdf_object, flashcard_lesson.flashcard)
    pdf_object.save()
 
    return response

def download_target_language_pdf(target_language, does_lesson_exist=True):
    (pdf_object, response) = __generate_pdf_object_and_response(filename=slugify('target-language-'+str(target_language.target_language)))
    __print_target_language(pdf_object, target_language, does_lesson_exist)
    pdf_object.save()
    return response

def download_all_target_languages_pdf(lesson):
    (pdf_object, response) = __generate_pdf_object_and_response(filename=slugify('target-language-lesson-'+str(lesson.lesson_number)))

    target_languages = TargetLanguage.objects.filter(lesson=lesson).order_by('target_language')
    for target_language in target_languages:
        __print_target_language(pdf_object, target_language)
    pdf_object.save()

    return response

def print_day_pdf(date_string):
    filename = slugify('class-schedule-'+date_string)+'.pdf'
    document = SimpleDocTemplate('/tmp/%s' % (filename), leftMargin=25, rightMargin=25, topMargin=30, bottomMargin=30)
    
    story = []
    __print_date(date_string, story)
    document.build(story)
    return __generate_pdf_download(filename)

def print_week_pdf(start_date_string):
    datetime_object = datetime.strptime(start_date_string, '%Y-%m-%d')
    filename = slugify('weekly-class-schedule-'+start_date_string)+'.pdf'
    document = SimpleDocTemplate('/tmp/%s' % (filename), leftMargin=25, rightMargin=25, topMargin=30, bottomMargin=30)

    story = []
    for i in range(0,7):
        new_datetime_object = datetime_object + timedelta(days=i)
        new_date_string = new_datetime_object.strftime('%Y-%m-%d')
        __print_date(new_date_string, story)
    document.build(story)

    return __generate_pdf_download(filename)
    
def print_timesheet_pdf(request):
    # Get relevant date and school information
    start_date = request.POST['start-date']
    end_date = request.POST['end-date']
    school_year_id = int(request.POST['school-year'])
    school_id = int(request.POST['school'])        
    school_year = SchoolYear.objects.get(id=school_year_id)

    # Get relevant PDF information
    alt_name = request.POST['ALT Name']
    lc_code = request.POST['LC Code']
    board_of_education = request.POST['Board of Education']
    sales_person = request.POST['Person in charge of sales']
    fax = request.POST['Fax']
    telephone = request.POST['Telephone']

    # Get the year, month, and day of the first date
    start_date_array = start_date.split('-', 1)
    end_date_array = end_date.split('-', 1)
    start_year = int(start_date_array[0])
    start_month = int(start_date_array[1])
    end_year = int(end_date_array[0])
    end_month = int(end_date_array[1])

    # Get school object from school_id
    schools = None 
    school_count = 1
    if school_id == 0:
        schools = School.objects.filter(school_year=school_year)
        school_count = schools.count()
    else:
        schools = [School.objects.get(id=school_id)]

    # Calculate number of months: (months_first_year) + (months_in_between) + months_last_year
    month_count = (13 - start_month) + ((end_year - start_year - 1)*12) + end_month

    # Make the filename
    now = dt.datetime.now()
    current_timestamp = str(now.year)+str(now.month)+str(now.day)+str(now.hour)+str(now.minute)+str(now.second)
    filename = slugify('timesheets-'+current_timestamp)+'.pdf'

    # Create response for the PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="'+filename+'"'

    # Create the PDF object, using the response object as its "file."
    pdf_object = canvas.Canvas(response, pagesize=A4)

    # PDF Font information
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_path = os.path.join(os.path.join(BASE_DIR, 'static'), 'fonts')
    reportlab.rl_config.TTFSearchPath.append(font_path)
    pdfmetrics.registerFont(TTFont('MS PGothic', 'ms-pgothic.ttf'))
    # I can't, for the life of me, find MS-PGothic-Bold.ttf, which is what they use
    pdfmetrics.registerFont(TTFont('GenShinGothic-Bold', 'GenShinGothic-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('Throw', 'ThrowMyHandsUpintheAir.ttf'))
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))        
    pdf_object.setLineWidth(0.8)
    
    for page_index in range(month_count):
        current_month = (start_month + page_index)%12
        current_month = 12 if current_month == 0 else current_month
        current_year = math.floor(start_year + (start_month + page_index)/12)
        current_year = current_year - 1 if start_month + page_index == 12 else current_year
        current_date_string = str(current_month) + '/' + str(current_year)

        # Top left corner
        cursor_y = 755
        pdf_object.setFont('MS PGothic', 12)
        pdf_object.drawString(50, cursor_y, 'REPORT SHEET OF WORK 業務実施報告書')

        pdf_object.setFont('MS PGothic', 20)
        pdf_object.drawString(70, cursor_y-23, 'FAX #: 043-203-8821')

        pdf_object.setFont('MS PGothic', 9)
        pdf_object.drawString(60, cursor_y-35, 'Fax to the office on the last working day of the month')
        
        box_start_x = 50
        box_start_y = cursor_y-5
        box_end_x = 275
        box_end_y = cursor_y-40
        pdf_object.setLineWidth(2)
        pdf_object.line(box_start_x, box_start_y, box_end_x, box_start_y) # top border
        pdf_object.line(box_start_x, box_end_y, box_end_x, box_end_y) # bottom border
        pdf_object.line(box_start_x, box_start_y+1, box_start_x, box_end_y-1) # left border
        pdf_object.line(box_end_x, box_start_y+1, box_end_x, box_end_y-1) # right border
        pdf_object.setLineWidth(1)

        # Top right corner: blanks
        pdf_object.setFont('MS PGothic', 11)
        pdf_object.drawString(350, cursor_y-1, 'BOE NAME:')
        pdf_object.drawString(350, cursor_y-19, 'NAME (講師名):')
        pdf_object.drawString(395, cursor_y-37, 'YEAR:           年 MONTH:          月')

        pdf_object.line(350, cursor_y-3, 560, cursor_y-3)
        pdf_object.line(350, cursor_y-21, 560, cursor_y-21)
        pdf_object.line(395, cursor_y-39, 560, cursor_y-39)

        # Top right corner: fill it in
        pdf_object.setFont('Throw', 13)
        pdf_object.drawString(440, cursor_y-1, board_of_education)
        pdf_object.drawString(437, cursor_y-19, alt_name+' ('+lc_code+') ')
        pdf_object.drawString(432, cursor_y-37, '%d                   %d'%(current_year, current_month))
        
        # Main table
        # Header
        pdf_object.setLineWidth(2)
        pdf_object.line(50, cursor_y-45, 560, cursor_y-45)
        pdf_object.setLineWidth(1)
        pdf_object.setFont('MS PGothic', 9)
        pdf_object.drawString(52, cursor_y-55, 'DATE')
        pdf_object.drawString(80, cursor_y-55, 'DAY')
        pdf_object.drawString(150, cursor_y-55, 'SCHOOL NAME1')
        pdf_object.drawString(280, cursor_y-55, 'DAILY STAMP')
        pdf_object.drawString(388, cursor_y-55, 'SCHOOL NAME2')
        pdf_object.drawString(500, cursor_y-55, 'DAILY STAMP')

        pdf_object.drawString(54, cursor_y-65, '日付')
        pdf_object.drawString(79, cursor_y-65, '曜日')
        pdf_object.drawString(167, cursor_y-65, '学校名1')
        pdf_object.drawString(293, cursor_y-65, '検収印')
        pdf_object.drawString(405, cursor_y-65, '学校名2')
        pdf_object.drawString(514, cursor_y-65, '検収印')

        # Body
        start_row_y = cursor_y-84
        start_row_x = 50
        end_row_x = 560
        month_range_object = calendar.monthrange(current_year, current_month)

        # Header horizontal lines
        header_line_1_y = cursor_y-70
        header_line_2_y = cursor_y-68
        pdf_object.line(start_row_x, header_line_1_y, 101, header_line_1_y)
        pdf_object.line(103, header_line_1_y, end_row_x, header_line_1_y)
        pdf_object.line(start_row_x, header_line_2_y, 101, header_line_2_y)
        pdf_object.line(103, header_line_2_y, end_row_x, header_line_2_y)

        # Header vertical lines
        header_start_line_y = cursor_y-45
        vert_date_x = 50
        vert_day_x = 76
        vert_school_name_1_x = 101
        vert_school_name_1_x2 = 103
        vert_daily_stamp_1_x = 275
        vert_school_name_2_x = 340
        vert_daily_stamp_2_x = 495
        vert_right_border_x = 560

        pdf_object.setLineWidth(2)
        pdf_object.line(start_row_x, header_start_line_y+1, start_row_x, header_line_1_y)
        pdf_object.setLineWidth(1)

        pdf_object.line(vert_day_x, header_start_line_y, vert_day_x, header_line_2_y)
        pdf_object.line(vert_school_name_1_x, header_start_line_y, vert_school_name_1_x, header_line_2_y)
        pdf_object.line(vert_school_name_1_x2, header_start_line_y, vert_school_name_1_x2, header_line_2_y)
        pdf_object.line(vert_daily_stamp_1_x, header_start_line_y, vert_daily_stamp_1_x, header_line_2_y)
        
        pdf_object.setLineWidth(2)
        pdf_object.line(vert_school_name_2_x, header_start_line_y, vert_school_name_2_x, header_line_2_y)
        pdf_object.setLineWidth(1)
        
        pdf_object.line(vert_daily_stamp_2_x, header_start_line_y, vert_daily_stamp_2_x, header_line_2_y)
        
        pdf_object.setLineWidth(2)
        pdf_object.line(vert_right_border_x, header_start_line_y+1, vert_right_border_x, header_line_1_y)
        pdf_object.setLineWidth(1)


        for day_index in range(month_range_object[1]):
            # Day
            pdf_object.setFont('MS PGothic', 10)
            day_row_y = start_row_y-(19*day_index)
            readable_day = str(day_index + 1)

            day_row_x = 58
            if day_index <= 8: # 1~9
                day_row_x = 61
            pdf_object.drawString(day_row_x, day_row_y, readable_day)

            # Weekday
            pdf_object.setFont('Throw', 11)
            weekday_readable = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            weekday_x = [79, 79, 78, 80, 81, 79, 79]
            weekday = (month_range_object[0]+day_index)%7
            pdf_object.drawString(weekday_x[weekday], day_row_y, weekday_readable[weekday])

            # School name
            pdf_object.setFont('Throw', 12)
            date_string = '%d-%d-%s'%(current_year, current_month, readable_day)
            datetime_object = datetime.strptime(date_string, '%Y-%m-%d')
            school_names = YearlySchedule.objects.get_school_names_for_day(datetime_object)

            for index, school_name in enumerate(school_names):
                school_index_x = 140 if index == 0 else 388
                pdf_object.drawString(school_index_x, day_row_y, school_name)

            # Draw horizontal lines
            line_row_y = day_row_y - 3
            if day_index == month_range_object[1]-1:
                pdf_object.setLineWidth(2)
                start_row_x -= 1
                end_row_x += 1
            pdf_object.line(start_row_x, line_row_y, 101, line_row_y)
            pdf_object.line(103, line_row_y, end_row_x, line_row_y)

            # Draw vertical lines
            day_row_y_start = day_row_y + 16
            day_row_y_end = day_row_y - 3

            pdf_object.setLineWidth(2)
            pdf_object.line(vert_date_x, day_row_y_start, vert_date_x, day_row_y_end)
            pdf_object.setLineWidth(1)

            if day_index == 0:
                day_row_y_start -= 2

            pdf_object.line(vert_day_x, day_row_y_start, vert_day_x, day_row_y_end)
            pdf_object.line(vert_school_name_1_x, day_row_y_start, vert_school_name_1_x, day_row_y_end)
            pdf_object.line(vert_school_name_1_x2, day_row_y_start, vert_school_name_1_x2, day_row_y_end)
            pdf_object.line(vert_daily_stamp_1_x, day_row_y_start, vert_daily_stamp_1_x, day_row_y_end)
            
            pdf_object.setLineWidth(2)
            pdf_object.line(vert_school_name_2_x, day_row_y_start, vert_school_name_2_x, day_row_y_end)
            pdf_object.setLineWidth(1)
            
            pdf_object.line(vert_daily_stamp_2_x, day_row_y_start, vert_daily_stamp_2_x, day_row_y_end)
            
            if day_index == 0:
                day_row_y_start += 2

            pdf_object.setLineWidth(2)
            pdf_object.line(vert_right_border_x, day_row_y_start, vert_right_border_x, day_row_y_end)
            pdf_object.setLineWidth(1)

        pdf_object.setLineWidth(2)
        pdf_object.line(vert_school_name_1_x, line_row_y, vert_school_name_1_x2, line_row_y)
        pdf_object.setLineWidth(1)

        text_row_y = line_row_y - 10
        pdf_object.setFont('MS PGothic', 9)
        pdf_object.drawString(52, text_row_y, '株式会社インタラック')
        pdf_object.drawString(vert_school_name_2_x+2, text_row_y, '上記のとおり業務を実施した事を報告致します。')

        # picture = static('/media/logo-interac.png')
        picture_y = text_row_y - 25
        picture = ImageReader('https://interacnetwork.com/the-content/cream/wp-content/themes/creampress/assets/images/logo-interac.png')
        pdf_object.drawImage(picture, 52, picture_y, width=80, height=20, preserveAspectRatio=True, mask='auto')
        
            # New page
        pdf_object.showPage()

    pdf_object.save()
    return response

def __print_date(date_string, story=[]):
    # Get school and period information for said date
    datetime_object = datetime.strptime(date_string, '%Y-%m-%d')
    school_info = YearlySchedule.objects.get_schedule_information_for_day(datetime_object)

    # Go through each school in the schedule
    for schedule in school_info['schedules']:
        # Prepare the basic school information for the day
        school_name = schedule.school.name
        period_profile = schedule.information['school_period_type'].period_name
        materials = schedule.information['materials']
        flashcards = schedule.information['flashcards']
        handouts = schedule.information['handouts']
        class_schedules = []

        flashcard_array = []
        flashcard_index = 0
        flashcard_count = len(flashcards)

        for flashcard in flashcards:
            flashcard_array.append(flashcard['flashcard'])

        handout_array = []
        handout_index = 0
        handout_count = len(handouts)

        for handout in handouts:
            handout_array.append(handout['filename'])

        # Prepare two arrays: One storing Lesson Plans (and flashcards/materials/handouts) for the day, the the other a Class to Lesson Plan map
        lesson_plans = []
        lesson_plan_class = OrderedDict()

        # Go through each class, and check its lesson plan
        for period in schedule.information['school_periods']:
            year_level = None
            section_name = None
            teacher_name = None
            lesson_number = None
            hour_number = None
            lesson_plan = None
            is_special_needs = False
            student_count = 0
            notes = ''

            if period.class_info:
                year_level = period.class_info.section.school_section.year_level
                is_special_needs = period.class_info.section.school_section.is_special_needs
                section_name = period.class_info.section.section_name
                teacher_name = period.class_info.section.teacher_name
                student_count = period.class_info.section.student_count
                lesson_number = period.class_info.lesson_number
                hour_number = period.class_info.hour_number
                notes = period.class_info.notes

                lesson_plan_info = period.class_info.lesson_plan.get_all_info_from_all_activities()

                handouts_raw = lesson_plan_info['handouts']
                handouts_string = ''
                handout_index = 0
                handout_count = len(handouts_raw)

                flashcards_raw = lesson_plan_info['flashcards']
                flashcards_arr = []

                for flashcard in flashcards_raw:
                    flashcards_arr.append(flashcard['flashcard'])

                for handout in handouts_raw:
                    handouts_string += handout['filename']
                    if handout_index < handout_count - 1:
                        handout_index += 1
                        handouts_string += ', '

                lesson_plan = {
                    'materials': ', '.join(lesson_plan_info['materials']),
                    'flashcards': ', '.join(flashcards_arr),
                    'handouts': handouts_string,
                    'greeting': period.class_info.lesson_plan.greeting,
                    'warmup': period.class_info.lesson_plan.warmup,
                    'presentation': period.class_info.lesson_plan.presentation,
                    'practice': period.class_info.lesson_plan.practice,
                    'production': period.class_info.lesson_plan.production,
                    'cooldown': period.class_info.lesson_plan.cooldown,
                    'assessment': period.class_info.lesson_plan.assessment,
                }

            class_schedules.append({
                'period_number': period.period_number,   
                'start_time': period.start_time,   
                'end_time': period.end_time,   
                'year_level': year_level,   
                'section': section_name,   
                'teacher': teacher_name,   
                'lesson': lesson_number,
                'student_count': student_count,
                'hour': hour_number,
                'notes': notes,
                'is_special_needs': is_special_needs,
            })

            ## If the lesson plan does not exist in the Lesson Plan array, store it in the Lesson Plan array
            if lesson_plan is not None:
                index = 0
                if lesson_plan not in lesson_plans:
                    lesson_plans.append(lesson_plan)
                    index = len(lesson_plans) - 1
                else:
                    index = lesson_plans.index(lesson_plan)

                # Use the index to update the Class to Lesson Plan Map
                if index not in lesson_plan_class:
                    lesson_plan_class[index] = []

                lesson_plan_class[index].append({
                    'year_level': year_level,
                    'section': section_name,
                    'student_count': student_count,
                })
             
        # PDF Font information
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        font_path = os.path.join(os.path.join(BASE_DIR, 'static'), 'fonts')
        reportlab.rl_config.TTFSearchPath.append(font_path)
        pdfmetrics.registerFont(TTFont('font-default', 'irohamaru-mikami-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('font-bold', 'irohamaru-mikami-Medium.ttf'))
        pdfmetrics.registerFont(TTFont('font-light', 'irohamaru-mikami-Light.ttf'))

        # Styles
        styles = getSampleStyleSheet() 
        styles.add(ParagraphStyle(name='header-left', alignment=TA_LEFT, fontName="font-bold", fontSize=20))
        styles.add(ParagraphStyle(name='header-right', alignment=TA_RIGHT, fontName="font-bold", fontSize=20))
        styles.add(ParagraphStyle(name='subheader', alignment=TA_LEFT, fontName='font-bold', fontSize=16))
        styles.add(ParagraphStyle(name='bold', alignment=TA_LEFT, fontName='font-bold', fontSize=12, leading=15))
        styles.add(ParagraphStyle(name='normal', alignment=TA_LEFT, fontName='font-default', fontSize=12, leading=15))
        styles.add(ParagraphStyle(name='justified', alignment=TA_JUSTIFY, fontName='font-default', fontSize=12))
        styles.add(ParagraphStyle(name='n-a', alignment=TA_LEFT, fontName='font-light', fontSize=12, textColor=colors.grey))
        default_table_style = TableStyle([
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LINEBELOW', (0,0), (-1,-1), 0.1, colors.black)
        ])

        # Header
        header_data = [[
            Paragraph(school_name, styles['header-left']),
            Paragraph('%s/%s/%s' % (str(datetime_object.month), str(datetime_object.day), str(datetime_object.year)), styles['header-right'])]]
        table = Table(header_data, [4.5*inch, 3*inch], 1*[0.4*inch])
        table.setStyle(TableStyle([
            ('VALIGN',(0,-1),(-1,-1),'TOP'),
            ('LINEBELOW', (0,0), (-1,-1), 2, colors.black)
        ]))
        story.append(table)

        # Class Schedule Subheader
        story.append(Spacer(1,12))
        story.append(Paragraph('Class Schedule: %s' % (period_profile), styles['subheader']))

        class_schedule_table_data = []

        # Class Schedule Table Header
        class_schedule_table_data.append([
            Paragraph('Period', styles['bold']),
            Paragraph('Class', styles['bold']),
            Paragraph('Students', styles['bold']),
            Paragraph('Teacher', styles['bold']),
            Paragraph('Lesson', styles['bold'])
        ])

        # Class Schedule Table Information
        for item in class_schedules:
            period_information = 'Period %s<br/><font size="8">%s ~ %s</font>' % (str(item['period_number']), item['start_time'].strftime('%H:%M'), item['end_time'].strftime('%H:%M'))

            if item['year_level'] is not None:
                # Class section name
                section_information = 'SN' if item['is_special_needs'] else '%d-%s' % (item['year_level'], item['section'])
                section_style = styles['normal']
                student_count = str(item['student_count'])
                lesson_information = 'Lesson %d, Hour %d\n' % (item['lesson'], item['hour'])
                lesson_element = [Paragraph(lesson_information, styles['normal'])]
                if item['notes']:
                    lesson_element.append(Paragraph('Notes: %s'%(item['notes']), styles['n-a']))

                if item['teacher'] == '':
                    teacher_name = 'N/A'
                    teacher_style = styles['n-a']
                else:
                    teacher_name = item['teacher']
                    teacher_style = styles['normal']

            else:
                section_information = 'Free'
                section_style = styles['n-a']
                student_count = ''
                teacher_name = ''
                teacher_style = styles['normal']
                lesson_element = Paragraph('', styles['normal'])

            class_schedule_table_data.append([
                Paragraph(period_information, styles['normal']),
                Paragraph(section_information, section_style),
                Paragraph(student_count, styles['normal']),
                Paragraph(teacher_name, teacher_style),
                lesson_element,
            ])
        
        story.append(Spacer(1,10))
        class_schedule_table = Table(class_schedule_table_data)
        class_schedule_table.setStyle(default_table_style)
        story.append(class_schedule_table)

        # Preparations for the day: header
        story.append(Spacer(1,12))
        story.append(Paragraph('Preparations for the day', styles['subheader']))

        # Preparations for the day: information
        story.append(Spacer(1,10))

        daily_preparations_data = [
            [Paragraph('Materials', styles['bold']), __get_preparation_items(materials, styles)],
            [Paragraph('Flashcards', styles['bold']), __get_preparation_items(flashcard_array, styles)],
            [Paragraph('Handouts', styles['bold']), __get_preparation_items(handout_array, styles)],
        ]
        daily_preparations_table = Table(daily_preparations_data, [1.25*inch, 6.25*inch])
        daily_preparations_table.setStyle(default_table_style)
        story.append(daily_preparations_table)

        # Lesson Plans
        for lesson_plan_index, item in lesson_plan_class.items():
            section_index = 0
            total_student_count = 0
            lesson_header_text = 'For '
            for section in item:
                total_student_count += section['student_count']
                if section['year_level']==0:
                    year_level='SN'
                else:
                    year_level=str(section['year_level'])
                lesson_header_text += year_level+'-'+str(section['section'])
                if section_index < len(item)-1:
                    section_index += 1
                    lesson_header_text += ', '
            lesson_header_text += ' ('+str(total_student_count)+' students)'

            # Lesson Plan Table Subheaders
            story.append(Spacer(1,20))
            story.append(Paragraph(lesson_header_text, styles['subheader']))

            __print_lesson_plan_contents(story, lesson_plans[lesson_plan_index], styles)
        story.append(PageBreak())

def __generate_pdf_object_and_response(filename):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s.pdf"'%(filename)
    return (canvas.Canvas(response, pagesize=A4), response)

def __pdf_draw_body_row_line(pdf_object, y_axis):
    pdf_object.line(40, y_axis, 333, y_axis)
    pdf_object.line(336, y_axis, 510, y_axis)
    pdf_object.line(513, y_axis, 558, y_axis)

def __prepare_styles_and_font():
    # PDF Font information
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_path = os.path.join(os.path.join(BASE_DIR, 'static'), 'fonts')
    reportlab.rl_config.TTFSearchPath.append(font_path)
    pdfmetrics.registerFont(TTFont('font-default', 'irohamaru-mikami-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('font-bold', 'irohamaru-mikami-Medium.ttf'))
    pdfmetrics.registerFont(TTFont('font-light', 'irohamaru-mikami-Light.ttf'))
    pdfmetrics.registerFont(TTFont('Handwriting', 'HandwritingWeCan-Medium.ttf'))

    styles = getSampleStyleSheet() 
    styles.add(ParagraphStyle(name='header-left', alignment=TA_LEFT, fontName="font-bold", fontSize=20))
    styles.add(ParagraphStyle(name='header-right', alignment=TA_RIGHT, fontName="font-bold", fontSize=20))
    styles.add(ParagraphStyle(name='subheader', alignment=TA_LEFT, fontName='font-bold', fontSize=16))
    styles.add(ParagraphStyle(name='bold', alignment=TA_LEFT, fontName='font-bold', fontSize=12, leading=15))
    styles.add(ParagraphStyle(name='normal', alignment=TA_LEFT, fontName='font-default', fontSize=12, leading=15))
    styles.add(ParagraphStyle(name='justified', alignment=TA_JUSTIFY, fontName='font-default', fontSize=12))
    styles.add(ParagraphStyle(name='n-a', alignment=TA_LEFT, fontName='font-light', fontSize=12, textColor=colors.grey))
    return styles

def __generate_pdf_download(filename='unnamed.pdf'):
    file_storage = FileSystemStorage('/tmp')
    with file_storage.open(filename) as pdf:
        # Create response for the PDF
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s"' % (filename)
    
    return response

def __print_lesson_plan_contents(story, lesson_plan, styles):
    default_table_style = TableStyle([
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LINEBELOW', (0,0), (-1,-1), 0.1, colors.black)
    ])

    lesson_plan_data = []
    lesson_plan_data.append([
        Paragraph('Materials', styles['bold']), 
        __get_preparation_items(lesson_plan['materials'], styles)])
    lesson_plan_data.append([
        Paragraph('Flashcards', styles['bold']), 
        __get_preparation_items(lesson_plan['flashcards'], styles)])
    lesson_plan_data.append([
        Paragraph('Handouts', styles['bold']), 
        __get_preparation_items(lesson_plan['handouts'], styles)])
    lesson_plan_data.append([
        Paragraph('Greeting', styles['bold']),
        __write_lesson_plan_portion(lesson_plan['greeting'], styles)])
    lesson_plan_data.append([
        Paragraph('Warmup', styles['bold']),
        __write_lesson_plan_portion(lesson_plan['warmup'], styles)])
    lesson_plan_data.append([
        Paragraph('Presentation', styles['bold']),
        __write_lesson_plan_portion(lesson_plan['presentation'], styles)])
    lesson_plan_data.append([
        Paragraph('Practice', styles['bold']),
        __write_lesson_plan_portion(lesson_plan['practice'], styles)])
    lesson_plan_data.append([
        Paragraph('Production', styles['bold']),
        __write_lesson_plan_portion(lesson_plan['production'], styles)])
    lesson_plan_data.append([
        Paragraph('Cooldown', styles['bold']),
        __write_lesson_plan_portion(lesson_plan['cooldown'], styles)])
    lesson_plan_data.append([
        Paragraph('Assessment', styles['bold']),
        __write_lesson_plan_portion(lesson_plan['assessment'], styles)])

    story.append(Spacer(1,10))
    lesson_plan_table = Table(lesson_plan_data, [1.25*inch, 6.25*inch])
    lesson_plan_table.setStyle(default_table_style)
    story.append(lesson_plan_table)

def __get_preparation_items(source_array, styles):
    if len(source_array) == 0:
        return_string = 'N/A'
        return_style = styles['n-a']
    else:
        if type(source_array) is list:
            return_string = ', '.join(source_array)
        else:
            return_string = source_array
        return_style = styles['normal']
    return Paragraph(return_string, return_style)

def __write_lesson_plan_portion(source, styles):
    if source is not None:
        description = source.description.replace('\n', '<br/>')
        simple_split = simpleSplit(description, 'font-default', 12, 533)
        max_line_count = 18
        if len(simple_split) > max_line_count:
            description = ''.join(simple_split[0:max_line_count-1]) + '(...This activity has been truncated because it is too long to fit in the page.)'
        return [Paragraph(source.activity_name, styles['bold']), Paragraph(description, styles['normal'])]
    else:
        return Paragraph('N/A', styles['n-a'])

def __print_flashcard(pdf_object, flashcard, specified_image=None):
    # Set the page size
    flashcard_type = flashcard.flashcard_type
    left_start_margin = 40
    top_start_margin = 800
    border_line_width = 2
    picture_height_offset = 10
    label_x = 50 
    label_w = 0 
    label = flashcard.label 
    cursor = {'x': left_start_margin, 'y': top_start_margin}

    # Font information
    __prepare_styles_and_font()

    # Get the lessons where the flashcard appears
    flashcard_lesson_instance = FlashcardLesson.objects.filter(flashcard=flashcard)
    lesson_text = ''
    for flashcard_lesson in flashcard_lesson_instance:
        lesson_text += (flashcard_lesson.lesson.course.course_code+'L'+str(flashcard_lesson.lesson.lesson_number)+' ')

    if flashcard.orientation == PORTRAIT:
        pdf_object.setPageSize(portrait(A4))

        # Border variables
        horizontal_border_length = 512
        vertical_border_length = 760
        font_size = 90

    else:
        pdf_object.setPageSize(landscape(A4))
        top_start_margin = 552
        cursor['y'] = top_start_margin

        # Border variables
        horizontal_border_length = 760
        vertical_border_length = 512
        font_size = 70

    # Calculate font size 
    label_w = horizontal_border_length-20 
    if flashcard_type == FRONT_BACK:
        font_size += 30

    max_text_horizontal_length = horizontal_border_length - 40
    while stringWidth(label, 'Handwriting', font_size) > max_text_horizontal_length: 
        font_size -= 1
    label_h = font_size
    label_y = 85 if flashcard_type != FRONT_BACK else vertical_border_length/2 + 40
 
    # Recalculate some values
    if flashcard_type == PICTURE_LABEL:
        picture_height_offset += (label_y+40)
    picture_x = 50
    picture_y = 80 + label_y if flashcard_type == PICTURE_LABEL else 50
    picture_width = horizontal_border_length - 20
    if flashcard_type == PICTURE_ONLY:
        picture_y += 30
        picture_height_offset += 30
    picture_height = vertical_border_length - picture_height_offset

    # Borders
    if flashcard.is_bordered:
        __draw_horizontal(pdf_object, cursor, border_line_width, horizontal_border_length, 0) # Top border
        __draw_horizontal(pdf_object, cursor, border_line_width, 0, -vertical_border_length) # Left border
        cursor['x'] = horizontal_border_length + left_start_margin
        cursor['y'] = left_start_margin
        __draw_horizontal(pdf_object, cursor, border_line_width, -horizontal_border_length, 0) # Bottom border
        __draw_horizontal(pdf_object, cursor, border_line_width, 0, vertical_border_length) # Right border

    # Lesson information, top left
    pdf_object.setFillColorRGB(0.6,0.6,0.6)
    pdf_object.setFont('font-default', 10)
    cursor['x'] = left_start_margin
    cursor['y'] = top_start_margin + 5
    __write_text(pdf_object, cursor, lesson_text)

    # Notes, bottom left, beneath the border
    cursor['y'] = 30
    __write_text(pdf_object, cursor, flashcard.notes)

    # Picture, front and center (a little vertically higher if the label is shown)
    picture = static('/media/'+str(flashcard.picture)) if specified_image == None else specified_image
    pdf_object.drawImage(picture, picture_x, picture_y, width=picture_width, height=picture_height, preserveAspectRatio=True, mask='auto')
    
    # Label, bottom, none, or next page
    # Prepare the frame 
    frame = Frame(label_x, label_y, label_w, label_h) 
    styles = getSampleStyleSheet() 
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER))  
    label = '<font name="Handwriting" size=%s>%s</font>' % (font_size, label) 
    story = [Paragraph(label, styles['Center'])] 
    story_in_frame = KeepInFrame(label_w, label_h, story) 

    if flashcard_type == FRONT_BACK:
        # Draw the label at the center of a new page
        pdf_object.showPage()

    if flashcard_type != PICTURE_ONLY:
        frame.addFromList([story_in_frame], pdf_object) 

    pdf_object.showPage()

def __print_target_language(pdf_object, target_language, does_lesson_exist=True):
    # Set the page size and label coordinates
    margin = 30
    inner_margin = 10
    border_line_width = 10
    width, height = landscape(A4)
    left_start_margin = margin
    top_start_margin = height-margin
    horizontal_border_length = width-(margin*2)
    vertical_border_length = height-(margin*2)
    font_size = 250
    label_x = margin+10
    label_w = horizontal_border_length-(inner_margin*2)
    label_h = font_size
    label = target_language.target_language
    cursor = {'x': left_start_margin, 'y': top_start_margin}
    pdf_object.setPageSize(landscape(A4))

    # Font information
    __prepare_styles_and_font()
    
    # Lesson information (not applicable if it's called from Generate Target Language)
    lesson_text = ''
    if does_lesson_exist:
        lesson = target_language.lesson
        lesson_text = lesson.course.course_code+'L'+str(lesson.lesson_number)

    # Notes
    notes = target_language.notes

    # Calculate font size and height
    # One-line flashcards have a minimum font size of 170, two-line flashcards: 155, etc.
    min_font_sizes = [170, 155, 140, 125]
    line_count = 1
    height_multiplier = 1.25
    max_text_horizontal_length = 1400

    while stringWidth(label, 'Handwriting', font_size)/line_count > max_text_horizontal_length: 
        font_size -= 1
        if font_size < min_font_sizes[line_count - 1]:
            line_count += 1
            height_multiplier -= 0.05
            if line_count > 5:
                break
                
    label_h = font_size*line_count*height_multiplier
    label_y = margin+((vertical_border_length-label_h)/2) - 20

    # Draw border
    r, g, b = tuple(int(target_language.get_hex_color()[i:i+2], 16)/255 for i in (0, 2 ,4))
    pdf_object.setStrokeColorRGB(r,g,b)
    __draw_horizontal(pdf_object, cursor, border_line_width, horizontal_border_length, 0) # Top border
    __draw_horizontal(pdf_object, cursor, border_line_width, 0, -vertical_border_length) # Left border
    cursor['x'] = horizontal_border_length + left_start_margin
    cursor['y'] = left_start_margin
    __draw_horizontal(pdf_object, cursor, border_line_width, -horizontal_border_length, 0) # Bottom border
    __draw_horizontal(pdf_object, cursor, border_line_width, 0, vertical_border_length) # Right border

    # Lesson information, top left
    pdf_object.setFillColorRGB(0.6,0.6,0.6)
    pdf_object.setFont('font-default', 10)
    cursor['x'] = left_start_margin
    cursor['y'] = top_start_margin + (border_line_width/1.5)
    __write_text(pdf_object, cursor, lesson_text)

    cursor['y'] = margin-15
    __write_text(pdf_object, cursor, notes)

    # Draw appropriate triangle
    triangle = '◀'
    pdf_object.setFont('font-default', 40)
    triangle_x = 0
    triangle_y = margin+(vertical_border_length/2)
    if target_language.color == TARGET_LANGUAGE_BLUE:
        triangle = '▶'
        triangle_x = horizontal_border_length+20
    cursor['x'] = triangle_x
    cursor['y'] = triangle_y
    pdf_object.setFillColorRGB(r,g,b)
    __write_text(pdf_object, cursor, triangle)

    # Label
    frame = Frame(label_x, label_y, label_w, label_h) 
    styles = getSampleStyleSheet() 
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontName="Handwriting", fontSize=font_size, leading=font_size*1.25, textColor=Color(r,g,b)))  

    story = [Paragraph(label, styles['Center'])] 
    story_in_frame = KeepInFrame(label_w, label_h, story) 
    frame.addFromList([story_in_frame], pdf_object) 

    pdf_object.showPage()

def __draw_horizontal(pdf_object, cursor, line_width, horizontal_distance, vertical_distance):
    x_initial = cursor['x']
    y_initial = cursor['y']
    x_final = x_initial + horizontal_distance
    y_final = y_initial + vertical_distance
    pdf_object.setLineWidth(line_width)
    pdf_object.line(x_initial, y_initial, x_final, y_final)

def __write_text(pdf_object, cursor, text):
    pdf_object.drawString(cursor['x'], cursor['y'], text)
