import time

import requests
from requests import RequestException
from typing import Union


class ANSI:
    # ANSI escape codes for basic text colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # ANSI escape codes for bright/extended text colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # ANSI escape codes for light and dark gray text colors
    LIGHT_GRAY = '\033[37m'
    DARK_GRAY = '\033[90m'

    # ANSI escape codes for background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    # ANSI escape code to reset text color to default
    RESET = '\033[0m'

    HIDE_CURSOR = '\033[?25l'
    SHOW_CURSOR = '\033[?25h'

def try_get_request(url, max_retries=5, retry_delay: Union[int, float] = 200, **kwargs):
    """Attempts to perform a get request to some URL. Will add delay in between failed requests.

    Parameters
    ----------
    url : str
        requesting URL path.
    max_retries : int
        Maximum number of connection retries.
    retry_delay : int
        Delay between retries in milliseconds.
    **kwargs
        Keyword arguments for the request. See: `requests.get()`

    Returns
    -------
    response | None
    """
    for retry_count in range(max_retries):
        try:
            response = requests.get(url, **kwargs)

            if response.status_code == 200:
                return response

        except RequestException as e:
            pass  # Network error happened

        if retry_count < max_retries - 1:
            time.sleep(retry_delay // 1000)

    raise ConnectionError(f'Connection to "{url}" failed after {max_retries} attempts ({retry_delay}ms)')

def try_get_json(url, max_retries=5, retry_delay: Union[int, float] = 200, **kwargs) -> dict:
    """Attempts to perform a get request to some URL. Will add delay in between failed requests.

    Parameters
    ----------
    url : str
        requesting URL path.
    max_retries : int
        Maximum number of connection retries.
    retry_delay : int
        Delay between retries in seconds.
    **kwargs
        Keyword arguments for the request. See: `requests.get()`
    """
    try:
        return try_get_request(url, max_retries=max_retries, retry_delay=retry_delay, **kwargs).json()
    except (ConnectionError, requests.exceptions.JSONDecodeError) as e:
        pass

    return dict([])
