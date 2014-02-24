from AccessControl.unauthorized import Unauthorized
from Products.Five.browser import BrowserView
from Products.CMFPlone.browser.navtree import DefaultNavtreeStrategy
from StringIO import StringIO
from bs4 import BeautifulSoup
from lxml import etree
from plone.app.layout.navigation.navtree import buildFolderTree
from plone.app.blocks.tiles import renderTiles
from plone.app.contenttypes.interfaces import ILink
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

    def _get_data(self):
        items = self.request.get("QUERY_STRING", "").split("&")
        data = {}
        data_ = [tuple(item.split("=")) for item in items if "=" in item]
        base = [(k, v) for k, v in data_ if k == 'base']
        data['base'] = urllib.unquote(base[0][1]).strip('/') if base else ''
        path = [(k, v) for k, v in data_ if k == 'path']
        data['path'] = urllib.unquote(path[0][1]).strip('/') if path else ''
        data['langs'] = [urllib.unquote(v) for k, v in data_ if k == 'lang']
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
        data = self._get_data()
        response_data = {}
        for lang in data['langs']:
            try:
                response_data = query_items(self.context,
                                            '/'.join([lang, data['base']]))
                if "title" in response_data:
                    break
            except KeyError:
                continue
        if data['langs'] == [] or response_data == {}:
            raise KeyError
        return response_data

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
        view = None
        link = None
        response_data = {}
        lang = u''
        data = self._get_data()
        if data['langs'] == [] or data['path'] == '':
            raise KeyError
        if data['path'].startswith("author/")\
                or data['path'].startswith("sitemap"):
            view = self.context.restrictedTraverse(data['path'])
        else:
            for lang in data['langs']:
                try:
                    item = self.context\
                        .restrictedTraverse("/".join([lang, data['path']]))
                    lang = lang
                    if item is not None:
                        break
                except (KeyError, TraversalError):
                    pass
            if item is None:
                raise KeyError
        if ILink.providedBy(item):
            link = item
            item = None
        response_data['lang'] = lang
        response_data['private'] = False

        html = ''
        tree = None
        redirect_url = u''
        if link:
            portal_state = link.restrictedTraverse("@@plone_portal_state")
            if "${navigation_root_url}" in link.remoteUrl:
                navigation_root_url = portal_state.navigation_root_url()
                redirect_url = link.remoteUrl.replace("${navigation_root_url}",
                                                      navigation_root_url)
            elif "${portal_url}" in link.remoteUrl:
                portal_url = portal_state.portal_url()
                redirect_url = link.remoteUrl.replace("${portal_url}",
                                                      portal_url)
            else:
                redirect_url = link.remoteUrl
        if view:
            html = view()
        if item:
            default_page_view = getMultiAdapter((item, self.request),
                                                name="default_page")
            default_page = default_page_view.getDefaultPage()
            item = item[default_page] if default_page else item

            viewname = item.getLayout() or item.getDefaultLayout()
            view = None
            try:
                view = getMultiAdapter((item, self.request), name=viewname)
            except ComponentLookupError:
                viewname = 'view'
                view = getMultiAdapter((item, self.request), name=viewname)
            view.request.URL = item.absolute_url() + "/" + viewname
            view.request.response.setHeader('Content-Type', 'text/html')
            view.request['plone.app.blocks.enabled'] = True
            html_no_tiles = view()
            parser = etree.HTMLParser()
            tree = etree.parse(StringIO(html_no_tiles), parser)
            renderTiles(view.request, tree)
            html = etree.tostring(tree.getroot(), method="html",
                                  pretty_print=True)

        soup = BeautifulSoup(html)

        css_classes_soup = soup.body['class'] if soup.body else None
        response_data['css_classes'] = css_classes_soup\
            if css_classes_soup else []
        column_r_soup = soup.find(id='portal-column-two')
        response_data['column_right'] = column_r_soup.encode('utf-8').strip()\
            if column_r_soup else u''
        nav_soup = soup.find(id='portal-globalnav')
        response_data['nav'] = nav_soup.encode('utf-8').strip()\
            if nav_soup else u''

        content_soup = soup.find(id="content")
        remove_ids = ['plone-document-byline']
        for id_ in remove_ids:
            tag = content_soup.find(id=id_) if content_soup else None
            if tag:
                tag.extract()
        title_soup = content_soup.find(class_='documentFirstHeading')\
            if content_soup else None
        response_data['title'] = title_soup.extract().get_text().strip()\
            if title_soup else u''
        descr_soup = content_soup.find(class_='documentDescription')\
            if content_soup else None
        response_data['description'] = descr_soup.extract().get_text().strip()\
            if descr_soup else u''
        response_data['body'] = content_soup.encode("utf-8").strip()\
            if content_soup else u''
        response_data['redirect_url'] = redirect_url

        return response_data

    def __call__(self, single=False):
        """rendering for staticpages or staticpages/single"""
        try:
            if single:
                response_data = self.staticpages_single()
            else:
                response_data = self.staticpages()
            self.request.response.setHeader('Content-Type',
                                            'application/json;;charset="utf-8"'
                                            )
            self.request.response.setStatus(200)
            return json.dumps(response_data)
        except (KeyError, AttributeError, Unauthorized, TraversalError):
            self.request.response.setStatus(400)
            self.request.response.setHeader('Content-Type', 'application/json;'
                                            ';charset="utf-8"')
            return json.dumps({'errors': []})

    def __call_single__(self):
        """call staticpages/single renderer"""
        return self.__call__(single=True)

    def __getitem__(self, name):
        """custom traversal to allow to render staticpages/single"""
        if name != "single":
            raise KeyError
        return self.__call_single__
