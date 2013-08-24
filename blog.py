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
import datetime
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
  elif path.endswith('.ico'):
    return True
  else:
    return False

def setupNavLinkStyles(config):
    config['navHomeStyle'] = "navDefaultLinkStyle"
    config['navBlogStyle'] = "navDefaultLinkStyle"
    config['navTipsStyle'] = "navDefaultLinkStyle"
    config['navGithubStyle'] = "navDefaultLinkStyle"
    config['navConnectStyle'] = "navDefaultLinkStyle"
    config['navPanelHomeStyle'] = "navPanelDefaultLinkStyle"
    config['navPanelBlogStyle'] = "navPanelDefaultLinkStyle"
    config['navPanelTipsStyle'] = "navPanelDefaultLinkStyle"
    config['navPanelGithubStyle'] = "navPanelDefaultLinkStyle"
    config['navPanelConnectStyle'] = "navPanelDefaultLinkStyle"

    if (config['navTitle'] == 'Home') or (config['navTitle'] == 'Blog') or (config['navTitle'] == 'Tips') or (config['navTitle'] == 'Github') or (config['navTitle'] == 'Connect'):
        config['nav'+config['navTitle']+'Style'] = "navThisLinkStyle"
        config['navPanel'+config['navTitle']+'Style'] = "navPanelThisLinkStyle"


def addPage(fspath,fsrelpath,fsrootpath):
  with open(os.path.join(fspath,'post.yaml')) as configFile:
    config = yaml.load(configFile)

    # add info about the file system path to config
    config['fspath'] = fspath
    config['fsrelpath'] = fsrelpath
    config['fsrootpath'] = fsrootpath

    # set up the common navigation link styles
    setupNavLinkStyles(config)

    # add the url and map it to the proper renderer
    g.urls = g.urls + (config['postWebPath'],config['postRenderer'])

    # map the web path to the appropriate configuration dictionary
    g.pages[config['postWebPath']] = config

def addBlog(fspath,fsrelpath,fsrootpath):
    addPage(fspath,fsrelpath,fsrootpath)
    blogDirContents = os.listdir(fspath)
    for dirEntry in blogDirContents:
      dirEntry_fp = os.path.join(fspath,dirEntry)
      if os.path.isdir(dirEntry_fp):
        if 'post.yaml' in os.listdir(dirEntry_fp):
          addPage(dirEntry_fp,os.path.join(fsrelpath,dirEntry),fsrootpath)

def getPostIntro(fsPostPath,template):
  with open(os.path.join(fsPostPath,template)) as templateFile:
    templateContents = templateFile.read()
    intro = templateContents.split('<intro>',1)[1].split('</intro>',1)[0]
    return intro
  return ''
    
def previewRenderer(template,config):
    contentDict = {}
    content = []
    blogDirContents = os.listdir(config['fspath'])
    empty = True
    for dirEntry in blogDirContents:
      dirEntry_fspath = os.path.join(config['fspath'],dirEntry)
      if os.path.isdir(dirEntry_fspath):
        if 'post.yaml' in os.listdir(dirEntry_fspath):
          with open(os.path.join(dirEntry_fspath,'post.yaml')) as entryConfigFile:
            entryContent = {}
            entryConfig = yaml.load(entryConfigFile)
            entryConfig['fspath'] = dirEntry_fspath
            entryConfig['fsrelpath'] = os.path.join(config['fsrelpath'],dirEntry)
            entryConfig['fsrootpath'] = config['fsrootpath']
            year = int(entryConfig['postDate'][0:4])
            month = int(entryConfig['postDate'][4:6])
            day = int(entryConfig['postDate'][6:8])
            entryContent['postDate']= datetime.date(year,month,day).strftime("%d %B %Y")

            # there'd better be content with a <intro> tag at one of these places
            if entryConfig['contentBlocks']['narrowContent']['template'] is not None:
                entryContent['intro'] = getPostIntro(entryConfig['fspath'],entryConfig['contentBlocks']['narrowContent']['template'])
            else:
                entryContent['intro'] = getPostIntro(entryConfig['fspath'],entryConfig['contentBlocks']['wideContent']['template'])
            renderer = web.template.frender(template)
            rendered = renderer(entryConfig,entryContent)
            print type(rendered)
            print rendered
            contentDict[entryConfig['postDate']] = str(rendered)
            empty = False

    if empty:
      return '<div style="text-align:center;">Coming Soon.</div>'
    for item in sorted(contentDict.iteritems(),reverse=True):
      content.append(item[1])
    return "".join(content)

def getTemplateFileContents(templateFileFullName):
  with open(templateFileFullName) as templateFile:
      rtn = templateFile.read()
  return rtn

def getTemplateFileName(templateFileName,config):
  if templateFileName.startswith('.'):
      templateFileFullName = os.path.join(config['fspath'],templateFileName)
  else:
      templateFileFullName = os.path.join(config['fsrootpath'],templateFileName)
  return templateFileFullName

def minimalRendererWithDate(templateFile,config):
  year = int(config['postDate'][0:4])
  month = int(config['postDate'][4:6])
  day = int(config['postDate'][6:8])
  dateStr = datetime.date(year,month,day).strftime("%d %B %Y")
  renderer = web.template.frender(templateFile)
  rendered = str(renderer(config))
  return '<div style="width:100%"><div style="text-align:center;font-size:18px;font-family:sans;color:rgb(188,188,188)">'+dateStr+'</div>'+rendered+'</div>'

def minimalRenderer(templateFile,config):
  renderer = web.template.frender(templateFile)
  return renderer(config)

class homeRenderer():
  def GET(self):
    webpath = web.ctx.fullpath
    config= g.pages[webpath]
    content = {}


    for contentBlockKey in config['contentBlocks']:
        if config['contentBlocks'][contentBlockKey]['template'] is None:
            content[contentBlockKey] = "&nbsp"
        else:
            templateFileName = getTemplateFileName(config['contentBlocks'][contentBlockKey]['template'],config)
            renderFuncName = config['contentBlocks'][contentBlockKey]['templateRenderer']
            if renderFuncName is None:
                templateFileContents = getTemplateFileContents(templateFileName)
                content[contentBlockKey] = templateFileContents
            else:
                content[contentBlockKey] = globals()[renderFuncName](templateFileName,config)
    return g.outerMostTemplate(config,content)



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
    addPage(os.path.join(template_path,'home'),'/template/home',root_path)
    addPage(os.path.join(template_path,'connect'),'/template/connect',root_path)
    addPage(os.path.join(template_path,'github'),'/template/github',root_path)
    addBlog(os.path.join(template_path,'blog'),'/template/blog',root_path)
    addBlog(os.path.join(template_path,'tips'),'/template/tips',root_path)
    print g.urls
    app = web.application(g.urls, globals()).wsgifunc()
    print 'Serving on 8088...'
    wsgifunc = app
    wsgifunc = StaticMiddleware(wsgifunc,root_path=root_path)
    WSGIServer(('', 8088), wsgifunc).serve_forever()
