def get_choice_from_display(choices, display):
    """Returns the choice value from the display value (which is often stored in the shapefiles"""
    for value, _display in choices:
        if display == _display or value == display:
            return value

    raise ValueError(display, choices)