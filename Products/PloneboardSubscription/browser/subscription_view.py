from Products import Five
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter

class SubscriptionView(Five.BrowserView):

    @property
    def portal_catalog(self):
        return getMultiAdapter((self.context,self.request),name=u"plone_tools").catalog()

    @property
    def portal_membership(self):
        return getMultiAdapter((self.context,self.request),name=u"plone_tools").membership()

    def getPending(self):
        user = self.portal_membership.getAuthenticatedMember().getId()

        pb_tool = getToolByName(self.context, 'portal_pbnotification')
        #1 - get every object subscriptable
        brains = self.portal_catalog.searchResults(portal_type=['PloneboardForum', 'PloneboardConversation'], sort_on='modified', sort_order='reverse')
        #2 - get subscription for this user
        return [brain for brain in brains if pb_tool.checkSubscriberId(brain.getPath(), user)]
        
    def getUser(self):
        return self.portal_membership.getAuthenticatedMember().getUserName()
        
