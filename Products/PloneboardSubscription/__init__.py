"""Product initialization."""

from Products.CMFCore import utils as CMFCoreUtils
from zope.i18nmessageid import MessageFactory
PSMessageFactory = MessageFactory('PloneboardSubscription')

def initialize(context):
    import NotificationTool
    tools = (NotificationTool.NotificationTool, )
    CMFCoreUtils.ToolInit(NotificationTool.META_TYPE,
                          tools=tools,
                          icon='tool.gif').initialize(context)
