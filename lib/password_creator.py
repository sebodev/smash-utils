""" creates passwords """
import string, random

def create(length):
    if length is None:
        length = 16
    chars = string.ascii_letters + string.digits + string.punctuation
    chars = chars.replace('"', "").replace("'", "").replace("=", "").replace("`", "").replace("\\", "")
    password = ''.join((random.SystemRandom().choice(chars)) for i in range(length))
    return password
