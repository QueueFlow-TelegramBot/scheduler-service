import string
import random


def generate_room_id(length: int = 5) -> str:
    """Generate a short alphanumeric room ID like 'aB3xQ'."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choices(alphabet, k=length))
