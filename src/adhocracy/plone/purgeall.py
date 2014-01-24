from zope.interface import implements
from zope.component import adapts

from z3c.caching.interfaces import IPurgePaths

from Products.CMFCore.interfaces import IContentish

class PurgeAllPaths(object):
    """Purge view taht clears the varnish proxy cache!

    It send a purge request with the following URL: /PURGE_ALL.
    Your need the right varnish config to make use of this.

    """
    implements(IPurgePaths)
    adapts(IContentish)

    def __init__(self, context):
        self.context = context

    def getRelativePaths(self):
        return []

    def getAbsolutePaths(self):
        return ['/PURGE_ALL']
