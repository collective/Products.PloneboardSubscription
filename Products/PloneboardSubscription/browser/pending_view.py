from Products import Five
from Products.CMFCore.utils import getToolByName

class PendingView(Five.BrowserView):

     def getPending(self):
         pb_tool = getToolByName(self.context, 'portal_pbnotification')
         #pb_tool.pending
         return []

