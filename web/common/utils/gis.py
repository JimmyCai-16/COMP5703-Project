from datetime import timedelta, datetime


def convert_esri_time(time):
    """ESRI time is in MS I think?"""
    if time:
        epoch = datetime(1970, 1, 1)  # Epoch for Unix timestamps
        milliseconds = timedelta(milliseconds=time)
        return epoch + milliseconds

    return None


def re_findall_ids(string):
    """Attempts to find all NNTT id's e.g., QS2001/001"""
    import re
    return re.findall(r'\b\w+\/\d+\b', string) if string else []