from Products import Five
from Products.CMFCore.utils import getToolByName

class Subscribe(Five.BrowserView):

     def __call__(self):
         pb_tool = getToolByName(self.context, 'portal_pbnotification')
         mtool = getToolByName(self.context, 'portal_membership')
         mem = mtool.getAuthenticatedMember().getId()
         pb_tool.addSubscriber(self.context, mem)
         self.request.response.redirect(self.context.absolute_url() + '#subscribe')


class Unsubscribe(Five.BrowserView):

     def __call__(self):
         pb_tool = getToolByName(self.context, 'portal_pbnotification')
         mtool = getToolByName(self.context, 'portal_membership')
         mem = mtool.getAuthenticatedMember().getId()
         pb_tool.delSubscriber(self.context, mem)
         self.request.response.redirect(self.context.absolute_url() + '#subscribe')
