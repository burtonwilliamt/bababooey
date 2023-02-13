from dataclasses import dataclass
import datetime

@dataclass
class SoundEffectData:
    num: int
    name: str
    emoji: str
    yt_url: str
    file_path: str
    author: int
    guild: int
    created_at: datetime.datetime
    start_millis: int = 0
    end_millis: int | None = None
    tags: str = ''
