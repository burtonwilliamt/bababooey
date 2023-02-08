from dataclasses import dataclass
import datetime

@dataclass
class SoundEffect:
    name: str
    emoji: str
    yt_url: str
    local_path: str
    #author: int
    #guild: int
    #created: datetime.datetime
    start_time: int = None
    end_time: int = None