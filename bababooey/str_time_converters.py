import re

MILLIS_STR_RE = re.compile(r'^(((\d?\d:)?\d)?|\d{0,3})\d(\.\d\d{0,2})?$')


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
    return f'{mins:02}:{secs:02}.{millis:03}'


def str_to_millis(millis_str: str) -> int:
    if not MILLIS_STR_RE.match(millis_str):
        raise ValueError(
            f'millis_str is of an unexpected structure: "{millis_str}"')
    mins = '0'
    millis = '0'
    if ':' in millis_str:
        mins, millis_str = millis_str.split(':')
    if '.' in millis_str:
        millis_str, millis = millis_str.split('.')
    secs = millis_str

    mins = int(mins)
    secs = int(secs)
    # Pad millis with enough zeros.
    # This prevents '1.01' and '1.1' from having same millis.
    millis = int(f'{millis:0<3}')
    return mins * 60 * 1000 + secs * 1000 + millis
