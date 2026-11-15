from typing import TypedDict
from datetime import datetime

class Guild(TypedDict):
    guild: int = None
    top_welcomer_role: int = None
    welcome_channel: int = None
    