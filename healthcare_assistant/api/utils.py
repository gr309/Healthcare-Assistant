import re
from django.contrib.auth.models import User
def generate_username(email) :
    base = email.split('@')[0]
    existing_usernames = User.objects.filter(username__startswith=base).values_list('username', flat=True)
    if base not in existing_usernames:
        return base

    suffixes = []
    pattern = re.compile(r'^' + re.escape(base) + r'(\d+)$')
    for username in existing_usernames:
        match = pattern.match(username)
        if match:
            suffixes.append(int(match.group(1)))

    max_suffix = 0
    if suffixes:
        max_suffix = max(suffixes)
    
    return f"{base}{max_suffix+1}"
