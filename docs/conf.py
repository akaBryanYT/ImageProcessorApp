import os
import sys
sys.path.insert(0, os.path.abspath('..')) # Point to project root relative to docs dir

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Image Processor App'
copyright = '2025, Bryan Chavez, Nicolas Desprez'
author = 'Bryan Chavez, Nicolas Desprez'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',   # Core Sphinx extension for docstrings
    'sphinx.ext.napoleon',  # If using Google/NumPy style docstrings
    'sphinx.ext.viewcode',  # Link to source code
    'sphinx.ext.githubpages', # Helper for GitHub Pages deployment
    'sphinx.ext.intersphinx', # Optional: Link to other projects' docs (e.g., Python, Flask)
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
