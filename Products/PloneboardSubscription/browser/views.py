from Products import Five
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from plone.app.layout.viewlets import ViewletBase
from zope.component import getMultiAdapter
from zope.component.interfaces import ComponentLookupError
from ..NotificationTool import ID
from Products.CMFCore.utils import getToolByName
from StringIO import StringIO


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

class SubscriberList(ViewletBase):

    def get_list(self):
        tool = getToolByName(self.context, ID)
        out = StringIO()
        for obj in tool.subscribers:
            print >> out, obj, tool.subscribers[obj]
        return out.getvalue()

    def render(self):
        #self.response.setHeader("Content-Type", "text/xml;charset=utf-8")
        self.request.response.setHeader("Content-Disposition", "attachment;filename=myfilename.csv")
        self.request.response.write(self.get_list())
