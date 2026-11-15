from typing import TypedDict
from datetime import datetime

class Welcome(TypedDict):
    welcomer: int
    welcomed: int
    date: datetime
    guild: int