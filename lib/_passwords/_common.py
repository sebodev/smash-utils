from collections import namedtuple
from lib.errors import SmashException

class CredentialsNotFound(SmashException):
    """raised when searching for a password and it cannot be found"""
    pass

credential = namedtuple('credential', 'name host username password')
