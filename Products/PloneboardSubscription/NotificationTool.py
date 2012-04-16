import re
import logging
from time import time
from email.Header import Header

from Globals import InitializeClass
from OFS.SimpleItem import SimpleItem
from ZODB.POSException import ConflictError
from OFS.PropertyManager import PropertyManager
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList

from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import UniqueObject
from Products.CMFCore.utils import getToolByName
from zope.i18n import translate
from Products.CMFPlone.i18nl10n import ulocalized_time

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
    auto_subscribe = False
    html_format = False
    mail_template = """Dear [PORTAL_TITLE] Member:

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
                   {'id': 'html_format',
                    'label': 'html mail format',
                    'mode': 'w',
                    'type': 'boolean'},
                   {'id': 'mail_template',
                    'label': 'mail template',
                    'mode': 'w',
                    'type': 'lines'},
                   {'id': 'auto_subscribe',
                    'label': 'auto subscribe',
                    'mode': 'w',
                    'type': 'boolean'},
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
        if self.auto_subscribe:
            # we don't check if user is already in dict because addSubscriber method do this
            mtool = getToolByName(self, 'portal_membership')
            memberid = mtool.getAuthenticatedMember().getId()
            conv = obj.getConversation()
            self.addSubscriber(conv, memberid)

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
        portal_path = getToolByName(self, 'portal_url').getPortalPath()
        for obj in self.pending:
            creator = obj.Creator()
            conv = obj.getConversation()
            if not conv:
                LOG.error('Comment: %s has no conv' % '/'.join(obj.getPhysicalPath()))
                continue
            forum = conv.getForum()
            conv_id = self.getObjId(conv)
            forum_id = self.getObjId(forum)
            convd = {}
            convd['conv'] = conv
            convd['id'] = conv_id.replace(portal_path, '', 1)
            convd['forum'] = forum
            convd['cmts'] = []
            if forum_id in self.subscribers:
                for n1 in self.subscribers[forum_id]:
                    if n1 == creator:
                        continue
                    if n1 not in notify:
                        notify[n1] = {'cvs':{}, 'key':[]}
                    if convd['id'] not in notify[n1]['key']:
                        notify[n1]['key'].append(convd['id'])
                        notify[n1]['cvs'][convd['id']] = convd
                    notify[n1]['cvs'][convd['id']]['cmts'].append(obj)
            if conv_id in self.subscribers:
                for n1 in self.subscribers[conv_id]:
                    if n1 == creator:
                        continue
                    if n1 not in notify:
                        notify[n1] = {'cvs':{}, 'key':[]}
                    if convd['id'] not in notify[n1]['key']:
                        notify[n1]['key'].append(convd['id'])
                        notify[n1]['cvs'][convd['id']] = convd
                    notify[n1]['cvs'][convd['id']]['cmts'].append(obj)

        messages = {}
        for n1 in notify:
            email, fullname = self.getEmailAddress(n1)
            if email:
                # we make the message only one time for each conversations combination
                key = ','.join(notify[n1]['key'])
                if not messages.has_key(key):
                    messages[key] = self.createMessage(notify[n1])
                self.sendNotification(email, fullname, messages[key])
        
    def createMessage(self, conversations):
        """Return email addresses of ``user``."""
        portal = getToolByName(self, 'portal_url').getPortalObject()
        portal_title = portal.getProperty('title').split(':')[0]        

        def formatUrls(with_forum=False, with_comment=False):
            urls = ''
            for conv_id in conversations['key']:
                convd = conversations['cvs'][conv_id]
                title = convd['conv'].Title()
                if with_forum:
                    title = '%s: %s'%(convd['forum'].Title(), title)
                if self.html_format:
                    urls += '<h3><a href="%s%s">%s</a></h3>\n' % (portal.absolute_url(), conv_id, title)
                else:
                    urls += '%s%s\n' % (portal.absolute_url(), conv_id)
                if with_comment:
                    comments = ''
                    for comment in convd['cmts']:
                        creatorinfo = portal.portal_membership.getMemberInfo(comment.Creator())
                        urls += '<li style="padding-left:2em;"><strong>%s %s %s %s</strong><br />\n'%(translate('posted_by', 'ploneboard', context=self.REQUEST, default='Posted by').encode('utf8'), creatorinfo is not None and creatorinfo['fullname'] or comment.Creator(), translate('text_at', 'ploneboard', context=self.REQUEST, default='at').encode('utf8'), ulocalized_time(comment.creation_date, long_format=True, context=self, request=self.REQUEST).encode('utf8'))
                        urls += '%s\n</li>\n'%comment.getText()
                    urls += '<ul>\n%s\n</ul>' % comments
            return urls

        msg = list(self.mail_template)
        for i in range(len(msg)):
            if msg[i].find('[PORTAL_TITLE]') >= 0:
                msg[i] = msg[i].replace('[PORTAL_TITLE]', portal_title)
            if msg[i].find('[URLS]') >= 0:
                msg[i] = msg[i].replace('[URLS]', formatUrls())
            if msg[i].find('[FORUMS]') >= 0:
                msg[i] = msg[i].replace('[FORUMS]', formatUrls(with_forum=True))
            if msg[i].find('[COMMENTS]') >= 0:
                msg[i] = msg[i].replace('[COMMENTS]', formatUrls(with_comment=True))
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
            fullname = member.getProperty('fullname', '')
        if user and EMAIL_REGEXP.match(user):
            return user, fullname
        return None

    def sendNotification(self, address, fullname, message):
        """Send ``message`` to all ``addresses``."""
        for m in MAIL_HOST_META_TYPES:
            mailhosts = self.superValues(m)
            if mailhosts: break
        if not mailhosts:
            raise MailHostNotFound
        mailhost = mailhosts[0]

        ptool = getToolByName(self, 'portal_properties').site_properties
        portal = getToolByName(self, 'portal_url').getPortalObject()
        portal_title = portal.getProperty('title').split(':')[0]
        email_from_name = portal.getProperty('email_from_name')
        email_from_address = portal.getProperty('email_from_address')
        encoding = ptool.getProperty('default_charset', 'utf-8')

        n_messages_sent = 0
        this_message = """From: %s <%s>
To: %s <%s>
Subject: %s Forum Notification
%s
""" % (email_from_name, email_from_address, fullname.decode(encoding), address, portal_title.decode(encoding), message.decode(encoding))
        this_message = self.encodeMailHeaders(this_message, encoding)
        this_message = this_message.encode(encoding)

        if self.getProperty('debug_mode'):
            LOG.info('About to send this message to %s: \n%s',
                     address, this_message)
            return 0

        msg_type = 'text/plain'
        if self.html_format:
            msg_type = 'text/html'
        try:
            mailhost.send(this_message, msg_type=msg_type)
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
