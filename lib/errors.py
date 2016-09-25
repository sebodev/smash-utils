class SmashException(Exception):
    """General exception that can be used anywhere in the program"""

    def __init__(self, title, message=None):
        """pass in either a title and an error message, or just an error message """
        if message and title:
            super(SmashException, self).__init__("\n\n"+title+": "+self.message)
        else:
            super(SmashException, self).__init__(title)
