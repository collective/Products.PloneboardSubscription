from Products import Five
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from zope.component import getMultiAdapter
from zope.component.interfaces import ComponentLookupError
from plone.app.layout.viewlets.common import ViewletBase
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

class SubscriberCheck(ViewletBase):

    template = ZopeTwoPageTemplateFile("subscribe.pt")
    def has_any(self):
        tool = getToolByName(self.context, ID)
        my_path = '/'.join(self.context.getPhysicalPath())
        for obj in tool.subscribers:
            if my_path in obj:
                return True
        return False

    def render(self):
        checkPermission = self.context.portal_membership.checkPermission
        can_list_subscribers = checkPermission('Manage Portal', self.context)
        sub = ''
        if can_list_subscribers:
            if self.has_any():
                sub = '<a target="_blank" href="%s/list_subscribers">Show Subscribers</a>' % self.context.absolute_url()
            else:
                sub = 'No Subscribers'
        if self.context.meta_type in ['PloneboardForum', 'PloneboardConversation']:
            return sub + self.template()
        else:
            return sub

class SubscriberList(Five.BrowserView):

    def get_list(self):
        tool = getToolByName(self.context, ID)
        out = StringIO()
        my_path = '/'.join(self.context.getPhysicalPath())
        for obj in tool.subscribers:
            if my_path in obj:
                print >> out, obj, tool.subscribers[obj]
        return out.getvalue()

    def __call__(self):
        self.request.response.setHeader("Content-Type", "text/csv;charset=utf-8")
        #self.request.response.setHeader("Content-Disposition", "attachment;filename=myfilename.csv")
        self.request.response.write(self.get_list())
