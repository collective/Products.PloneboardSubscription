import re
import inspect
import logging
from time import time
from email.Header import Header

from types import StringType

from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from ZODB.POSException import ConflictError
from OFS.PropertyManager import PropertyManager
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList

from AccessControl import Unauthorized
from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl.PermissionRole import rolesForPermissionOn

from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.Expression import Expression

from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Ploneboard.interfaces import IForum, IConversation, IComment

ID = 'portal_pbnotification'
TITLE = 'Ploneboard Notification tool'
META_TYPE = 'PloneboardNotificationTool'

LOG = logging.getLogger('PloneboardNotification')

EMAIL_ADDRESS_IN_HEADER_REGEXP = re.compile('(?:\s*,\s*)?(.*?) <(.*?)>')
EMAIL_REGEXP = re.compile('^[0-9a-zA-Z_&.%+-]+@([0-9a-zA-Z]([0-9a-zA-Z-]*[0-9a-zA-Z])?\.)+[a-zA-Z]{2,6}$')
MAIL_HOST_META_TYPES = ('MockMailHost', 'Secure Maildrop Host', 'Maildrop Host', 'Secure Mail Host', 'Mail Host', )

class NotificationTool(UniqueObject, SimpleItem, PropertyManager):
    """Main notification tool."""
    id = ID
    title = TITLE
    meta_type = META_TYPE

    manage_options = (PropertyManager.manage_options
                      + SimpleItem.manage_options)
    ## Debug mode
    debug_mode = False
    send_interval = 10
    last_sent = ''

    mail_template = """Dear Plone portal Member:

There is new activity in the conversation(s) that you have subscribed to.
Please follow the following link(s) to view the latest update:

[URLS]

Note: If you no longer want to receive update notices for this conversation,
follow the link above and click on the Unsubscribe link at the bottom of the
page after logging in.
"""

    mail_template = mail_template.split('\n')

    _properties = (
                   {'id': 'debug_mode',
                    'label': 'Toggle debug mode',
                    'mode': 'w',
                    'type': 'boolean'},
                   {'id': 'send_interval',
                    'label': 'send_interval',
                    'mode': 'w',
                    'type': 'int'},
                   {'id': 'last_sent',
                    'label': 'last_sent',
                    'mode': 'w',
                    'type': 'str'},
                   {'id': 'mail_template',
                    'label': 'mail template',
                    'mode': 'w',
                    'type': 'lines'},
                  )

    security = ClassSecurityInfo()
    decPrivate = security.declarePrivate
    decProtected = security.declareProtected
    decPublic = security.declarePublic

    def __init__(self, *args, **kwargs):
        self.subscribers = PersistentMapping()
        self.pending = PersistentList()

    def addSubscriber(self, obj, user):
        """ adds user """
        obj_id = self.getObjId(obj)
        if obj_id not in self.subscribers:
            self.subscribers[obj_id] = PersistentList()
        if user not in self.subscribers[obj_id]:
            LOG.info('Adding obj %s to user %s', obj_id, user)
            self.subscribers[obj_id].append(user)

    def checkSubscriber(self, obj):
        """ checks user """
        mtool = getToolByName(self, 'portal_membership')
        user = mtool.getAuthenticatedMember().getId()
        return self.checkSubscriberId(self.getObjId(obj), user)

    def checkSubscriberId(self, obj_id, user):
        """ checks user """
        if obj_id not in self.subscribers:
            return False
        return user in self.subscribers[obj_id]

    def getObjId(self, obj):
        """ gets obj id """
        return '/'.join(obj.getPhysicalPath())

    def delSubscriber(self, obj, user):
        """ deletes user """
        obj_id = self.getObjId(obj)
        if self.checkSubscriberId(obj_id, user):
            LOG.info('Removing obj %s to user %s', obj_id, user)
            self.subscribers[obj_id].remove(user)
            if len(self.subscribers[obj_id]) == 0:
                del self.subscribers[obj_id]

    def onItemModification(self, obj):
        """ sends notifications """
        self.pending.append(obj)
        now = int(time())
        if self.last_sent and (now - self.last_sent) < self.send_interval:
            return
        self.process_pending()
        self.last_sent = now
        self.pending = PersistentList()

    def process_pending(self):
        """ sends notifications """
        notify = {}
        for obj in self.pending:
            creator = obj.Creator()
            conv = obj.getConversation()
            forum = conv.getForum()
            conv_id = self.getObjId(conv)
            forum_id = self.getObjId(forum)
            if forum_id in self.subscribers:
                for n1 in self.subscribers[forum_id]:
                    if n1 == creator:
                        continue
                    if n1 not in notify:
                        notify[n1] = []
                    notify[n1].append(conv_id)
            if conv_id in self.subscribers:
                for n1 in self.subscribers[conv_id]:
                    if n1 == creator:
                        continue
                    if n1 not in notify:
                        notify[n1] = []
                    if conv_id not in notify[n1]:
                        notify[n1].append(conv_id)
        for n1 in notify:
            email = self.getEmailAddress(n1)
            if email:
                message = self.createMessage(notify[n1])
                self.sendNotification(email, message)
        
    def createMessage(self, conv):
        """Return email addresses of ``user``."""
        portal = getToolByName(self, 'portal_url').getPortalObject()
        portal_id = '/' + portal.getId()
        urls = '\n'.join(['%s%s' % (portal.absolute_url(), c1.replace(portal_id, '')) for c1 in conv])
        msg = list(self.mail_template)
        for i in range(len(msg)):
            if msg[i].startswith('[URLS]'):
                msg[i] = urls
        return '\n'.join(msg)

    def getEmailAddress(self, user):
        """Return email addresses of user

        - if the value is not an e-mail, suppose it is an user id and
        try to get the email property of this user;

        - remove bogus e-mail addresses.
        """
        mtool = getToolByName(self, 'portal_membership')
        member = mtool.getMemberById(str(user))
        if member is not None:
            user = member.getProperty('email', '')
        if user and EMAIL_REGEXP.match(user):
            return user
        return None

    def sendNotification(self, address, message):
        """Send ``message`` to all ``addresses``."""
        for m in MAIL_HOST_META_TYPES:
            mailhosts = self.superValues(m)
            if mailhosts: break
        if not mailhosts:
            raise MailHostNotFound
        mailhost = mailhosts[0]

        ptool = getToolByName(self, 'portal_properties').site_properties
        encoding = ptool.getProperty('default_charset', 'utf-8')
        message = self.encodeMailHeaders(message, encoding)

        if self.getProperty('debug_mode'):
            LOG.info('About to send this message to %s: \n%s',
                     address, message)

        n_messages_sent = 0
        this_message = ('To: %s\n' % address) + message
        this_message = this_message.encode(encoding)
        try:
            mailhost.send(this_message)
            n_messages_sent += 1
        except ConflictError:
            raise
        except:
            LOG.error('Error while sending '\
                      'notification: \n%s' % this_message,
                      exc_info=True)
        return n_messages_sent

    def encodeMailHeaders(self, message, encoding):
        """Return ``message`` with correctly encoded headers.

        The following headers are encoded: ``From``, ``Reply-to``,
        ``Sender``, ``Cc`` and ``Subject``.
        """
        mout = []
        lines = message.split('\n')
        for line_i in range(0, len(lines)):
            line = lines[line_i]
            if not line:
                break ## End of headers block.
            header = line[:line.find(':')]
            if header.lower() in ('from', 'reply-to', 'sender',
                                  'cc', 'subject'):
                value = line[len(header) + 1:].lstrip()
                if header.lower() in ('from', 'reply-to', 'sender', 'cc'):
                    ## We must not encode e-mail addresses.
                    addresses = EMAIL_ADDRESS_IN_HEADER_REGEXP.findall(value)
                    if addresses:
                        addresses = [(Header(s, encoding).encode(), addr) \
                                     for s, addr in addresses]
                        value = ', '.join(['%s <%s>' % (s, addr) \
                                           for (s, addr) in addresses])
                else:
                    value = Header(value, encoding).encode()
                mout.append('%s: %s' % (header, value))
                continue
            mout.append(line)
        mout.extend(lines[line_i:])
        return '\n'.join(mout)

InitializeClass(NotificationTool)
