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

OPERATION = 'فرآیند'

PRODUCTS = 'محصولات'

FIRST_NAME = 'نام کوچک'

LAST_NAME = 'نام خانوادگی'

PHONE = 'موبایل'

CANCEL_OP = f'لغو {OPERATION}'

CONTINUE_OP = f'ادامه {OPERATION}'

ADMIN_PANEL = f'{PANEL} {ADMIN}'
"""The title of the Admin Panel."""

ADMIN_PANEL_NO_ACCESS = f'شما به {PANEL} {ADMIN} دسترسی ندارید'
"""The message to show when a user does not have access to the
Admin Panel.
"""

HELP = 'راهنمایی'

HELP_ALL_CMDS = 'فهرست تمامی دستورات:'

HELP_CMD_INTRO = f'{HELP}: برای نمایش همین {PANEL}'

MY_COURSES = 'دوره های من'

PRODUCTS_CMD_INTRO = f'{PRODUCTS}: نمایش یک لیست از تمام {PRODUCTS}'
"""The introduction of Products command."""

SIGN_IN = 'ثبت نام'

ALREADY_SIGNED_IN = 'شما قبلا ثبت نام کرده اید.'

START = f'{PANEL} من'
"""The title of the user panel."""

START_CMD_INTRO = f'برای دسترسی به {PANEL} شما'
"""The introduction of Start command."""

OBJECTIVES = 'هدف ما آموزش سریع زبان است'

BONUS = ''

REJECT_UNKNOWN = f'متاسفانه {USER} شما تشخیص داده نشد. امکان خدمات دهی به شما وجود ندارد.'

UNEX_CMD = "'{}' یک دستور نیست. برای مشاهده فهرست دستورات دکمه زیر را بزنید."

UNKNOWN_USER = f'{USER} شما ناشناس است'
"""The message to show when the user object is `None`."""

SHOWCASE = f'ویترین {PRODUCTS}'

SHOWCASE_CMD_INTRO = F'{COMMANDS}: برای نمایش خلاصه همه {COMMANDS}'

UNEX_DATA = 'شما مجاز به وارد کردن اطلاعات نیستید. اگر در میانه فرآیندی بودید، از ابتدا آن را انجام دهید.'

DISRUPTIVE_CMD = 'شما در حال انجام یک فرآیند هستید. با وارد کردن یک دستور، آن فرآیند لغو می شود.'

CONFIRM_DATA = 'آیا اطلاعات زیر مورد تایید شما می باشد؟'

CONFIRM = 'تایید'

RESTART = 'شروع دوباره'

EXPIRED_CB = 'فرآیند مربوط به این دکمه منقضی شده است.'
