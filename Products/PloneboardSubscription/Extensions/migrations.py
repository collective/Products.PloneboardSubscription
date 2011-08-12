# -*- coding: utf-8 -*-
#utilities
def check_role(self, role='Manager', context=None):
    from Products.CMFCore.utils import getToolByName
    pms = getToolByName(self, 'portal_membership')
    return pms.getAuthenticatedMember().has_role(role, context)

def check_zope_admin():
    from AccessControl.SecurityManagement import getSecurityManager
    user = getSecurityManager().getUser()
    if user.has_role('Manager') and user.__module__ == 'Products.PluggableAuthService.PropertiedUser':
        return True
    return False

###############################################################################

def subscribe_comment_owner(self):
    """
        This script adds comment owners as conversation subscribers.
        It is intended to be done before using auto_subscribe functionality.
    """
    from Products.CMFCore.utils import getToolByName
    from persistent.list import PersistentList

    if not check_role(self):
        return "You must have a manager role to run this script"

    out = []

    portal_url = getToolByName(self, "portal_url")
    pbn = getToolByName(self, 'portal_pbnotification')
    portal = portal_url.getPortalObject()

    kw = {}
    kw['portal_type'] = ('PloneboardConversation')

    results = portal.portal_catalog.searchResults(kw)
    out.append("%d conversations found\n"%len(results))
    for r in results :
        conv = r.getObject()
        conv_id = pbn.getObjId(conv)
        for com in conv.getComments():
            if conv_id not in pbn.subscribers:
                pbn.subscribers[conv_id] = PersistentList()
            creator = com.Creator().decode('utf8')
            if creator not in pbn.subscribers[conv_id]:
                pbn.subscribers[conv_id].append(creator)
    return "\n".join(out)
