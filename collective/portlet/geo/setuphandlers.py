import random

from zope.component import getUtility
from zope.component import queryAdapter

from plone.registry.record import Record
from plone.registry.interfaces import IRegistry
from plone.registry.interfaces import IPersistentField

from .interfaces import ISettings


def create_update_token(context):
    registry = getUtility(IRegistry)

    for name, value in (
        ('update_token', u"%016x" % random.getrandbits(128)),
        ('url', u"http://software77.net/geo-ip?DL=1"),
        ):
        field = ISettings[name]
        persistent_field = queryAdapter(field, IPersistentField)
        key = ISettings.__identifier__ + "." + field.__name__
        registry.records.setdefault(key, Record(persistent_field, value))
