# Regular expression used to validate channel names.
# (Note that you have to escape backslashes with \ )
# channelname=[ \\-=\\w\\#\\[\\]\\{\\}\\(\\)\\@\\|]+

# Regular expression used to validate user names.
# (Note that you have to escape backslashes with \ )
# username=[-=\\w\\[\\]\\{\\}\\(\\)\\@\\|\\.]+
DEFAULT_MUMBLE_USERNAME_REGEX = r"[-=\w\[\]\{\}\(\)\@\|\.]+"

import re
from typing import Optional

def sanitize_username(username: str, pattern: Optional[str] = None) -> str:
    """
    Sanitize the supplied username against the provided regex pattern.

    :param username: The username to sanitize.
    :param pattern: A regex pattern representing permitted characters.
    :return: The sanitized username with invalid characters replaced by '-'.
    """
    username = username.replace(' ','_')
    # Compile the regex pattern to match invalid characters
    pattern = pattern or DEFAULT_MUMBLE_USERNAME_REGEX
    allowed_pattern = re.compile(pattern)
    sanitized = ''.join(char if allowed_pattern.fullmatch(char) else '-' for char in username)
    return sanitized
