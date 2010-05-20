"""Event handlers for CMFNotification."""

import logging
from Products.CMFCore.utils import getToolByName

LOG = logging.getLogger('PloneboardNotification')

from Products.PloneboardSubscription.NotificationTool import ID

def onObjectEditedEvent(obj, event):
    """Subscriber for ObjectModifiedEvent"""
    ntool = getToolByName(obj, ID, None)
    if ntool is not None:
        ntool.onItemModification(obj)
    LOG.info('FIRING event for obj %s', '/'.join(obj.getPhysicalPath()))
