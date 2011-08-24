from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getMultiAdapter
from zope.interface import implements
from plone.memoize.instance import memoize
# This interface defines the configurable options (if any) for the portlet.
# It will be used to generate add and edit forms.

class ISubscriptionPortlet(IPortletDataProvider):
    pass

# The assignment is a persistent object used to store the configuration of
# a particular instantiation of the portlet.

class Assignment(base.Assignment):
    implements(ISubscriptionPortlet)
    title = u'Iscrizioni al forum'


class Renderer(base.Renderer):
    render = ViewPageTemplateFile('subscriptions.pt')
    MAX_VALUES = 5

    @memoize
    def _getPendings(self):
        subscriptions = getMultiAdapter((self.context, self.request),name=u'view_subscriptions')
        return subscriptions.getPending()

    def subscriptions(self):
        return self._getPendings()[:self.MAX_VALUES]

    def areTooMany(self):
        return len(self._getPendings()) > self.MAX_VALUES
        
class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()
