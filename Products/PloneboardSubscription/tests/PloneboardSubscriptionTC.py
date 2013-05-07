from Testing import ZopeTestCase

# Make the boring stuff load quietly
ZopeTestCase.installProduct('SimpleAttachment')
ZopeTestCase.installProduct('CMFPlacefulWorkflow')
ZopeTestCase.installProduct('Ploneboard')
ZopeTestCase.installProduct('collective.MockMailHost')
ZopeTestCase.installProduct('PloneboardSubscription')

from Products.PloneTestCase import PloneTestCase

PloneTestCase.setupPloneSite(products=('SimpleAttachment', 'CMFPlacefulWorkflow', 'Ploneboard',
                                       'collective.MockMailHost', 'PloneboardSubscription', ))

from Products.Five.testbrowser import Browser

class FunctionalTestCase(PloneTestCase.FunctionalTestCase):
    
    class Session(dict):
        def set(self, key, value):
            self[key] = value

    def _setup(self):
        PloneTestCase.FunctionalTestCase._setup(self)
        self.app.REQUEST['SESSION'] = self.Session()
        self.browser = Browser()
        self.browser.handleErrors = False
        self.portal.error_log._ignored_exceptions = ()
        self.portal.left_slots = self.portal.right_slots = []
        mailhost = self.portal.MailHost
        from collective.MockMailHost.MockMailHost import MockMailHost
        # Checking if MailHost is a MockMailost object. Not always the case!
        if not isinstance(mailhost, MockMailHost):
            from collective.MockMailHost.setuphandlers import replace_mailhost
            replace_mailhost(self.portal)
        self.portal.portal_pbnotification.send_interval = 0
