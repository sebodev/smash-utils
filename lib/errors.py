class SmashException(Exception):
    """General exception that can be used anywhere in the program"""

    def __init__(self, title, message=None):
        """pass in either a title and an error message, or just an error message """
        if message and title:
            self.title = title
            self.message = message
            super(SmashException, self).__init__("\n"+"-"*80+"\n"+title+": "+self.message)
        else:
            self.message = title
            super(SmashException, self).__init__(title)

class CredentialsNotFound(SmashException):
    """used by the lib.passwords module when searching for a password and it cannot be found"""
    def __init__(self, *args, **kwargs):
        super(CredentialsNotFound, self).__init__(*args, **kwargs)

class LoginError(SmashException):
    def __init__(self, *args, **kwargs):
        super(LoginError, self).__init__(*args, **kwargs)

class SSHError(SmashException):
    """ Raised when an SSH command returns a non-zero exit status.
    One of the subprocess error could still be raised if the command fails for some other reason """
    def __init__(self, *args, **kwargs):
        super(SSHError, self).__init__(*args, **kwargs)
