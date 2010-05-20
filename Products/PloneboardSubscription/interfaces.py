from zope.interface import Interface, Attribute

class INotificationTool(Interface):
    """
    Provides subscription for Ploneboard objects like forum and conversation
    """

    def addSubscriber(object, user):
        """     
        This method adds a user to the notification list
        """     

    def delSubscriber(object, user):
        """     
        This method deletes a user from the notification list
        """     

    def notify():
        """     
        This method notifies all the subscribers of changes
        """     
