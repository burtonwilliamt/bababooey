
def split_millis(millis: int) -> tuple[int, int, int]:
    """Returns (minutes, seconds, millis)."""
    minutes = int(millis // 1000 // 60)
    seconds = int((millis // 1000) % 60)
    millis = int(millis % 1000)
    return (minutes, seconds, millis)


def millis_to_str(millis: int | None) -> str:
    if millis is None:
        return 'None'
    mins, secs, millis = split_millis(millis)
    if mins > 0:
        return f'{mins:02}:{secs:02}.{millis:04}'
    else:
        return f'{secs:02}.{millis:04}'
