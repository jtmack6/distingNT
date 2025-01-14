from typing import List

def nybble_char(n: int) -> str:
    """Convert a nybble to a character."""
    if n >= 10:
        return chr(ord('A') + n - 10)
    return chr(ord('0') + n)

def dump_sysex(data: List[int], prefix: str = "") -> str:
    """Format SysEx data for display."""
    result = [prefix]
    for i, b in enumerate(data):
        result.append(f"{nybble_char(b >> 4)}{nybble_char(b & 0xf)} ")
        if (i & 0xf) == 0xf:
            result.append("\n")
    return "".join(result) 