from typing import Tuple
import re

def parse_ib_reference(value: str) -> Tuple[bool, str, str]:
    s = (value or "").strip()
    if not s:
        return False, "", ""
    sl = s.lower()
    if 'srvr=' in sl and 'ref=' in sl:
        m = re.search(r'(?i)srvr\s*=\s*"?([^";]+)"?;.*?ref\s*=\s*"?([^";]+)"?', s)
        if m:
            server = m.group(1).strip('\\/ ')
            base = m.group(2).strip('\\/ ')
            return True, server, base
    if sl.startswith('/s'):
        rest = s[2:]
        if rest.startswith('\\') or rest.startswith('/'):
            rest = rest[1:]
        rest = rest.replace('/', '\\')
        parts = rest.split('\\', 1)
        server = parts[0].strip('\\/ ')
        base = (parts[1] if len(parts) > 1 else '').strip('\\/ ')
        return True, server, base
    if sl.startswith('/f'):
        path = s[2:].lstrip('\\/')
        return False, "", path
    if 'file=' in sl:
        m = re.search(r'(?i)file\s*=\s*"?([^";]+)"?', s)
        if m:
            path = m.group(1).strip()
            return False, "", path
    return False, "", s
