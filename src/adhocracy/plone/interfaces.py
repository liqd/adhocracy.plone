from zope import interface
from zope import schema


class IAddOnInstalled(interface.Interface):

    """Marker interface for browser layers."""


class IAdhocracyStaticPagesRootRegistry(interface.Interface):

    """Plone Registry entry to list map object path to adhocarcy url."""

    roots = schema.List(title=u"Adhocracy static pages root to adhocracy url"
                              u" mapping",
                        default=[u"adhocracy|https://adhocracy.de/static/"],
                        value_type=schema.TextLine(title=u"path|url"))
