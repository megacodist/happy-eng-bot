#
# 
#


def main() -> None:
    from gettext import translation
    mainEn = translation('main', 'locales', ['en'])
    mainEn.install()
    print(_('LANG'))
    print(_('SELECT_LANG'))
    mainFr = translation('main', 'locales', ['fr'])
    mainFr.install()
    print(_('LANG'))
    

if __name__ == '__main__':
    main()