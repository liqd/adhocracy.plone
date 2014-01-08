import json
from plone.app.layout.navigation.navtree import buildFolderTree
from plone.app.layout.navigation.navtree import NavtreeStrategyBase
from Products.CMFPlone.browser.navtree import SitemapNavtreeStrategy, DefaultNavtreeStrategy

from AccessControl.unauthorized import Unauthorized
from zope.traversing.interfaces import TraversalError
from Products.Five.browser import BrowserView
import plone.api


def query_items(root, path, query={}):
    """
    Return a navtree of portal_catalog queried items in their natural order.

    @param path: INavigationRoot content object

    @param path: Path relative to INavigationRoot to set the query path

    @param query: Dictionary of portal_catalog query parameters

    @return: Navtree dictionary

    @raises: KeyError if path is not available
    """
    # Apply default search filters
    absolute_path = '/'.join(root.getPhysicalPath() + (path.strip('/'),))
    applied_query = {
        'sort_on': 'getObjPositionInParent'
    }
    # Apply caller's filters
    applied_query.update(query)
    # Set the navigation tree build strategy
    strategy = DefaultNavtreeStrategy(root)
    strategy.rootPath = absolute_path
    strategy.showAllParents = False
    # This will yield out tree of nested dicts of item brains
    navtree = buildFolderTree(root, root, applied_query, strategy=strategy)

    def cleanup(child):
        """ Recursively cleanup the tree """
        children = child.get('children', [])
        for childchild in children:
            cleanup(childchild)
        cleaned = {u'title': child['Title'], u'name': child['id'],
                   u'children': children}
        child.clear()
        child.update(cleaned)

    if "id" in navtree:
        cleanup(navtree)
    else:
        raise KeyError
    return navtree


class StaticPagesView(BrowserView):

    def _get_validated_data(self):
        base = ''
        lang = ''
        data = self._get_data()
        # validate lang parameter
        for key, value in data:
            if key == 'lang' and value in self.context:
                lang = value.strip('/')
                break
        # validate base parameter
        for key, value in data:
            if key == 'base':
                base = value.strip('/')
                break
        if lang == '':
            raise KeyError
        return (base, lang)

    def _get_data(self):
        items = self.request.get("QUERY_STRING", "").split("&")
        data = [tuple(item.split("=")) for item in items if "=" in item]
        return data

    def __call__(self):
        self.request.response.setHeader('Content-Type',
                                        'application/json;;charset="utf-8"')
        try:
            base, lang = self._get_validated_data()
            response_data = query_items(self.context, '/'.join([lang, base]))
            return json.dumps(response_data)
        except KeyError:
            self.request.response.setStatus(400)
            return json.dumps({'errors': []})
