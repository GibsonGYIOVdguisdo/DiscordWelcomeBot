from typing import TypedDict
from datetime import datetime

class Guild(TypedDict):
    guild: int
    top_welcomer_role: int
    welcome_channel: int
    