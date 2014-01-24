from plone.app.caching.operations.default import StrongCaching
from plone.caching.interfaces import ICachingOperationType
from zope.interface import classProvides


class StaticResource(StrongCaching):

    classProvides(ICachingOperationType)

    maxage = None
    smaxage = 84000
