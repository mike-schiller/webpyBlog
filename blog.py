#!/usr/bin/python
"""A web.py application powered by gevent"""


from gevent import monkey; monkey.patch_all()
from gevent.pywsgi import WSGIServer
from gevent.event import AsyncResult
import gevent
import time
import web
import httplib
import sys
import traceback
import json
from gevent import spawn
import string
import posixpath
import urllib
import os
import yaml
#from darts.lib.utils.lru import LRUDict

class g():
  urls = ()
  pages = {}
  outerMostTemplate = None

# post_name_directory
#   post.yaml
#      postName
#      postNameColor
#      postNameBackgroundColor
#   post.png
#   postBody.html
#   images/

def pathIsImage(path):
  path=path.lower()
  if path.endswith('.png'):
    return True
  elif path.endswith('.jpg'):
    return True
  elif path.endswith('.gif'):
    return True
  elif path.endswith('.jpeg'):
    return True
  else:
    return False


def addPage(fspath,fsrelpath):
  #here is where we would open the yaml and set up the renderer
  with open(os.path.join(fspath,'post.yaml')) as configFile:
    config = yaml.load(configFile)
    config['fspath'] = fspath
    config['fsrelpath'] = fsrelpath
    renderClass = config['postRenderer']
    g.urls = g.urls + (config['postWebPath'],renderClass)
    g.pages[config['postWebPath']] = config

class homeRenderer():
  def GET(self):
    webpath = web.ctx.fullpath
    config= g.pages[webpath]
    return g.outerMostTemplate(config)



class StaticMiddleware():
    """Serving Static Files."""
    def __init__(self, app, prefix='/static/', root_path=''):
        self.app = app
        self.prefix = prefix
        self.root_path = root_path

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        path = self.normpath(path)

        if (path.startswith(self.prefix)) or (pathIsImage(path)):
            print "TRYING TO HANDLE"
            environ["PATH_INFO"] = path
            print environ["PATH_INFO"]
            return web.httpserver.StaticApp(environ, start_response)
        else:
            return self.app(environ, start_response)

    def normpath(self, path):
        path2 = posixpath.normpath(urllib.unquote(path))
        if path.endswith("/"):
            path2 += "/"
        return path2

if __name__ == "__main__":
    root_path = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(root_path,'template')
    static_path = os.path.join(root_path,'static')
    g.outerMostTemplate = web.template.frender(os.path.join(static_path,'outer.html'))
    addPage(os.path.join(template_path,'home'),'/template/home')
    print g.urls
    app = web.application(g.urls, globals()).wsgifunc()
    print 'Serving on 8088...'
    wsgifunc = app
    wsgifunc = StaticMiddleware(wsgifunc,root_path=root_path)
    WSGIServer(('', 8088), wsgifunc).serve_forever()
