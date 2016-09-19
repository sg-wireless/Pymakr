
def readQssColors():
    import re
    from PyQt5.QtGui import QColor
    from E5Gui.E5Application import e5App

    qss = e5App().styleSheet()
    colorStart = qss.find("PycomEditorColors")
    if colorStart == -1:
        return None        
    colorEnd = qss.find("}", colorStart)
    if colorEnd == -1:
        return None
    colorStart = qss.find("{", colorStart, colorEnd)
    if colorStart == -1:
        return None

    colorString = qss[colorStart + 1:colorEnd]
    colorString = re.sub(r"\s+", "", colorString, flags=re.UNICODE)

    pattern = re.compile(r'(.+?):(.+?);')

    result = {}
    for (name, value) in re.findall(pattern, colorString):
        if name != 'colors':
            result[name] = QColor(value)
        else:
            result[name] = value

    if 'colors' in result:
        result['colors']  = result['colors'] .split(',')

    return result