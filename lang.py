#
# 
#
"""This module provides GUI messages & string in Persian."""


LANG = 'فارسی'

LANG_EN = 'Persian'

USER = 'کاربر'

ADMIN = 'مدیر'

COMMANDS = 'دستورات'

PANEL = 'صفحه'

ADMIN_PANEL = f'{PANEL} {ADMIN}'
"""The title of the Admin Panel."""

ADMIN_PANEL_NO_ACCESS = f'شما به {PANEL} {ADMIN} دسترسی ندارید'
"""The message to show when a user does not have access to the
Admin Panel.
"""

HELP = 'راهنمایی'

HELP_CMD_INTRO = f'{HELP}: برای نمایش همین {PANEL}'

MY_COURSES = 'دوره های من'

PRODUCTS = 'محصولات'

PRODUCTS_CMD_INTRO = f'{PRODUCTS}: نمایش یک لیست از تمام {PRODUCTS}'
"""The introduction of Products command."""

SIGN_IN = 'ثبت نام'

ENTER_YOUR_FIRST_NAME = 'لطفا نام کوچک خود را وارد کنید:'

START = f'{PANEL} من'
"""The title of the user panel."""

START_CMD_INTRO = f'برای دسترسی به {PANEL} شما'
"""The introduction of Start command."""

OBJECTIVES = 'هدف ما آموزش سریع زبان است'

BONUS = ''

REJECT_UNKNOWN = f'متاسفانه {USER} شما تشخیص داده نشد. امکان خدمات دهی به شما وجود ندارد.'

SELECT_LANG = 'لطفا زبان خود را انتخاب کنید.'

UNEX_CMD = "'{}' یک دستور نیست. برای مشاهده فهرست دستورات دکمه زیر را بزنید."

UNKNOWN_USER = f'{USER} شما ناشناس است'
"""The message to show when the user object is `None`."""

COMMANDS_CMD_INFO = F'{COMMANDS}: برای نامیش خلاصه همه {COMMANDS}'

UNEX_DATA = 'شما مجاز به وارد کردن اطلاعات نیستید. اگر در میانه فرآیندی بودید، از ابتدا آن را انجام دهید.'
