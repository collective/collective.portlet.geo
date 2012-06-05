from zope.interface import Interface
from zope import schema

from .i18n import MessageFactory as _


class ISettings(Interface):
    url = schema.TextLine(
        title=_(u"Database URL"),
        description=_(u"The URL that points to the GZIP-compressed database. "
                      u"If this field is left blank, a snapshot distributed "
                      u"with the add-on package will be used for the update."),
        required=False,
        )

    update_token = schema.TextLine(
        title=_(u"Update token"),
        description=_(u"This token allows an anonymous user to prompt "
                      u"the system to update the geolocation database."),
        readonly=True,
        required=False,
        )
