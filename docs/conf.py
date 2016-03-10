#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

# Path munging
sys.path.insert(0, os.path.abspath('..'))

# Extensions
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 'sphinx.ext.autosummary']
autodoc_member_order = 'bysource'

autosummary_generate = True

intersphinx_mapping = {
    'python': ('http://docs.python.org/3.5', None)
}

# Templates
templates_path = ['_templates']
master_doc = 'index'

# Metadata
project = u'agate'
copyright = u'2016, Christopher Groskopf'
version = '1.3.1'
release = '1.3.1'

exclude_patterns = ['_build']
pygments_style = 'sphinx'

# HTMl theming
html_theme = 'default'

on_rtd = os.environ.get('READTHEDOCS', None) == 'True'

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme
    html_theme = 'sphinx_rtd_theme'
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

html_static_path = ['_static']
htmlhelp_basename = 'agatedoc'
