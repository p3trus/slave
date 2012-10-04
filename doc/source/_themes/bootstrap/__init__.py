import os

from docutils import nodes

from sphinx.locale import admonitionlabels
from sphinx.writers.html import HTMLTranslator as SphinxHTMLTranslator

class HTMLTranslator(SphinxHTMLTranslator):
  """
  Handle translating to bootstrap structure.
  """

  def visit_document(self, node):
    SphinxHTMLTranslator.visit_document(self, node)

    # used to detect that bullet_lists are for the global and page tocs
    self.is_partial = node.get('source') == '<partial node>'
    self.page_toc_position = self.builder.config.html_theme_options.get(
      'page_toc_position', 'subnav')
    self.toc_nav = self.page_toc_position == 'nav'
    self.toc_subnav = self.page_toc_position == 'subnav'
    self.toc_sidebar = self.page_toc_position.startswith('sidebar-')

    self.page_toc_handled_first = False
    if self.toc_subnav:
      self.page_toc_maxdepth = 1
    else:
      self.page_toc_maxdepth = int(
        self.builder.config.html_theme_options.get('page_toc_maxdepth', '-1'))

    self.in_subnav = False
    if not self.is_partial and self.toc_subnav:
      docname = os.path.relpath(
        node['source'],
        self.builder.env.srcdir
      ).replace(self.builder.config.source_suffix, '')
      self.page_toc = self.builder.env.get_toc_for(docname, self.builder)

      toc_empty = bool(
        not len(self.page_toc.children) or
        len(self.page_toc.children[0].children) <= 1)
      if not toc_empty:
        toc_empty = True
        for child in self.page_toc.children[0].children[1]:
          if isinstance(child, nodes.list_item):
            toc_empty = False
            break

      if not toc_empty:
        # for page toc in the subnav, skip the first list
        self.page_toc = self.page_toc.children[0].children[1]
        self.page_toc['classes'].append('nav')
      else:
        self.page_toc = None

  admonitionclasses = {
    'note': 'alert-info',
    'hint': 'alert-info',
    'tip': 'alert-info',
    'error': 'alert-error',
    'danger': 'alert-error',
  };
  def visit_admonition(self, node, name=''):
    self.body.append(self.starttag(
        node, 'div', CLASS=('alert %s' % self.admonitionclasses.get(name, ''))))
    if name and name != 'seealso':
      node.insert(0, nodes.title(name, admonitionlabels[name], classes=['alert-heading']))
    self.set_first_last(node)

  def visit_literal(self, node):
    self.body.append(self.starttag(node, 'code', ''))
  def depart_literal(self, node):
    self.body.append('</code>')

  def visit_section(self, node):
    # insert the subnav after the section heading + optional lead
    if not self.is_partial and \
       self.toc_subnav and \
       self.page_toc and \
       self.section_level == 0:
      index = 0
      children = node.children
      if len(children) and isinstance(children[0], nodes.title):
        index = 1
      if index and len(children) > 1 and 'lead' in children[1].get('classes'):
        index = 2
      node.children.insert(index, self.page_toc)

    SphinxHTMLTranslator.visit_section(self, node)

  def bullet_list_is_global(self, node):
    if isinstance(node, nodes.bullet_list):
      if not len(node):
        return False
      node = node[0]

    for classname in node.get('classes', []):
      if classname.startswith('toctree-l'):
        return True
    return False

  def bullet_list_depth(self, node):
    if not isinstance(node.parent, nodes.list_item):
      return 0

    return 1 + self.bullet_list_depth(node.parent.parent)

  def visit_bullet_list(self, node):
    if self.is_partial and len(node) and not self.bullet_list_is_global(node):
      # honor page_toc_maxdepth option
      if self.page_toc_maxdepth > -1 and \
         self.bullet_list_depth(node) > self.page_toc_maxdepth:
          raise nodes.SkipNode

      # for page toc in the nav, collapse the first list, which contains only
      # a link to the top of the page, into the next list containing the
      # first level of page sections.
      if (self.toc_nav or self.toc_sidebar) and not self.page_toc_handled_first:
        self.page_toc_handled_first = True
        if len(node.children[0].children) > 1:
          page_node = nodes.list_item('', node.children[0].children[0])
          toc_list = node.children[0].children[1]
          toc_list.insert(0, page_node)

          # required for target based scrollspy, but screws the styling.
          #if self.toc_nav:
          #  toc_list['classes'].append('nav')
          if self.toc_sidebar:
            toc_list['classes'].extend(['nav', 'nav-list'])
            page_node['classes'].append('nav-header')

          toc_list.walkabout(self)
          raise nodes.SkipNode

    atts = {}
    old_compact_simple = self.compact_simple
    self.context.append((self.compact_simple, self.compact_p))
    self.compact_p = None
    self.compact_simple = self.is_compactable(node)
    if self.compact_simple and not old_compact_simple:
      atts['class'] = 'simple'

    else:
      # continuation of visit_section handling of toc_subnav
      if not self.is_partial and self.toc_subnav and node is self.page_toc:
        self.body.append(self.starttag({'classes': ['page-toc', 'subnav', 'navbar']}, 'div'))
        self.body.append(self.starttag({'classes': ['navbar-inner']}, 'div'))
        self.in_subnav = True

      # handle toc bullet list
      elif self.is_partial and len(node):
        # page toc is in the nav, so both are
        if self.toc_nav:
          atts['class'] = 'dropdown-menu'

        # only global toc is in the nav, so see if that is what we are rendering
        elif self.bullet_list_is_global(node):
          atts['class'] = 'dropdown-menu'

      # subnav bullet list children
      elif self.in_subnav:
        atts['class'] = 'dropdown-menu'

    self.body.append(self.starttag(node, 'ul', **atts))

  def depart_bullet_list(self, node):
    SphinxHTMLTranslator.depart_bullet_list(self, node)
    if not self.is_partial and self.toc_subnav and node is self.page_toc:
      self.in_subnav = False
      self.body.append('</div>\n</div>\n')

  def visit_list_item(self, node):
    # handle toc bullet list items
    if self.is_partial:
      classes = node.get('classes')

      # page toc is in the nav, so both are
      if self.toc_nav:
        children = node.children
        if len(children) > 1:
          if isinstance(children[1], nodes.bullet_list) and len(children[1]):
            if self.bullet_list_is_global(node) or \
               self.page_toc_maxdepth < 0 or \
               self.bullet_list_depth(children[1]) <= self.page_toc_maxdepth:
              for child in children[1]:
                if isinstance(child, nodes.list_item):
                  classes.append('dropdown-submenu')
                  break

      for classname in classes[:]:
        children = node.children
        # only global toc is in the nav, so see if that is what we are rendering
        if not self.toc_nav and classname.startswith('toctree-l') and len(children) > 1:
          if isinstance(children[1], nodes.bullet_list) and len(children[1]):
            classes.append('dropdown-submenu')

        # translate sphinx 'current' class to bootstrap's 'active'
        if classname == 'current':
          classes.append('active')

    # subnav bullet list items
    elif self.in_subnav:
      children = node.children
      if len(children) > 1 and \
         isinstance(children[1], nodes.bullet_list) and \
         len(children[1]):
        node['classes'].append('dropdown')
        children[0][0]['classes'].append('subnav-toggle')

    self.body.append(self.starttag(node, 'li', ''))
    if len(node):
      node[0]['classes'].append('first')

  def visit_reference(self, node):
    if self.in_subnav and 'subnav-toggle' in node['classes']:
      toggle = nodes.raw(
        '', '<b class="dropdown-toggle caret" data-toggle="dropdown"></b>')
      toggle['format'] = 'html'
      node.append(toggle)
    SphinxHTMLTranslator.visit_reference(self, node)

def setup(sphinx):
  sphinx.config.html_translator_class = 'bootstrap.HTMLTranslator'
