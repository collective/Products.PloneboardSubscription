Description
===========

Products.PloneboardSubscription enables users to subscribe/unsubscribe to email
notification to a Ploneboard forum or a particular conversation,

and has an option to automatically add as subscriber a member adding a comment to a conversation.

A "Subscribe/Unsubscribe" link is provided on the forum or conversation
and if the user chooses to subscribe, any further comments made to the forum
or conversation triggers an email.

Configuration
=============

The product creates a tool "portal_pbnotification" at the Plone site which contains some
parameters that can be set:

* debug mode : if checked, mail is not sent but only logged !
* send interval : in seconds. The email contains modifications done during the last send interval.
* last sent : int time of the last send verification (not to be manually changed...)
* html mail format : must be checked if the email template contains html.
* mail template : the mail template can be plain text or html.
    The following special parts will be replaced:
        * [PORTAL_TITLE] : by the portal title
        * [URLS] : by the modified conversation urls
        * [FORUMS] : by the modified conversation urls and the corresponding forum (only in html format)
        * [COMMENTS] : by the modified conversation urls, the corresponding forum and the new comments (only in html format)
* auto_subscribe : if checked, each member adding a comment will be added in the conversation subscribers list. 