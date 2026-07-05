from slowapi import Limiter
from slowapi.util import get_remote_address

# Define the limiter in a central place to avoid circular imports
# between main.py and the router modules.
limiter = Limiter(key_func=get_remote_address)
