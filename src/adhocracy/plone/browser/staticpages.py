from AccessControl.unauthorized import Unauthorized
from Acquisition import aq_base
from Acquisition import aq_inner
from Products.Five.browser import BrowserView
from Products.CMFPlone.browser.navtree import DefaultNavtreeStrategy
from bs4 import BeautifulSoup
from plone.app.layout.navigation.navtree import buildFolderTree
from zope.component import getMultiAdapter
from zope.component import ComponentLookupError 
from zope.traversing.interfaces import TraversalError

import json
import urllib


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

    def _staticpages_validated_data(self):
        base = ''
        lang = ''
        data = self._get_data()
        # validate lang parameter
        for key, value in data:
            if key == 'lang' and value in self.context:
                lang = urllib.unquote(value).strip('/') 
                break
        # validate base parameter
        for key, value in data:
            if key == 'base':
                base = urllib.unquote(value).strip('/')
                break
        if lang == '':
            raise KeyError
        return (base, lang)

    def _staticpages_single_validated_data(self):
        path = ''
        lang = ''
        data = self._get_data()
        # validate lang parameter
        for key, value in data:
            if key == 'lang' and value in self.context:
                lang = urllib.unquote(value).strip('/')
                break
        # validate path parameter
        for key, value in data:
            if key == 'path':
                path = urllib.unquote(value).strip('/')
                break
        if lang == '' or path == '':
            raise KeyError
        return (path, lang)

    def _get_data(self):
        items = self.request.get("QUERY_STRING", "").split("&")
        data = [tuple(item.split("=")) for item in items if "=" in item]
        return data

    def staticpages(self):
        """staticpages View

        Context: INavigationRoot content

        Get parameter:

            * lang: language folder, multiple allowed to set fallback, required
            * base: path to root item relative to the lang folder

        Traverse to the content under lang/base and return navtree dictionary
        of all children.

        @return: JSON dictio nary with navtree information

        """
        self.request.response.setHeader('Content-Type',
                                        'application/json;;charset="utf-8"')
        try:
            base, lang = self._staticpages_validated_data()
            response_data = query_items(self.context, '/'.join([lang, base]))
            return json.dumps(response_data)
        except KeyError:
            self.request.response.setStatus(400)
            return json.dumps({'errors': []})

    def staticpages_single(self):
        """saticpages/single View

        Context: INavigationRoot content

        Get parameter:

            * lang: language folder, multiple allowed to set fallback, required
            * path: path to item relative to the lang folder

        Traverse to the content under lang/path and return the rendered html
        of the default view.

        @return: JSON dictionary with html representation

        """
        item = None
        data = {}
        try:
            path, lang = self._staticpages_single_validated_data()
            item = self.context.restrictedTraverse("/".join([lang, path]))
        except (KeyError, AttributeError, Unauthorized, TraversalError):
            self.request.response.setStatus(400)
            self.request.response.setHeader('Content-Type', 'application/json;'
                                            ';charset="utf-8"')
            return json.dumps({'errors': []})

        data['lang'] = lang
        data['private'] = False
	
	item = aq_inner(item)
	default_page = getattr(aq_base(item), 'default_page', False) 
	if default_page:
		item = item[default_page]
	viewname =  item.getLayout() or item.getDefaultLayout()
	view = None
	try:
	    view = getMultiAdapter((item, self.request), name=viewname)
	except ComponentLookupError:
	    import pdb;pdb.set_trace()
	    view = item.restrictedTraverse("view")
	item_html = view.__of__(item)()
        soup = BeautifulSoup(item_html)

        css_classes_soup = soup.body['class']
        data['css_classes'] = css_classes_soup if css_classes_soup else []
        column_r_soup = soup.find(id='portal-column-two')
        data['column_right'] = column_r_soup.encode('utf-8').strip()\
            if column_r_soup else u''
        nav_soup = soup.find(id='portal-globalnav')
        data['nav'] = nav_soup.encode('utf-8').strip()\
            if nav_soup else u''

        content_soup = soup.find(id="content")
        remove_ids = ['plone-document-byline']
        for id_ in remove_ids:
            tag = content_soup.find(id=id_)
            if tag:
                tag.extract()
        title_soup = content_soup.find(class_='documentFirstHeading')\
            if content_soup else None
        data['title'] = title_soup.extract().get_text().strip()\
            if title_soup else u''
        descr_soup = content_soup.find(class_='documentDescription')\
            if content_soup else None
        data['description'] = descr_soup.extract().get_text().strip()\
            if descr_soup else u''
        data['body'] = content_soup.encode("utf-8").strip()\
            if content_soup else u''

        self.request.response.setHeader('Content-Type',
                                        'application/json;;charset="utf-8"')
        return json.dumps(data)

    def __call__(self):
        """default rendering for staticpages"""
        return self.staticpages()

    def __getitem__(self, name):
        """custom traversal to allow to render staticpages/single"""
        if name != "single":
            raise KeyError
        else:
            return self.staticpages_single
