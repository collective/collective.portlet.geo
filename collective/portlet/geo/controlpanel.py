import copy
import time
import logging
import datetime
import transaction
import hashlib
import urllib

from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from ZPublisher.HTTPResponse import status_reasons
from zExceptions import Redirect


from zope.component import getUtility
from zExceptions import Unauthorized

from plone.registry.interfaces import IRegistry


from persistent.mapping import PersistentMapping

from zope.annotation.interfaces import IAnnotations

from plone.z3cform import layout
from plone.app.registry.browser import controlpanel

from z3c.form import button
from z3c.form import field
from z3c.form import widget
from z3c.form.browser import text


from .interfaces import ISettings
from .i18n import MessageFactory as _
from .database import Software77GeoDatabase
from . import security


logger = logging.getLogger("geoportlet")


class UpdateURLWidget(text.TextWidget):
    @classmethod
    def factory(cls, field, request):
        field = copy.copy(field)

        # Update field labels
        field.title = _(u"Update URL")
        field.description = _(u"Pre-authenticated URL which updates "
                              u"the database. Note that since the database "
                              u"is large, it's recommended to update only "
                              u"once per week "
                              u"(and never at exactly midnight).")

        return widget.FieldWidget(field, cls(request))

    def render(self):
        base = self.form.context.absolute_url()
        url = base + "/@@%s-request?auth=%s&update=1" % (
            self.form.__name__,
            self.context.update_token
            )

        return u'<a href="%s">%s</a>' % (url, url)


class ControlPanelEditForm(controlpanel.RegistryEditForm):
    prefix = ""

    schema = ISettings
    fields = field.Fields(ISettings)

    fields['update_token'].widgetFactory = UpdateURLWidget.factory

    label = _(u"Geoportlet")
    description = _(u"Manage database updates.")

    buttons = button.Buttons()
    buttons += controlpanel.RegistryEditForm.buttons

    handlers = controlpanel.RegistryEditForm.handlers.copy()

    @button.buttonAndHandler(_(u"Update"), name='update')
    def handleUpdate(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return

        annotations = IAnnotations(self.context)
        storage = annotations.setdefault('geoportlet', PersistentMapping())
        database = Software77GeoDatabase(storage)

        url = data['url']
        url = url and url.encode('utf-8') or None

        try:
            count = database.update(url)
        except IOError as exc:
            IStatusMessage(self.request).addStatusMessage(
                _(u"An error occurred: ${error}.",
                  mapping={'error': exc}), "info")
        else:
            IStatusMessage(self.request).addStatusMessage(
                _(u"Database updated (${count} records read).",
                  mapping={'count': '{0:,}'.format(count)}),
                "info")

    buttons.prefix = ""


ControlPanel = layout.wrap_form(
    ControlPanelEditForm,
    controlpanel.ControlPanelFormWrapper
    )


class ControlPanelPublicRequest(ControlPanel):
    def __call__(self, auth=None):
        if auth is None:
            raise Unauthorized("Missing authentication token.")

        registry = getUtility(IRegistry)
        settings = registry.forInterface(ISettings)

        if auth != settings.update_token:
            raise Unauthorized("Bad authentication token.")

        # as unrestricted user ...
        old = security.loginAsUnrestrictedUser()
        try:
            super(ControlPanelPublicRequest, self).update()
        finally:
            security.loginAsUser(old)

        self.request.response.setHeader('Content-Type', 'text/plain')

        status = IStatusMessage(self.request)
        return "\n".join(
            "%s: %s" % (message.type.upper(), message.message)
            for message in status.show()
            )
