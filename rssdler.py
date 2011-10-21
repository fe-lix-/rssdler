#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""An RSS broadcatching script 
(podcasts, videocasts, torrents, or, if you really wanted, web pages."""

from __future__ import division

__version__ = u"0.4.2"

__author__ = u"""lostnihilist <lostnihilist _at_ gmail _dot_ com> or 
"lostnihilist" on #libtorrent@irc.worldforge.org"""
__copyright__ = u"""RSSDler - RSS Broadcatcher
Copyright (C) 2007, 2008, lostnihilist

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; under version 2 of the license.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details."""

import codecs
import ConfigParser
import cookielib
import email
import getopt
import httplib
import logging
import mimetypes
import operator
import os
import pickle
try: import random
except ImportError: random = None
import re
import signal
import sgmllib
import socket
import StringIO
import sys
import time
import traceback
import urllib
import urllib2
import urlparse
try: import xml.dom.minidom as minidom
except ImportError: minidom = None

if not sys.path.count(''): sys.path.insert(0, '') 

import feedparser
try: import mechanize
except ImportError: mechanize = None

# # # # #
# == Globals ==
# # # # #
# Reminders of potential import globals elsewhere.
resource = None #daemon
userFunctions = None
sqlite3 = None #Firefox3 cookies

# Rest of Globals
configFile = os.path.expanduser(os.path.join('~','.rssdler', 'config.txt'))
downloader = None
rss = None
saved = None
MAXFD = 1024
_action = None
_configInstance = None
_runOnce = None
_USER_AGENT = u"RSSDler %s" % __version__
# ~ defined helps with feedburner feeds
percentQuoteDict = {u'!': u'%21', u' ': u'%20', u'#': u'%23', u'%': u'%25', 
  u'$': u'%24', u"'": u'%27', u'&': u'%26', u')': u'%29', u'(': u'%28', 
  u'+': u'%2B', u'*': u'%2A', u',': u'%2C', u'=': u'%3D', u'@': u'%40', 
  u';': u'%3B', u':': u'%3A', u']': u'%5D', u'[': u'%5B', u'?': u'%3F', 
  u'!':u'%7E'}
percentunQuoteDict = dict(((j,i) for (i,j) in percentQuoteDict.items()))
netscapeHeader= """# HTTP Cookie File
# http://www.netscape.com/newsref/std/cookie_spec.html
# This is a generated file!  Do not edit.\n\n"""
commentConfig = u"""# default config filename is config.txt in ~/.rssdler
# lines (like this one) starting with # are comments and 
# will be ignored by the config parser
# the only required section (though the program won't do much without others)
# sections are denoted by a line starting with [
# then the name of the section, then ending with ]
# so this is the global section
[global]
# download files to this directory. Defaults to the working directory.
downloadDir = /home/user/downloads

# makes this the 'working directory' of RSSDler. anytime you specify a filename
# without an absolute path, it will be relative to this, this s the default:
workingDir = /home/user/.rssdler

# if a file is smaller than this, it will not be downloaded. 
# if filesize cannot be determined, this is ignored. 
# Specified in MB. Remember 1024 MB == 1GB
# 0 means no minimum, as does "None" (w/o the quotes)
minSize = 10

# if a file is larger than this, it will not be downloaded.  Default is None
# though this line is ignored because it starts with a #
# maxSize = None

# write messages to a log file. 0 is off, 1 is just error messages, 
# 3 tells you when yo download something, 5 is very, very wordy. (default = 0)
log = 0
# where to write those log messages (default 'downloads.log')
logFile = downloads.log

# like log, only prints to the screen (errors to stderr, other to stdout)
# default 3
verbose = 3

# the place where a cookie file can be found. Default None.
cookieFile = /home/user/.mozilla/firefox/user/cookies.txt

# type of cookie file to be found at above location. default MozillaCookieJar
cookieType = MozillaCookieJar
# other possible types are:
# LWPCookieJar, Safari, Firefox3, KDE
# only works if urllib = False and mechanize is installed
# cookieType = MSIECookieJar

#how long to wait between checking feeds (in minutes). Default 15.
scanMins = 10

# how long to wait between http requests (in seconds). Default 0
sleepTime = 2

# to exit after scanning all the feeds, or to keep looping. Default False.
runOnce = True

# set to true to avoid having to install mechanize. 
# side effects described in help. Default False.
# will fallback to a sane value if mechanize is not installed
urllib = True

# the rest of the global options are described in the help,
# let's move on to a thread

###################
# each section represents a feed, except for the one called global. 
# this is the thread: somesite
###################
[somesite]
# just link to the feed
link = http://somesite.com/rss.xml

# Default None, defers to maxSize in global, otherwise,
# files larger than this size (in MB) will not be downloaded
# only applies to the specific thread
# if set to 0, means no maximum and overrides global option
maxSize = 2048

# like maxSize, only file smaller than this will not be downloaded
# if set to 0, means no minimum, like maxSize. in MB.
minSize = 10

# if specified, will download files in this thread to this directory
directory = /home/user/someotherfiles

# if you do not know what regular expressions are, stop now, do not pass go, 
# do not collect USD200 (CAN195)
# google "regular expressions tutorial" and find one that suits your needs
# one with an emphasis on Python may be to your advantage

# Now, without any of the download<x> or regEx options (detailed below)
# every item in the rss feed will be downloaded, 
# provided that it has not previously been downloaded
# all the regular expression should be specified in lower case 
# (except for character classes and other special regular expression characters,
#  if you know what that means)
# as the string that it is searched against is set to lower case.
# Starting with regExTrue (RET)
# let's say we want to make sure there are two numbers,
# separated by something not a number
# for everything we download in this thread.
regExTrue = \d[^\d]+\d
# the default value, None, makes RET ignored
# regExTrue = None

# but we want to make sure we don't get anything with nrg or ccd in the name
# because those are undesirable formats, but we want to make sure to not match
# a name that may have those as a substring e.g. enrgy 
# (ok, not a great example, come up with something better and I'll include it)
# REF from now on (\b indicates a word boundary)
regExFalse = (\bnrg\b|\bccd\b)
# the default value, which means it will be ignored
# regExFalse = None

# at this point, as long as the file gets a positive hit in RET 
# and no hit in REF, the file will be downloaded
# equivalently said, RET and REF are necessary and sufficient conditions.
# lengthy expressions can be constructed
# to deal with every combination of things you want, but there is 
# a looping facility to allow us to get more fine grained control
#  over the items we want to grab without having to have hundreds 
# of characters on a single line, which of course gets rather unreadable

# making use of this looping facility makes RET and REF neccessary 
# (though that can be bypassed too, more later) conditions
# however, they are no longer sufficient....
# download<x> is like regExTrue, but begins the definition of an 'item' and 
# we can associate further actions with it if we so choose
# put a non-negative integer where <x> goes
download1 = ubuntu
# but say we love ubuntu, and want to always grab everything that mentions it
# so we want to ignore regExTrue, this 'bypasses' RET when set to False. 
# Default True.
download1True = False

# we could also bypass REF. but we really don't like nrg, 
# but we'll deal with ccd's, just for ubuntu
# to be clear, download<x>False is a mixed type option,
# taking both True, False for dealing with the global REF 
# or a string (like here) to specify what amounts to a 'localized REF',
# which effectively says False to the global REF
# while at the same time specifying the local REF
download1False = \\bnrg\\b

# with %()s interpolation, we can effectively add on to REF in a basic manner
# say for Ubuntu, we don't want want the 'hoary version, 
download1False = hoary.*%(regExFalse)s
# this will insert the value for regExFalse in place of the %()s expression
# resulting in: hoarsy.*(\bnrg\b|\bccd\b)
# note the parantheses are there b/c they are in the original REF

# we don't want to download things like howto, md5 files, etc, 
# so we can set a minSize (MB)
# this overrides the global/thread minSize when not set to None
# Default None. works like thread-based minSize.
# a maxSize option is also available
download1MinSize = 10
download1MaxSize = 750

# and finally, we can put our ubuntu stuff in a special folder, if we choose
download1Dir = /home/user/ubuntustuff

# note that the numbers are not important
# as long as the options correspond to each other
# there is no download2, and that is ok.
download3 = fedora

# you have to have the base setting to have the other options
# this will not work b/c download4 is not specified
# download4Dir = /home/user/something
"""
configFileNotes = u"""There are two types of sections: global and threads. 
There can be as many thread sections as you wish, but only one global section.
global must be named "global." Threads can be named however you wish, 
except 'global,' and each name should be unique. 
With a couple of noted exceptions, there are three types of options:
    
Boolean Options: 'True' is indicated by "True", "yes", or "1". 
    "False" is indicated by "False", "no", or "0" (without the quotes)
Integer Options: Just an integer. 1, 2, 10, 2348. Not 1.1, 2.0, 999.3 or 'a'.
String Options: any string, should make sense in terms of the option 
    being provided (e.g. a valid file/directory on disk; url to rss feed)

Required indicates RSSDler will not work if the option is not set. 
Recommended indicates that the default is probably not what you want. 
Optional is not necessarily not recommended, just each case determines use 

Run with --comment-config to see what a configuration file would look like.
    e.g. rssdler --comment-config > .config.txt.sample
"""
cliOptions = u"""Command Line Options:
    --config/-c can be used with all the options except --comment-config, --help
    --comment-config: Prints a commented config file to stdout
    --help/-h: print the short help message (command line options)
    --full-help/-f: print the complete help message (quite long)
    --run/-r: run according to the configuration file
    --runonce/-o: run only once then exit
    --daemon/-d: run in the background (Unix-like only)
    --kill/-k: kill the currently running instance (may not work on Windows)
    --config/-c: specify a config file (default %s).
    --list-failed: Will list the urls of all the failed downloads
    --purge-failed: Use to clear the failed download queue. 
        Use when you have a download stuck (perhaps removed from the site or 
        wrong url in RSS feed) and you no longer care about RSSDler attempting 
        to grab it. Will be appended to the saved download list to prevent 
        readdition to the failed queue.
        Should be used alone or with -c/--config. Exits after completion.
    --list-saved: Will list everything that has been registered as downloaded.
    --purge-saved: Clear the list of saved downloads, not stored anywhere.
    --state/-s: Will return the process ID if another instance is running with.
        Otherwise exits with return code 1
        Note for Windows: will return the pid found in daemonInfo,
        regardless of whether it is currently running.
    --set-default-config: [No longer available. Deprecated]
""" % configFile
nonCoreDependencies = u"""Non-standard Python libraries used:
    feedparser: [REQUIRED] http://www.feedparser.org/
    mechanize: [RECOMMENDED] http://wwwsearch.sourceforge.net/mechanize/
    For debian based distros: 
    "sudo apt-get install python-feedparser python-mechanize"
"""
securityIssues = u"""Security Note: 
    I keep getting notes about people running as root. DO NOT DO THAT!
    """
# # # # #
#Exceptions
# # # # #
class Locked( Exception ):
    def __init__(self, value=u"""An lock() on savefile failed.""" ):
      self.value = value
    def __str__(self): return repr( self.value)

# # # # #
#String/URI Handling
# # # # #
def unicodeC( s ):
    if not isinstance(s, basestring):
        try:
            s= unicode(s) # __str__ for exceptions etc
        except:
            s= unicode(s.__str__(), errors='ignore')

    if isinstance(s, str): s = unicode(s, 'utf-8', 'replace')
    if not isinstance(s, unicode): 
        raise UnicodeEncodeError(u'could not encode %s to unicode' % s)
    return s
    
def xmlUnEscape( sStr, percent=0, pd=percentunQuoteDict ):
    u"""xml unescape a string, by default also checking for percent encoded 
    characters. set percent=0 to ignore percent encoding. 
    can specify your own percent quote dict 
    (key, value) pairs are of (search, replace) ordering with percentunQuoteDict
    """
    sStr = sStr.replace("&lt;", "<")
    sStr = sStr.replace("&gt;", ">")
    if percent: sStr = percentUnQuote( sStr, pd )
    sStr = sStr.replace("&amp;", "&")
    return sStr

def percentIsQuoted(sStr, testCases=percentQuoteDict.values()):
    u"""does not include query string or page marker (#) in detection. 
    these seem to cause the most problems.
    Specify your own test values with testCases
    """
    for i in testCases:
        if sStr.count(i): return True
    return False

def percentNeedsQuoted(sStr, testCases=percentQuoteDict.keys()):
    u"""if there is a character in the path part of the url that is 'reserved'
    """
    for aStr in urlparse.urlparse(sStr)[:4]:
        for i in testCases:
            if aStr.count(i): return True
    return False

def percentUnQuote( sStr, p=percentunQuoteDict, reserved=('%25',) ):
    u"""percent unquote a string. 
    reserved is a sequence of strings that should be replaced last.
      it needs have a key in p, with a value to replace it with. will be
      replaced in order of the sequence"""
    for search in p:
        if search in reserved: continue
        sStr = sStr.replace( search, p[search] )
    for search in reserved:
        sStr = sStr.replace( search, p[search])
    return sStr

def percentQuote(sStr, urlPart=(2,), pd=percentQuoteDict):
    u"""quote the path part of the url. 
    urlPart is a sequence of parts of the urlunparsed entries to quote"""
    urlList = list( urlparse.urlparse(sStr) )
    for i in urlPart:   urlList[i] = urllib.quote( urlList[i].encode('utf-8') )
    return unicodeC(urlparse.urlunparse( urlList ))

def unQuoteReQuote( url, quote=1 ):
    u"""fix urls from feedparser. they are not always properly unquoted 
    then unescaped. will requote by default"""
    logging.debug(u"unQuoteReQuote %s" % url)
    if percentIsQuoted(url): url = xmlUnEscape( url, 1 )
    else: url = xmlUnEscape( url, 0 ) 
    if quote: url = percentQuote( url )
    return url

def encodeQuoteUrl( url, encoding='utf-8'):
    u"""take a url, percent quote it, if necessary and encode the string 
    to encoding, default utf-8"""
    if not percentIsQuoted(url) and percentNeedsQuoted(url):
        logging.debug( u"quoting url: %s" % url)
        url = percentQuote( url )
    logging.debug( u"encoding url %s" % url)
    try: url = url.encode(encoding)
    except UnicodeEncodeError: 
        logging.critical( ''.join((traceback.format_exc(),os.linesep,url)))
        return None
    return url

class htmlUnQuote(sgmllib.SGMLParser):
    from htmlentitydefs import entitydefs
    def __init__(self, s=None):
        sgmllib.SGMLParser.__init__(self)
        self.result = ""
        if s: self.feed(s)
    def handle_entityref(self, name):
        if self.entitydefs.has_key(name): x = ';'
        else: x = ''
        self.result = "%s&%s%s" % (self.result, name, x)
    def handle_data(self, data):
        if data: self.result += data
def natsorted(seq, case=False):
    """Returns a copy of seq, sorted by natural string sort. local is faster
    Inner functions modified from: 
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/285264"""
    def try_int(s):
      "Convert to integer if possible."
      try: return int(s)
      except (TypeError, ValueError): return s
    def natsort_key(s): return map(try_int, re.findall(r'(\d+|\D+)', s))
    def natcmp(a, b): return cmp(natsort_key(a), natsort_key(b))
    def natcmpcase(a,b): return natcmp(a.lower(), b.lower())
    if case: return sorted(seq, cmp=natcmpcase)
    else: return sorted(seq, cmp=natcmp)
# # # # #
# Network Communication
# # # # #
def getFilenameFromHTTP(info, url):
    u"""info is an http header from the download,
    url is the url to the downloaded file (responseObject.geturl() )."""
    filename = None
    logging.debug(u"determining filename")
    filename = email.message_from_string(unicodeC(info).encode('utf-8')).get_filename(failobj=False)
    if filename:
        m = htmlUnQuote(filename)
        if m.result: filename = m.result
        logging.debug(u"filename from content-disposition header")
        return unicodeC( filename )
    logging.debug(u"filename from url")
    filename = percentUnQuote( urlparse.urlparse( url )[2].split('/')[-1] )
    try: typeGuess = info.gettype()
    except AttributeError: typeGuess = None
    typeGuess1 = mimetypes.guess_type(filename)[0]
    if typeGuess and typeGuess1 and typeGuess == typeGuess1: pass
    elif typeGuess: # trust server content-type over filename
        logging.debug(u"getting extension from content-type header")
        fileExt = mimetypes.guess_extension(typeGuess)
        if fileExt:         # sloppy filename guess, probably will never get hit
            if not filename: 
                logging.debug(u"""never guessed filename, just setting it to the\
 time""")
                filename = unicodeC( int(time.time()) ) + fileExt
            else: filename += fileExt
    elif 'content_type' not  in info:
            msg = (
u"""Proper file extension could not be determined for the downloaded file: 
%s you may need to add an extension to the file for it to work in some programs.
 It came from url %s. It may be correct, but I have no way of knowing due to 
 insufficient information from the server.""" % (filename, url) )
            logging.critical( msg)
    if not filename: 
        logging.critical('Could not determine filename for torrent from %s' % url)
        return None
    if filename.endswith('.obj'): filename = filename[:-4]
    return unicodeC( filename)

def convertMoz3ToNet(cookie_file):
  """modified from: 
  https://addons.mozilla.org/en-US/firefox/discussions/comments.php?DiscussionID=8623"""
  conn = sqlite3.connect(cookie_file)
  cur = conn.cursor()
  cur.execute("""SELECT host, path, isSecure, expiry, name, value FROM \
moz_cookies;""")
  s = StringIO.StringIO(netscapeHeader)
  s.seek(0,2)
  s.writelines( "%s\tTRUE\t%s\t%s\t%d\t%s\t%s\n" % (row[0], row[1],
      unicode(bool(row[2])).upper(), row[3], unicode(row[4]), unicode(row[5]))
      for row in cur.fetchall())
  conn.close() 
  s.seek(0)
  return s

def convertSafariToMoz(cookie_file):
  "convert Safari cookies to a Netscape/Mozilla/Firefox format"
  if not minidom: 
    raise ImportError('xml.dom.minidom needed for use of Safari Cookies')
  s = StringIO.StringIO(netscapeHeader)
  s.seek(0,2)
  try: x = minidom.parse(cookie_file)
  except IOError: # No xml parsing errors caught.
    logging.critical('Cookie file faied to load. Please check for correct path')
    s.seek(0)
    return s
  for cookie in x.getElementsByTagName('dict'):
    d = {}
    for key in cookie.getElementsByTagName('key'):
      keyText = key.firstChild.wholeText.lower()
      try: valueText = key.nextSibling.nextSibling.firstChild.wholeText
      except AttributeError: valueText = ''
      if keyText == 'domain': d['domain'] = valueText
      elif keyText == 'path': d['path'] = valueText
      elif keyText == 'expires': # ignores HH:MM:SS, etc.: 2018-02-14T15:37:51Z
        d['expires'] =str(int(time.mktime(time.strptime(valueText,'%Y-%m-%dT%H:%M:%SZ'))))
      elif keyText == 'name': d['name'] = valueText
      elif keyText == 'value': d['value'] = valueText
    else: 
      if 5 == len(set(d.keys()).intersection(('domain','path','expires','name','value'))):
        d['dspec'] = str(d['domain'].startswith('.')).upper()
        s.writelines( "%(domain)s\t%(dspec)s\t%(path)s\tFALSE\t%(expires)s\t%(name)s\t%(value)s\n" % d)
      else:
        logging.error('there was an error parsing the cookie with these values\n%s' % d)
  s.seek(0)
  return s

def convertKDEToMoz(cookie_file):
  s = StringIO.StringIO(netscapeHeader)
  s.seek(0,2)
  for line in open(cookie_file,'r').readlines():
    line = line.strip()
    if (line.startswith('#') or 
      (line.startswith('[') and line.endswith(']')) or
      line == ''):
        continue
    line = [ x.strip('"') for x in line.split() ]
    if line[1] == '': line[1] = line[0]
    del line[6], line[4], line[0] #Sec Prot Host
    line.insert(2,'FALSE')
    line.insert(1, str(line[0].startswith('.')).upper())
    s.write('\t'.join(line))
    s.write('\n')
  s.seek(0)
  return s

def cookieHandler():
    u"""tries to turn cj into a *CookieJar according to user preferences."""
    cj = None
    cType = getConfig()['global']['cookieType']
    cFile = getConfig()['global']['cookieFile']
    netMod = getConfig()['global']['urllib']
    m="Cookies disabled. RSSDler will reload the cookies if you fix the problem"
    logging.debug(u"""testing cookieFile settings""")
    if not cFile: logging.debug(u"""no cookie file configured""")
    elif netMod:
        logging.debug(u"""attempting to load cookie type: %s""" % cType)
        if cType in ['Safari', 'Firefox3','KDE']: cj = cookielib.MozillaCookieJar()
        else: cj = getattr(cookielib, cType)()
        try: 
          if cType == 'Firefox3':
            cj._really_load(convertMoz3ToNet(cFile), cFile, 0, 0)
          elif cType == 'Safari': 
            cj._really_load(convertSafariToMoz(cFile), cFile, 0, 0)
          elif cType == 'KDE':
            cj._really_load(convertKDEToMoz(cFile), cFile, 0, 0)
          else: cj.load(cFile)
        except (cookielib.LoadError, IOError):
          logging.critical( traceback.format_exc() + m)
          cj = None
        else: logging.debug(u"""cookies loaded""")
    else:
        logging.debug(u"""attempting to load cookie type: %s""" % cType)
        if cType in [ 'Safari', 'Firefox3', 'KDE']: cj = mechanize.MozillaCookieJar()
        else: cj = getattr(mechanize, cType )()
        try: 
          if cType == 'Firefox3':
            cj._really_load(convertMoz3ToNet(cFile), cFile, 0, 0)
          elif cType == 'Safari':
            cj._really_load(convertSafariToMoz(cFile), cFile, 0, 0)
          elif cType == 'KDE':
            cj._really_load(convertKDEToMoz(cFile), cFile, 0, 0)
          else: cj.load(cFile)
        except(mechanize._clientcookie.LoadError, IOError):
          logging.critical( traceback.format_exc() + m)
          cj = None
        else: logging.debug(u"""cookies loaded""")
    return cj

def urllib2RetrievePage( url, th=((u'User-agent', _USER_AGENT),)):
    u"""URL is the full path to the resource we are retrieve/Posting
    th is a sequence of (field,value) pairs of any extra headers
    """
    th = [ (x.encode('utf-8'), y.encode('utf-8')) for x,y in th ]
    time.sleep( getConfig()['global']['sleepTime'] )
    url, urlNotEncoded = encodeQuoteUrl( url, encoding='utf-8' ), url
    if not url: 
        logging.critical(u"""utf encoding, quoting url failed, returning false %s\
""" % url)
        return False
    if not urllib2._opener:
      cj = cookieHandler()
      if cj:
        logging.debug(u"building and installing urllib opener with cookies")
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj) )
      else:
        logging.debug(u"building and installing urllib opener without cookies")
        opener = urllib2.build_opener( )
      urllib2.install_opener(opener)
    logging.debug(u"grabbing page at url %s" % urlNotEncoded)
    return urllib2.urlopen(urllib2.Request(url, headers=dict(th)))

def mechRetrievePage(url, th=(('User-agent', _USER_AGENT),), ):
    u"""URL is the full path to the resource we are retrieve/Posting
    txheaders: sequence of tuples of header key, value
    """
    th = [ (x.encode('utf-8'), y.encode('utf-8')) for x,y in th ]
    time.sleep( getConfig()['global']['sleepTime'] )
    url, urlNotEncoded = encodeQuoteUrl( url, encoding='utf-8' ), url
    if not url: 
        logging.critical(u"utf encoding and quoting url failed, returning false")
        return False
    if not mechanize._opener:
      cj = cookieHandler()
      if cj:
        logging.debug(u"building and installing mechanize opener with cookies")
        opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(cj), 
          mechanize.HTTPRefreshProcessor(), mechanize.HTTPRedirectHandler(), 
          mechanize.HTTPEquivProcessor())
      else:
        logging.debug(u"building and installing mech opener without cookies")
        opener = mechanize.build_opener(mechanize.HTTPRefreshProcessor(), 
          mechanize.HTTPRedirectHandler(), mechanize.HTTPEquivProcessor())
      mechanize.install_opener(opener)
    logging.debug(u"grabbing page at url %s" % urlNotEncoded)
    return mechanize.urlopen(mechanize.Request(url, headers=dict(th)))

def getFileSize( info, data=None ):
    u"""give me the HTTP headers (info) and, 
    if you expect it to be a torrent file, the actual file, 
    i'll return the filesize, of type None if not determined"""
    logging.debug(u"determining size of file")
    size = None
    if 'torrent' in info.gettype():
        if data:
            if hasattr(data, 'read'): data = data.read()
            try: tparse = bdecode(data)
            except ValueError:
                logging.critical(''.join((traceback.format_exc() ,
u"""File was supposed to be torrent data, but could not be bdecoded""")))
                return size, data
            if 'length' in tparse['info']: size = int(tparse['info']['length'])
            elif 'files' in tparse['info']: 
              size = sum(int(j['length']) for j in tparse['info']['files'])
    else:
        try: 
            if 'content-length' in info: size = int(info['content-length'])
        except ValueError:  pass # 
    logging.debug(u"filesize seems to be %s" % size)
    return size, data

# # # # #
# Check Download
# # # # #
def searchFailed(urlTest):
    u"""see if url is in saved.failedDown list"""
    for failedItem in getSaved().failedDown:
        if urlTest == failedItem['link']: return True
    return False

def checkFileSize(size, threadName, downloadDict):
    u"""returns True if size is within size constraints specified by config file
    takes the size in bytes, threadName and downloadDict (parsed download<x>).
    """
    returnValue = True
    logging.debug(u"checking file size")
    if downloadDict['maxSize'] != None: maxSize = downloadDict['maxSize']
    elif getConfig()['threads'][threadName]['maxSize'] != None: 
        maxSize = getConfig()['threads'][threadName]['maxSize']
    elif getConfig()['global']['maxSize'] != None: 
        maxSize = getConfig()['global']['maxSize']
    else: maxSize = None
    if maxSize:
        maxSize = maxSize * 1024 * 1024
        if size > maxSize:  returnValue = False
    if downloadDict['minSize'] != None: minSize = downloadDict['minSize']
    elif getConfig()['threads'][threadName]['minSize'] != None: 
        minSize = getConfig()['threads'][threadName]['minSize']
    elif getConfig()['global']['minSize'] != None: 
        minSize = getConfig()['global']['minSize']
    else: minSize = None
    if minSize:
        minSize = minSize * 1024 * 1024
        if size <  minSize: returnValue = False
    if returnValue: logging.debug(u"size within parameters")
    else: logging.debug(u"size outside parameters")
    return returnValue

def checkRegExGTrue(tName, itemNode):
    u"""return type True or False if search matches or no, respectively."""
    if getConfig()['threads'][tName]['regExTrue']:
        logging.debug(u"checking regExTrue on %s" % itemNode['title'])
        if getConfig()['threads'][tName]['regExTrueOptions']: 
            regExSearch = re.compile(
                getConfig()['threads'][tName]['regExTrue'],
                getattr(re, getConfig()['threads'][tName]['regExTrueOptions']) | re.I )
        else: 
            regExSearch = re.compile(
                getConfig()['threads'][tName]['regExTrue'], re.I)
        if regExSearch.search(itemNode['title']): return True
        else: return False
    else: return True

def checkRegExGFalse(tName, itemNode):
    u"""return type True or False if search doesn't match or does, respectively.
    """
    if getConfig()['threads'][tName]['regExFalse']:
        logging.debug(u"checking regExFalse on %s" % itemNode['title'])
        if getConfig()['threads'][tName]['regExFalseOptions']: 
            regExSearch = re.compile(
                getConfig()['threads'][tName]['regExFalse'], 
                getattr(re, getConfig()['threads'][tName]['regExFalseOptions']) | re.I )
        else: 
            regExSearch = re.compile(
                getConfig()['threads'][tName]['regExFalse'], re.I)
        if regExSearch.search(itemNode['title']):   return False
        else: return True
    else: return True

def checkRegEx(tName, itemNode):
    u"""goes through regEx* and download<x> options to see if any of them 
    provide a positive match. Returns False if Not. 
    Returns a DownloadItemConfig dictionary if so"""
    if getConfig()['threads'][tName]['downloads']:
        LDown = checkRegExDown(tName, itemNode)
        if LDown:           return LDown
        else:           return False
    elif checkRegExGFalse(tName, itemNode) and checkRegExGTrue(tName, itemNode):
        return DownloadItemConfig()
    else:   return False

def checkRegExDown(tName, itemNode):
    u"""returns false if nothing found in download<x> to match itemNode.
    returns DownloadItemConfig instance otherwise"""
    # Also, it's incredibly inefficient
    # for every x rss entries and y download items, it runs this xy times.
    logging.debug(u"checking download<x>")
    for downloadDict in getConfig()['threads'][tName]['downloads']:
        if getConfig()['threads'][tName]['regExTrueOptions']: 
            LTrue = re.compile( downloadDict['localTrue'], 
                getattr(re, getConfig()['threads'][tName]['regExTrueOptions']) | re.I )
        else: LTrue = re.compile(downloadDict['localTrue'], re.I )
        if not LTrue.search(itemNode['title']): continue
        if type(downloadDict['False']) == type(''):
            if getConfig()['threads'][tName]['regExFalseOptions']: 
                LFalse = re.compile(downloadDict['False'],
                getattr(re, getConfig()['threads'][tName]['regExFalseOptions']) | re.I )
            else: LFalse = re.compile(downloadDict['False'], re.I)
            if LFalse.search(itemNode['title']): continue
        elif downloadDict['False'] == False: pass
        elif downloadDict['False'] == True:
            if not checkRegExGFalse(tName, itemNode): continue
        if downloadDict['True'] == True:
            if not checkRegExGTrue(tName, itemNode): continue
        elif downloadDict['True'] == False: pass
        return downloadDict
    return False

# # # # #
# Download
# # # # #
def validFileName(aStr, invalid=('?','\\', '/', '*','<','>','"',':',';','!','|','\b','\0','\t')):
    invalid = set(invalid)
    invalid.update(map(chr, range(32)))
    outStr = aStr
    for i in invalid:  
        outStr = outStr.replace(i,'')
    if not outStr: 
        raise ValueError("no characters are valid!")
    if aStr== outStr: 
        logging.debug('no replacement made to filename')
    else: 
        logging.debug('potentially illegal characters removed from filename')
    return outStr
  
def downloadFile(link=None, threadName=None, rssItemNode=None, 
    downItemConfig=None):
    u"""tries to download data at URL. returns None if it was not supposed to, 
    False if it failed, and a tuple of arguments for userFunct"""
    try: data = downloader(link)
    except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException), m: 
        logging.critical(''.join((traceback.format_exc(), os.linesep, 
          u'error grabbing url: %s' % link)))
        return False
    filename = getFilenameFromHTTP(data.info(), link)
    if not filename: return False
    size, data2 = getFileSize(data.info(), data)
    if size and not checkFileSize(size, threadName, downItemConfig): 
        del data, data2
        return None
    if downItemConfig['Dir']: directory = downItemConfig['Dir']
    elif getConfig()['threads'][threadName]['directory']: 
        directory = getConfig()['threads'][threadName]['directory']
    else: directory = getConfig()['global']['downloadDir']
    try: filename = writeNewFile( filename, directory, data2 )
    except IOError: 
        logging.critical( u"write to disk failed")
        return False
    logging.warn( u"Filename: %s%s\tDirectory: %s%s\tFrom Thread: %s%s" % ( 
        filename, os.linesep, directory, os.linesep, threadName, os.linesep ))
    if rss:
        logging.debug( u"generating rss item")
        if 'description' in rssItemNode: description =rssItemNode['description']
        else: description = None
        if 'title' in rssItemNode: title = rssItemNode['title']
        else: title = None
        pubdate = time.strftime(u"%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
        itemLoad = {'title':title ,'description':description ,'pubDate':pubdate}
        rss.addItem( itemLoad )
    userFunctArgs = (directory, filename, rssItemNode, data.geturl(), 
        downItemConfig, threadName )
    return userFunctArgs

def writeNewFile(filename, directory, data):
    u"""write a file to disk at location. won't clobber, depending on config. 
        writes to .__filename.tmp first, then moves to filename"""
    filename = validFileName(filename)
    if getConfig()['global']['noClobber']: 
        directory, filename = findNewFile( filename, directory)
        tmpPath = os.path.join( *findNewFile( u'.__' + filename + u'.tmp', 
            directory) )
    else: tmpPath = os.path.join(directory, u'.__' +  filename + u'.tmp')
    realPath = os.path.join(directory, filename)
    try:
        logging.debug(u'opening %s' % tmpPath)
        # open should handle unicode path automagically
        fd = codecs.open( tmpPath, 'wb') #'replace' ?
        if hasattr(data, 'xreadlines'):
            for piece in data.xreadlines():         fd.write(piece)
        elif hasattr(data, 'readline'):
            piece = data.readline()
            while piece:
                fd.write(piece)
                piece = data.readline()
        elif hasattr(data, 'read'): fd.write(data.read())
        else: fd.write(data)
        fd.flush()
        fd.close()
    except IOError: 
        if getConfig()['global']['noClobber'] and os.path.isfile( tmpPath ): 
            os.unlink(tmpPath)
        logging.critical(''.join((traceback.format_exc() ,
          u'Failed to write file %s in directory %s'%(filename, directory))))
        raise IOError
    logging.debug(u'moving to %s' % realPath)
    os.rename(tmpPath, realPath)
    return filename

def findNewFile(filename, directory):
    u"""find a filename in the given directory that isn't already taken. 
    adds '.1' before the file extension, 
    or just .1 on the end if no file extension"""
    if os.path.isfile( os.path.join(directory, filename) ):
        logging.error(u"""filename already taken, looking for another: %s\
""" % filename)
        filenameList = filename.split(u'.')
        if len( filenameList ) >1: 
            try: 
                num = u'.' + unicodeC( int( filenameList[-2] ) +1)
                del filenameList[-2]
                filename = (u'.'.join( filenameList[:-1] ) + num + u'.' +
                    filenameList[-1])
            except (ValueError, IndexError, UnicodeEncodeError): 
                try: 
                    num = u'.' + unicodeC( int( filenameList[-1] ) + 1 )
                    del filenameList[-1]
                    filename = u'.'.join( filenameList ) + num
                except (ValueError, IndexError, UnicodeEncodeError) : 
                    num = u'.' + unicodeC( 1 )
                    filename = ( u'.'.join( filenameList[:-1] ) + num + '.' + 
                        filenameList[-1] )
        else: filename += u'.1'
        return findNewFile( filename, directory )
    else: return unicodeC(directory), unicodeC(filename)

def bdecode(x):
        """This function decodes torrent data. 
        It comes (modified) from the GPL Python BitTorrent implementation"""
        def decode_int(x, f):
            f += 1
            newf = x.index('e', f)
            try: n = int(x[f:newf])
            except (OverflowError, ValueError):  n = long(x[f:newf])
            if x[f] == '-':
                if x[f + 1] == '0': raise ValueError
            elif x[f] == '0' and newf != f+1:  raise ValueError
            return (n, newf+1)
        def decode_string(x, f):
            colon = x.index(':', f)
            try:  n = int(x[f:colon])
            except (OverflowError, ValueError):  n = long(x[f:colon])
            if x[f] == '0' and colon != f+1:  raise ValueError
            colon += 1
            return (x[colon:colon+n], colon+n)
        def decode_list(x, f):
            r, f = [], f+1
            while x[f] != 'e':
                v, f = decode_func[x[f]](x, f)
                r.append(v)
            return (r, f + 1)
        def decode_dict(x, f):
            r, f = {}, f+1
            lastkey = None
            while x[f] != 'e':
                k, f = decode_string(x, f)
                if lastkey >= k:   raise ValueError
                lastkey = k
                r[k], f = decode_func[x[f]](x, f)
            return (r, f + 1)
        decode_func = {
          'l' : decode_list ,
          'd' : decode_dict,
          'i' : decode_int}
        for i in range(10): decode_func[str(i)] = decode_string
        if hasattr(x, 'read'): x = x.read()
        try:  r, l = decode_func[x[0]](x, 0)
        except (IndexError, KeyError):
            try: 
                x = open(x, 'r').read()
                r, l = decode_func[x[0]](x,0)
            except (OSError, IOError, IndexError, KeyError): raise ValueError
        if l != len(x):  raise ValueError
        return r
# # # # #
#Persistence
# # # # #
class FailedItem(dict):
    u"""represents an item that we tried to download, but failed, 
    either due to IOError, HTTPError, or some such"""
    def __init__(self, link=None, threadName=None, rssItemNode=None, 
        downItemConfig=None):
        u"""upgrade note: [0] = link, [1] = threadName, [2] = itemNode, [3] = 
        downloadLDir #oldnote"""
        dict.__init__(self)
        self['link'] = link
        self['threadName'] = threadName
        self['rssItemNode'] = rssItemNode
        self['downItemConfig'] = downItemConfig
    def __setstate__(self,state):
        if 'data' in state: self.update(state['data'])
        
class DownloadItemConfig(dict):
    u"""downloadDict: a dictionary representing the download<x> options. 
    keys are: 'localTrue' (corresponding to download<x>) ; 'False' ; 'True' ; 
    'Dir' ; 'minSize' ; and 'maxSize' 
    corresponding to their analogues in download<x>."""
    def __init__(self, regextrue=None, dFalse=True, dTrue=True, dir=None, 
        minSize=None, maxSize=None, Function=None):
        u"was [0] = localTrue, [1] = False, [2] = True, [3] = dir"
        dict.__init__(self)
        self['localTrue'] = regextrue
        self['False'] = dFalse
        self['True'] = dTrue
        self['Dir'] = dir
        self['minSize'] = minSize
        self['maxSize'] = maxSize
        self['Function'] = Function
    def __setstate__(self,state):
        if 'data' in state: self.update(state['data'])

class MakeRss(object):
    u"""A class to generate, and optionally parse and load, an RSS 2.0 feed. 
    Example usage:
    rss = MakeRss(filename='rss.xml')
    rss.addItem(dict)
    rss.close()
    rss.write()"""
    chanMetOpt = ['title', 'description', 'link', 'language', 
      'copyright', 'managingEditor', 'webMaster', 'pubDate', 
      'lastBuildDate', 'category', 'generator', 'docs', 'cloud', 'ttl', 
      'image', 'rating', 'textInput', 'skipHours', 'skipDays']
    itemMeta = ['title', 'link', 'description', 'author', 'category', 
      'comments', 'enclosure', 'guid', 'pubDate', 'source']
    _date_fmt = "%a, %d %b %Y %H:%M:%S GMT"
    def __init__(self, channelMeta={}, parse=False, filename=None):
        u"""channelMeta is a dictionary where the keys are the feed attributes 
        (description, title, link are REQUIRED). 
        filename sets the internal filename, where parsed feeds are parsed from 
        (by default) and the stored feed data is written to (by default).
        parse will read the xml file found at self.filename and load the data 
        into the various places
        or XML objects. The former is easier to deal with and is how RSSDler 
        works with them as of 0.3.2"""
        global minidom, random
        if not minidom: raise ImportError('minidom not imported')
        if not random: raise ImportError('random not imported')
        object.__init__(self)
        self.feed = minidom.Document()
        self.rss = self.feed.createElement('rss')
        self.rss.setAttribute('version', '2.0')
        self.channel = self.feed.createElement('channel')
        self.channelMeta = channelMeta
        self.filename = filename
        self.items = []
        self.itemsQuaDict = []
        if parse: self.parse()
    def loadChanOpt(self):
        u"""takes self.channelMeta and  turns it into xml 
        and adds the nodes to self.channel. Will only add those elements which 
        are part of the rss standard (aka those elements in self.chanMetOpt. 
        If you add to this list, you can override what is allowed
        to be added to the feed."""
        if 'title' not in self.channelMeta: 
          self.channelMeta['title'] = 'Title Not Specified'
        if 'description' not in self.channelMeta: 
          self.channelMeta['description'] = 'No Description'
        if 'link' not in self.channelMeta: 
          self.channelMeta['link'] = 'http://nolinkgiven.com'
        for key in self.chanMetOpt:
          if key in self.channelMeta: 
            self.channel.appendChild(self.makeTextNode(key, self.channelMeta[key]))
    def makeTextNode(self, nodeName, nodeText, nodeAttributes=()):
        """returns an xml text element node, 
        with input being the name of the node, text, 
        and optionally node attributes as a sequence
        of tuple pairs (attributeName, attributeValue)
        """
        node = self.feed.createElement(nodeName)
        text = self.feed.createTextNode(unicodeC(nodeText))
        node.appendChild(text)
        for attribute, value in nodeAttributes: 
          node.setAttribute(attribute, value)
        return node
    def makeItemNode(self, itemAttr={}, action='insert'):
        """Generates xml ItemNodes from a Dictionary. 
        Only allows elements in RSS specification. 
        Overridden by adding elements to self.itemMeta. 
        Should not need to call directly unless action='return'.
        action: 
            insert: put at 0th position in list.
            return: do not attach to self.items at all, just return the XML object.
        """
        if 'title' not in itemAttr: itemAttr['title'] = 'no title given'
        if 'description' not in itemAttr: itemAttr['description'] = 'not given'
        if 'pubdate' not in itemAttr and 'pubDate' not in itemAttr:
            if 'updated_parsed' in itemAttr: 
                try: itemAttr['pubDate'] = itemAttr['pubdate'] = time.strftime(self._date_fmt, itemAttr['updated_parsed'])
                except TypeError: itemAttr['pubDate'] = time.strftime(self._date_fmt, time.gmtime())
            elif 'updated' in itemAttr: itemAttr['pubDate'] = itemAttr['pubdate'] = itemAttr['updated']
            else: itemAttr['pubDate'] = itemAttr['pubdate'] = time.strftime(self._date_fmt, time.gmtime())
        if 'guid' not in itemAttr: 
          itemAttr['guid'] = random.randint(10000,1000000000)
        if 'link' not in itemAttr or not itemAttr['link']: 
          itemAttr['link'] = itemAttr['guid']
        item = self.feed.createElement('item')
        for key in self.itemMeta:
          if key in itemAttr: 
            item.appendChild(self.makeTextNode(key, itemAttr[key]))
        if action.lower() == 'insert':  self.items.insert(0, item)
        elif action.lower() == 'return': return item
    def appendItemNodes(self, length=20):
        """adds the items in self.items to self.channel. starts at the front"""
        for item in reversed(self.itemsQuaDict): self.makeItemNode(item) 
        if length==0: 
          for item in self.items: self.channel.appendChild(item)
        else: 
          for item in self.items[:length]: self.channel.appendChild(item)
    def close(self, length=20):
        u"""takes care of taking the channelMeta data and the items 
        (dictionary or XML), and putting it all together in self.feed"""
        self.loadChanOpt()
        self.appendItemNodes(length=length)
        self.rss.appendChild(self.channel)
        self.feed.appendChild(self.rss)
    def parse(self, filename=None, rawfeed=None, parsedfeed=None, itemsonly=False):
        """give parse a raw feed (just the xml/rss file, unparsed) and 
        it will fill in the class attributes, and allow you to modify the feed.
        Or give me a feedparser.parsed feed (parsedfeed) and I'll do the same"""
        if filename:
            if not os.path.isfile(filename): return None
            p = feedparser.parse(filename)
        elif rawfeed:   p = feedparser.parse(rawfeed)
        elif parsedfeed: p = parsedfeed
        elif self.filename:
            if not os.path.isfile(self.filename):               return None
            p = feedparser.parse(self.filename)
        else: raise Exception, "Must give either a rawfeed, filename, set self.filename, or parsedfeed"
        if not itemsonly:
            if 'updated' in p['feed']: 
              p['feed']['pubDate'] = p['feed']['pubdate']  =p['feed']['updated']
            elif 'updated_parsed' in p['feed']: 
                p['feed']['pubDate'] = p['feed']['pubdate']  = time.strftime(self._date_fmt, p['feed']['updated_parsed'])
            self.channelMeta = p['feed']
        self.itemsQuaDict.extend(p['entries'])
    def _write(self, data, fd):
        fd.write( data.toxml() )
        fd.flush()
    def write(self, filename=None, file=None):
        """Writes self.feed to a file, default self.filename. 
        If fed filename, will write and close self.feed to file at filename.
        if fed file, will write to file, but closing it is up to you"""
        if file: self._write(self.feed, file)
        elif filename:
            outfile = codecs.open(filename, 'w', 'utf-8', 'replace')
            self._write(self.feed, outfile)
            outfile.close()
        else:
            outfile = codecs.open(self.filename, 'w', 'utf-8', 'replace')
            self._write(self.feed, outfile)
            outfile.close()
    def addItem(self, newItem):
        """newItem is a dictionary representing an rss item. 
        Use this method to add new items to the object,"""
        self.itemsQuaDict.insert(0, newItem)
    def delItem(self, x=0):
        u"""returns what should be the last added item to the rss feed. 
        Or specify which item to return"""
        self.itemsQuaDict.pop(x)

class GlobalOptions(dict):
    u"""    
    downloadDir: [Recommended] A string option. Default is workingDir. 
        Set to a directory where downloaded files will go.
    workingDir: [Optional] A string option. Default is ${HOME}/.rssdler.
        Directory rssdler switches to, relative paths are relative to this
    minSize: [Optional] An integer option. Default None. Specify, in MB.
        the minimum size for a download to be. 
        Files less than this size will not be saved to disk.
    maxSize: [Optional] An integer option. Default None. Specify, in MB.
        the maximum size for a download to be. 
        Files greater than this size will not be saved to disk.
    log: [Optional] An integer option. Default 0. Write meassages a log file 
        (specified by logFile). See verbose for what options mean.
    logFile: [Optional] A string option. Default downloads.log. Where to log to.
    verbose: [Optional] An integer option, Default 3. Lower decreases output. 
        5 is absurdly verbose, 1 is major errors only. 
        Set to 0 to disable. Errors go to stderr, others go to stdout.
    cookieFile: [Optional] A string option. Default 'None'. The file on disk, 
        in Netscape Format (requires headers)(unless otherwise specified) 
        that has cookie data for whatever site(s) you have set that require it.
    cookieType: [Optional] A string option. Default 'MozillaCookieJar.' 
        Possible values (case sensitive): 'MozillaCookieJar', 'LWPCookieJar', 
        'MSIECookieJar', 'Firefox3', 'Safari', 'KDE'. Only mechanize supports MSIECookieJar.
        Program will exit with error if you try to use urllib and MSIECookieJar.
        Firefox3 requires that you use Python 2.5+, specifically sqlite3 must be
          available.
        Safari requires xml.dom.minidom and is experimental
    scanMins: [Optional] An integer option. Default 15. Values are in minutes. 
        The number of minutes between scans.
        If a feed uses the <ttl> tag, it will be respected. 
        If you have scanMins set to 10 and the site sets <ttl>900</ttl> 
        (900 seconds; 15 mins); then the feed will be scanned every other time.
        More formally, the effective scan time for each thread is:
        for X = global scanMins, Y = ttl: min{nX | nX >= Y ; n \u2208 \u2115}
    sleepTime: [Optional] An integer option. Default 1. Values are in seconds. 
        Amount of time to pause between fetches of urls. 
        Some servers do not like when they are hit too quickly, 
        causing weird errors (e.g. inexplicable logouts).
    runOnce: [Optional] A boolean option, default False. 
        Set to True to force RSSDler to exit after it has scanned
    urllib: [Optional]. Boolean Option. Default False. Do not use mechanize.
        You lose several pieces of functionality. 
        1) Referers will no longer work. On most sites, this will not be a 
            problem, but some sites require referers and will deny requests 
            if the referer is not passed back to the site. 
        2) Some sites have various 'refresh' mechanisms that may redirect you 
            around before actually giving you the file to download. 
            Mechanize has the ability to follow these sites.
    noClobber: [Optional] Boolean. Default True. Overwrite file, or use new name
    rssFeed: [Optional] Boolean Option. Default False. Setting this option 
        allows you to create your own rss feed of the objects you have 
        downloaded. It's a basic feed, likely to not include links to the 
        original files. The related rss items (all are required if this is set 
        to True):
    rssLength: [Optional]  Integer. Default 20. An integer. How many entries 
        should the RSS feed store before it starts dropping old items. 0 means 
        that the feed will never be truncated.
    rssTitle: [Optional] A string. Default "some RSS Title".  Title of rssFeed.
    rssLink: [Optional]   string: Default 'nothing.com'. <link> on generated rss
    rssDescription: [Optional] A string. Default "Some RSS Description".
    rssFilename: [Optional] A string. Default 'rssdownloadfeed.xml'. 
        Where to save generated rss
    saveFile: [Optional] A string option. Default savedstate.dat. History data.
    lockPort: [Optional] An integer option. Default 8023. Port to lock saveFile
    daemonInfo: [Optional] A string. Default daemon.info. PID written here.
    umask: [Optional] An integer option. Default 077 in octal.
        Sets umask for file creation. PRIOR TO 0.4.0 this was read as BASE10.
        It is now read as octal like any sane program would.
        Do not edit this if you do not know what it does. 
    debug: [Optional] A boolean option. Default False. If rssdler is attached to
        a console-like device and this is True, will enter into a post-mortem 
        debug mode.
    rss: DEPRECATED, will no longer be processed.
    error: DEPRECATED, wil no longer be processed."""
    def __init__(self):
        dict.__init__(self)
        self['verbose'] = 3
        self['downloadDir'] = os.getcwd()
        self['runOnce'] = False
        self['maxSize'] = None
        self['minSize'] = None
        self['log'] = 0
        self['logFile'] = u'downloads.log'
        self['saveFile'] = u'savedstate.dat'
        self['scanMins'] = 15
        self['lockPort'] = 8023
        self['cookieFile'] = None
        self['workingDir'] = os.path.expanduser( os.path.join('~', '.rssdler') )
        self['daemonInfo'] = u'daemon.info'
        self['rssFeed'] = False
        self['rssDescription'] = u"Some RSS Description"
        self['rssFilename'] = u'rssdownloadfeed.xml'
        self['rssLength'] = 20
        self['rssLink'] = u'nothing.com'
        self['rssTitle'] = u"some RSS Title"
        self['urllib'] = False
        self['cookieType'] = 'MozillaCookieJar'
        self['sleepTime'] = 1
        self['noClobber'] = True
        self['umask'] = 77
        self['debug'] = False

class ThreadLink(dict):
    u"""    link: [Required] A string option. Link to the rss feed.
    active:  [Optional] A boolean option. Default True. Whether Feed is scanned.
    maxSize: [Optional] An integer option, in MB. default is None. 
        A thread based maxSize like in global. If set to None, will default to 
        global's maxSize. 
        Other values override global, including 0 to indicate no maxSize.
    minSize: [Optional] An integer opton, in MB. default is None. 
        A thread based minSize, like in global. If set to None, will default to 
        global's minSize. 
        Other values override global, including 0 to indicate no minSize.
    noSave: [Optional] Boolean. Default: False. True: Never download seen files
    directory: [Optional] A string option. Default to None. If set, 
        overrides global's downloadDir, directory to download download objects.
    checkTime<x>Day: [Optional] A string option. Scan only on specified day
        Either the standard 3 letter abbreviation of the day of the week, 
        or the full name. One of Three options that will specify a scan time. 
        the <x> is an integer.
    checkTime<x>Start: [Optional] An integer option. Default: 0. 
        The hour (0-23) at which to start scanning on correlated day. 
        MUST specify checkTime<x>Day.
    checkTime<x>Stop: [Optional] An integer option. Default 23. 
        The hour (0-23) at which to stop scanning on correlated day. 
        MUST specify checkTime<x>Day.
    regExTrue: [Optional] A string option. Default None. Case insensitive
        If specified, will only download if a regex search of the download name
    regExTrueOptions: [Optional] STRING. Default None. Python re.OPTIONS
    regExFalse: [Optional] A string (regex) option. Default None. 
        If specified, will only download if pattern not in name
    regExFalseOptions: [Optional] A string option. Default None. re.OPTIONS
    postDownloadFunction: [Optional] A string option. Default None. 
        The name of a function, stored in userFunctions.py found in the current 
        working directory. Any changes to this requires a restart of RSSDler. 
        Calls the named function in userFunctions after a successful download 
        with arguments: directory, filename, rssItemNode, retrievedLink, 
        downloadDict, threadName. Exception handling is up to the function, 
        no exceptions are caught. Check docstrings (or source) of 
        userFunctHandling and callUserFunction to see reserved words/access to 
        RSSDler functions/classes/methods.
    preScanFunction: [Optional] See postScanFunction, only before scan.
    postScanFunction: [Optional] A string option. Default None. 
        The name of a function, stored in userFunctions.py. Any changes to this 
        requires a restart of RSSDler. Calls the named function after a scan of 
        a feed with arguments, page, ppage, retrievedLink, and threadName. 
        Exception Handling is up to the function, no exceptions are caught. 
        Check docstrings of userFunctHandling and callUserFunctions for more 
        information.
    The following options are ignored if not set (obviously). But once set, 
        they change the behavior of regExTrue (RET) and regExFalse (REF). 
        Without specifying these options, if something matches RET and doesn't 
        match REF, it is downloaded, i.e. RET and REF constitute sufficient 
        conditions to download a file. Once these are specified, RET and REF 
        become necessary (well, when download<x>(True|False) are set to True, 
        or a string for False) but not sufficient conditions for any given 
        download. If you set RET/REF to None, they are of course ignored and 
        fulfill their 'necessity.' You can specify these options as many times 
        as you like, by just changing <x> to another number. 
    download<x>: [Optional] No default. Where <x> is an integer,
        This is a 'positive' hit regex. This is required for download<x>true and
        download<x>false.
    download<x>False: [Optional] Default = True. 
        However, this is not strictly a boolean option. True means you want to 
        keep regExFalse against download<x>. If not, set to False, and there 
        will be no 'negative' regex that will be checked against. You can also 
        set this to a string (i.e. a regex) that will be a negative regex ONLY 
        for the corresponding download<x>. Most strings are legal, however the 
        following False/True/Yes/No/0/1 are reserved words when used alone and 
        are interpreted, in a case insensitive manner as Boolean arguments. 
        Requires a corresponding download<x> argument.
    download<x>True. [Optional] A Boolean option. default True. True checks 
        against regExTrue. False ignores regExTrue. Requires a corresponding 
        download<x> argument.
    download<x>Dir. [Optional] A String option. Default None. If specified, the 
        first of the download<x> tuples to match up with the download name, 
            downloads the file to the directory specified here. Full path is 
            recommended.
    download<x>Function. [Optional] A String option. Default None. just like 
        postDownloadFunction, but will override it if specified.
    download<x>MinSize. [Optional]. An Integer option. Default None. 
        Analogous to minSize.
    download<x>MaxSize. [Optional]. An integer option. Default None. 
        Analogous to maxSize.
    scanMins [Optional]. An integer option. Default 0. Sets the MINIMUM 
        interval at which to scan the thread. If global is set to, say, 5, and 
        thread is set to 3, the thread will still only be scanned every 5 
        minutes. Alternatively, if you have the thread set to 7 and global to 5,
        the actual interval will be 10. More formally, the effective scan time 
        for each thread is:
        for X = global scanMins, Y = thread scanMins, Z = ttl Mins: 
        min{nX | nX >= Y ; nX >= Z ; n \u2208 \u2115 }
    checkTime: DEPRECATED. Will no longer be processed.
    Programmers Note: 
        download<x>* stored in a DownloadItemConfig() Dict in .downloads. 
        checkTime* stored as tuple of (DoW, startHour, endHour)
    """ 
    def __init__(self, name=None, link=None, active=True, maxSize=None, 
        minSize=None, noSave=False, directory=None, regExTrue=None, 
        regExTrueOptions=None, regExFalse=None, regExFalseOptions=None, 
        postDownloadFunction=None, scanMins=0):
        dict.__init__(self)
        self['link'] = link
        self['active'] = active
        self['maxSize'] = maxSize
        self['minSize'] = minSize
        self['noSave'] = noSave
        self['directory'] = directory
        self['checkTime'] = []
        self['regExTrue'] = regExTrue
        self['regExTrueOptions'] = regExTrueOptions
        self['regExFalse'] = regExFalse
        self['regExFalseOptions'] = regExFalseOptions
        self['postDownloadFunction'] = postDownloadFunction
        self['scanMins'] = scanMins
        self['downloads'] = []
        self['postScanFunction'] = None
        self['preScanFunction'] = None

class SaveInfo(dict):
    u"""lastChecked: when we last checked the rss feeds
downloads: list of urls to downloads that we have grabbed
minScanTime: if feed has <ttl>, we register that fact here in a dictionary with 
threadName as key, and scanTime information as values
failedDown: list of FailedItem instances to be re-attempted to download
version: specifies which version of the program this was made with"""
    def __init__(self, lastChecked=0, downloads=[]):
        dict.__init__(self)
        self['lastChecked'] = lastChecked
        self['downloads'] = downloads
        self['minScanTime'] = {}
        self['failedDown'] = []
        self['version'] = getVersion()
    def __setstate__(self,state):
        if 'data' in state: self.update(state['data'])

class SaveProcessor(object):
    u"""Saves state data to disk.
    Data saved includes downloads, failed items, previous scanTime, and ttl
    and other sources (e.g. user) of minScanTime.
    Developer note, pickled objects include SaveInfo and FailedItem instances
    these are expected to be found in the __name__ namespace. Thus, if you
    try using this outside the __main__ namespace, you will get a 'module' not
    found error. Fix this with: from rssdler import SaveInfo, FailedItem
    in addition to import rssdler. Only needed for transition from 034 to 035"""
    def __init__(self, saveFileName=None):
        u"""saveFileName: location where we store persistence data
        lastChecked: seconds since epoch when we last checked the threads
        downloads: a list of download links, so that we do not repeat ourselves
        minScanTime: a dictionary, keyed by rss link aka thread name, with 
            values of tuples (x,y) where x=last scan time for that thread,
            y=min scan time in minutes, only set if ttl is set in rss feed, 
            otherwise respect checkTime and lastChecked
        failedDown: a list of tuples (item link, threadname, rssItemNode, 
            localized directory to download to (None if to use global) ). 
        (ppage['entries'][i]['link'], threadName, ppage['entries'][i], 
            dirTuple[1]) 
        This means that the regex, at the time of parsing, identified this file 
            as worthy of downloading, but there was some failure in the 
            retrieval process. Size will be checked against the configuration 
            state at the time of the redownload attempt, not the size 
            configuration at the time of the initial download attempt (if there 
            is a difference)
        """
        object.__init__(self)
        if saveFileName:
            self.saveFileName = os.path.join( 
                getConfig()['global']['workingDir'], saveFileName )
        else: 
            self.saveFileName = os.path.join(getConfig()['global']['workingDir']
                , getConfig()['global']['saveFile'])
        self.lastChecked = 0
        self.downloads = []
        self.failedDown = []
        self.minScanTime = {}
        self.version = None
        self.lockSock = None
        self.lockedState = False
    def save(self):
        saveFile = SaveInfo()
        saveFile['lastChecked'] = self.lastChecked
        saveFile['downloads'] = list(set(self.downloads))
        saveFile['minScanTime'] = self.minScanTime
        saveFile['failedDown'] = self.failedDown
        saveFile['version'] = self.version
        f = open(self.saveFileName, 'wb')
        pickle.dump(saveFile, f, -1)
    def load(self):
        u"""take care of conversion from older versions here, 
        then call save to store updates, then continue with loading."""
        f = open(self.saveFileName, 'rb')
        saveFile = pickle.load(f)
        if 'version' not in saveFile: self.version = u'0.2.4'
        else: self.version = saveFile['version']
        self.lastChecked = saveFile['lastChecked']
        self.downloads = saveFile['downloads']
        self.minScanTime = saveFile['minScanTime']
        if (self.version <= u'0.2.4' and len(saveFile['failedDown'])  and
          not isinstance(saveFile['failedDown'][0], FailedItem)):
                for link, threadName, itemNode, LDir  in saveFile['failedDown']:
                    failureDownDict = DownloadItemConfig(None, None, None, LDir)
                    self.failedDown.append( FailedItem( link, threadName, 
                        itemNode, failureDownDict ) )
                self.version = getVersion()
                self.save()
        else: self.failedDown = saveFile['failedDown']
        del saveFile
        # upgrade process should be complete, set to current version
        self.version = getVersion()
    def lock( self ):
        u"""Portable locking mechanism. Binds to 'lockPort' as defined in config
        on 127.0.0.1.
        Raises Locked if a lock already exists.
        """
        if self.lockSock:
            raise Locked
        try:
            self.lockSock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            self.lockSock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.lockSock.bind(('127.0.0.1', getConfig()['global']['lockPort']))
            self.lockedState = True
        except socket.error:
            raise Locked
    def unlock( self ):
        u"""Remove an existing lock()."""
        try: 
            self.lockSock.close()
            self.lockedState = False
        except socket.error: pass

def getConfig(reload=False, filename=None):
    u"""Return an instance of the Config class (creating one if neccessary)"""
    global _configInstance
    if reload: _configInstance = None
    if not _configInstance: _configInstance = Config(filename)
    return _configInstance

def getSaved( filename=None, unset=False):
    u"""Return an instance of the SaveProcessor class creating one if needed"""
    global saved
    if unset: saved = None
    elif not saved: saved = SaveProcessor(saveFileName=filename)
    return saved

class Config(ConfigParser.SafeConfigParser, dict):
    topSections = ['global']
    dayList = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 
        'Saturday', 'Sunday', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun', 
        '0', '1', '2', '3', '4', '5', '6']
    boolOptionsGlobal = ['runOnce', 'active', 'rssFeed', 'urllib', 'noClobber',
        'debug']
    boolOptionsThread = ['active', 'noSave']
    stringOptionsGlobal = ['downloadDir', 'saveFile', 'cookieFile', 'cookieType'
        , 'logFile', 'workingDir', 'daemonInfo', 'rssFilename', 'rssLink',
        'rssDescription', 'rssTitle', ]
    stringOptionsThread = ['link', 'directory', 'postDownloadFunction', 
        'regExTrue', 'regExTrueOptions', 'regExFalse', 'regExFalseOptions', 
        'postScanFunction', 'preScanFunction']    
    intOptionsGlobal = ['maxSize', 'minSize', 'lockPort', 'scanMins', 
        'rssLength', 'sleepTime', 'verbose', 'umask','log', 'maxLogLength']
    intOptionsThread = ['maxSize', 'minSize', 'scanMins']
    validCookies = ['MSIECookieJar' , 'LWPCookieJar' , 'MozillaCookieJar', 
      'Firefox3', 'Safari', 'KDE']
    def __init__(self, filename=None, parsecheck=1):
        u"""
        see helpMessage
        """
        ConfigParser.SafeConfigParser.__init__(self)
        dict.__init__(self)
        if filename: self.filename = filename
        else:
            global configFile
            self.filename = configFile
        if not os.path.isfile( self.filename ): 
            raise SystemExit(u"Configuration File could not be found, exiting")
        a = self.read(self.filename)
        if not a: SystemExit(u'a config file was not parsed. exiting...')
        self['global'] = GlobalOptions()
        self['threads'] = {}
        if parsecheck:
            self.parse()
            self.check()
    def parse(self):
        try: glob = [ x for x in self.sections() if x.lower() == 'global'][0]
        except IndexError: raise SystemExit('no global section found')
        for option in self.boolOptionsGlobal:
            if option.lower() in self.options(glob): 
                try: self['global'][option]=self.getboolean(glob,option)
                except ValueError: 
                    print >> sys.stderr, u"""failed to parse option %s in \
global""" % option
        for option in self.stringOptionsGlobal:
            if option.lower() in self.options(glob):
                self['global'][option] = self._ifnone(self.get(glob,option))
        for option in self.intOptionsGlobal:
            if option.lower() in self.options(glob):
                try: self['global'][option] = self.getint(glob, option)
                except ValueError: print >> sys.stderr, u"""failed to parse \
option %s in global""" % option
        if isinstance(self['global']['umask'] , int): self['global']['umask'] = int(str(self['global']['umask']), 8)
        for thread in ( x for x in self.sections() if x.lower() != 'global'):
            self['threads'][thread] = ThreadLink()
            for option in self.boolOptionsThread:
                if option.lower() in self.options(thread):
                    try: self['threads'][thread][option]=self.getboolean(thread,
                        option)
                    except ValueError: print >> sys.stderr, u"""failed to parse\
 option %s in thread %s""" % (option, thread)
            for option in self.stringOptionsThread:
                if option.lower() in self.options(thread):
                    self['threads'][thread][option]=self._ifnone(self.get(thread
                        , option) )
            for option in self.intOptionsThread:
                if option.lower() in self.options(thread):
                    try: self['threads'][thread][option] = self.getint(thread, 
                        option)
                    except ValueError: print >> sys.stderr, u"""failed to parse\
 option %s in thread %s""" % (option, thread)
            for i in self.getsortedOnName('download', thread):
                if i.lower().endswith('false'): 
                    try: self['threads'][thread]['downloads'][-1]['False'] = (
                        self.getboolean(thread, i) )
                    except ValueError: 
                        self['threads'][thread]['downloads'][-1]['False'] = (
                            self._ifnone( self.get(thread, i) ) )
                elif i.lower().endswith('true'): 
                    try: self['threads'][thread]['downloads'][-1]['True'] = (
                        self.getboolean(thread, i))
                    except ValueError: pass # let default holder
                elif i.lower().endswith('dir'):
                    self['threads'][thread]['downloads'][-1]['Dir'] = (
                        self._ifnone( self.get(thread, i) ))
                elif i.lower().endswith('maxsize'):
                    try: self['threads'][thread]['downloads'][-1]['maxSize'] = (
                        self.getint(thread, i))
                    except ValueError: pass
                elif i.lower().endswith('minsize'):
                    try: self['threads'][thread]['downloads'][-1]['minSize'] = (
                        self.getint(thread, i))
                    except ValueError: pass
                elif i.lower().endswith('function'):
                    self['threads'][thread]['downloads'][-1]['Function'] = (
                        self._ifnone( self.get(thread, i) ))
                else: self['threads'][thread]['downloads'].append( 
                    DownloadItemConfig( self.get(thread, i) ) )
            for j in self.getsortedOnName('checktime', thread):
                optionCheck = self.get(thread, j)
                if j.endswith('day'):
                    if self.dayList.count(optionCheck.capitalize()): 
                        self['threads'][thread]['checkTime'].append(
                            [self.dayList.index(optionCheck.capitalize()) % 7,
                            0,23] )
                    else: raise Exception, u"""Could not identify valid day of \
the week for %s""" % optionCheck
                elif j.endswith('start'): 
                    self['threads'][thread]['checkTime'][-1][1]=int(optionCheck)
                    if self['threads'][thread]['checkTime'][-1][1] > 23: 
                        self['threads'][thread]['checkTime'][-1][1] = 23
                    elif self['threads'][thread]['checkTime'][-1][1] < 0: 
                        self['threads'][thread]['checkTime'][-1][1] = 0
                elif j.endswith('stop'): 
                    self['threads'][thread]['checkTime'][-1][2]=int(optionCheck)
                    if self['threads'][thread]['checkTime'][-1][2] > 23: 
                        self['threads'][thread]['checkTime'][-1][2] = 23
                    elif self['threads'][thread]['checkTime'][-1][2] < 0: 
                        self['threads'][thread]['checkTime'][-1][2] = 0
    def _ifnone(self, option):
        if option == '' or option.lower() == 'none': return None
        else: return option
    def getsortedOnName(self, key, thread):
      return natsorted([x for x in self.options(thread) if x.startswith(key) ])
    def check(self):
        global mechanize
        if not self['global']['urllib'] and not mechanize:
            print >> sys.stderr, """Using urllib2 instead of mechanize. setting\
 urllib = True"""
            self['global']['urllib'] = True
        if self['global']['saveFile'] == None:
            self['global']['saveFile'] = u'savedstate.dat'
        if self['global']['downloadDir'] == None:
            raise SystemExit(u"""Must specify downloadDir in [global] config
Invalid configuration, no download directory""")
        if 'runOnce' not in self['global'] or self['global']['runOnce'] == None:
            self['global']['runOnce'] = False
        if self['global']['scanMins'] == None:
            self['global']['scanMins'] = 15
        if (self['global']['cookieType'] == 'MSIECookieJar' and 
            self['global']['urllib']):
            raise SystemExit( u"""Cannot use MSIECookieJar with urllib = True. \
Choose one or the other. May be caused by failed mechanize import. Incompatible\
 configuration, IE cookies must use mechanize. please install and configure\
 mechanize""")
        if self['global']['cookieType'] not in self.validCookies:
            raise SystemExit(u"""Invalid cookieType option: %s. Only \
MSIECookieJar, LWPCookieJar, and MozillaCookieJar are valid options. Exiting...
""" % self['global']['cookieType'])
        if self['global']['cookieType'] == 'Firefox3':
          global sqlite3
          import sqlite3
        if self['global']['lockPort'] == None:
            self['global']['lockPort'] = 8023
        if ( 'log' in self['global'] and self['global']['log'] and 
            self['global']['logFile'] == None ):
                self['global']['logFile'] = u'downloads.log'
        # check all directories to make sure they exist. Ask for creation?
        if self['global']['downloadDir']:
            if not os.path.isdir( os.path.join(self['global']['workingDir'], 
                self['global']['downloadDir']) ):
                try: os.mkdir( os.path.join(self['global']['workingDir'], 
                    self['global']['downloadDir']) )
                except OSError: 
                    raise SystemExit(''.join((traceback.format_exc(),os.linesep,
u"""Could not find path %s and could not make a directory there. Please make \
sure this path is correct and try creating the folder with proper permissions
""" % os.path.join(self['global']['workingDir'], self['global']['downloadDir']))))
        for thread in self['threads']:
            if self['threads'][thread]['directory'] and not os.path.isdir( 
                os.path.join(self['global']['workingDir'], 
                self['threads'][thread]['directory']) ):
                try: os.mkdir( os.path.join(self['global']['workingDir'], 
                    self['threads'][thread]['directory']) )
                except OSError: 
                  raise SystemExit(''.join((traceback.format_exc(),os.linesep,
u"""Could not find path %s and could not make a directory there. Please make \
sure this path is correct and try creating the folder with proper permissions
""" % os.path.join(self['global']['workingDir'], 
        self['threads'][thread]['directory']))))
            for downDict in self['threads'][thread]['downloads']:
                if downDict['Dir'] and not os.path.isdir( 
                    os.path.join(self['global']['workingDir'],downDict['Dir'])):
                    try: os.mkdir( os.path.join(self['global']['workingDir'], 
                        downDict['Dir'] ) )
                    except OSError, m:
                      raise SystemExit(''.join((traceback.format_exc(),os.linesep,
u"""Could not find path %s and could not make a directory there. Please make \
sure this path is correct and try creating the folder with proper permissions
""" % os.path.join(self['global']['workingDir'], downDict['Dir'] ))))
    def save(self):
        raise DeprecationWarning("""this feature failed at saving custom \
options. You should implement the native ConfigParser write methods""")
    def push(self):
      u"""Pushes the value in the conveniently accessed config dictionaries
      onto the ConfigParser instances so that self.write() changes with any
      updated values"""
      for key, value in self['global'].iteritems():
        #avoid setting options that weren't already set
        if self.has_option('global',key): 
          self.set('global', key, unicodeC(value))
      for section in self['threads'].keys():
        for option in self.options(section): 
          if re.match('(checktime|download)\d',option, re.I): 
            self.remove_option(section, option)
        for key, value in self['threads'][section].iteritems():
          if key == 'downloads':
            for downNum, downDict in enumerate(self['threads'][section]['downloads']):
              for downKey, downValue in downDict.iteritems():
                if downKey == 'localTrue': 
                  self.set(section, u'download%s' % downNum, unicodeC(downValue))
                elif downValue != DownloadItemConfig()[downKey]:
                  self.set(section,u'download%s%s' %(downNum,downKey),unicodeC(downValue))
          elif key.lower() == 'checktime':
            for checkNum, checkTup in enumerate(self['threads'][section][key]):
              self.set(section, 'checkTime%sDay' % checkNum, self.dayList[checkTup[0]])
              self.set(section, 'checkTime%sStart' % checkNum, unicodeC(checkTup[1]))
              self.set(section, 'checkTime%sStop' % checkNum, unicodeC(checkTup[2]))
          elif self.has_option(section,key):
            self.set(section, key, unicodeC(value))
    def write(self, fp):
      """bypasses ConfigParser.write method, because it mangles the file
      expects RSSDler type configuration. 
      This derives from RawConfigParser.write """
      def _write(options, sectionname):
        fd.write("[%s]\n" % sectionname) #why not use __name__?
        for k,v in sorted(list(options),key=operator.itemgetter(0)):
          if k != '__name__':
            fd.write("%s = %s\n" % (k, str(v).replace('\n', '\n\t')))
        fd.write("\n")
      if hasattr(fp, 'write'): fd = fp
      else: fd = codecs.open(fp,'w','utf-8')
      if self._defaults: 
        _write(self._defaults.items(), DEFAULTSECT)
      for section in self.topSections:
        if section in self._sections: 
          _write(self._sections[section].items(), section)
      for section in sorted(list(self._sections)):
        if section not in self.topSections: 
          _write(self._sections[section].items(), section)
      if fd != fp: fd.close() # if we open, we close

# # # # #
# User/InterProcess Communication
# # # # #
def setDebug(type, value, tb):
  if getConfig()['global']['debug'] and _action !='daemon' and sys.stderr.isatty():
    import pdb
    traceback.print_exception(type, value, tb)
    print
    pdb.pm()
  else: sys.__excepthook__(type, value, tb)

def callUserFunction( functionName, *args ):
    u"""calls the named function in userFunctions with arguments 
    (these are positional, not keyword, arguments): 
    if postDownloadFunction: directory, filename, rssItemNode, retrievedLink, 
        downloadDict, threadName
    if postScanFunction: page, ppage, retrievedLink, and threadName 
    directory: name of the directory the file was saved to
    filename: name of the file the downloaded data was saved to
    rssItemNode: the feedparser entry for the item we are downloading. 
        This will have been altered such that the original ['link'] element is 
        now at ['oldlink'] and the ['link'] element has been made to be friendly
        with urllib2RetrievePage and mechRetrievePage
    retrievedLink: the resultant url from the retrieval. May be different from 
        ['link'] and ['oldlink'] in a number of ways (percent quoting and 
        character encoding, in particular, plus any changes to the url from 
        server redirection, etc.)
    downloadDict: a dictionary representing the download<x> options. keys are: 
        'localTrue' (corresponding to download<x>) ; 'False' ; 'True' ; 'Dir' ; 
        'minSize' ; and 'maxSize' corresponding to their names in download<x>.
    threadName: the name of the config entry. to be accessed like 
        getConfig()['threads'][threadName]
    
    page: the raw feed fetched from the server
    ppage: the feedparser parsed feed
    retrievedLink: the url that was sent by the server
    """
    global userFunctions
    logging.debug( u"attempting a user function")
    if hasattr(userFunctions, functionName):
      getattr(userFunctions, functionName)(*args)
    else:
      logging.critical( u"module does not have function named %s called from thread %s" % (functionName, args[-1]))

def userFunctHandling():
    u"""tries to import userFunctions, sets up the namespace
    reserved words in userFunctions: everything in globals() except '__builtins__', '__name__', '__doc__', 'userFunctHandling', 'callUserFunction', 'userFunctions'. If using daemon mode, 'resource' is reserved.
    Reserved words: 'Config', 'ConfigParser', 'DownloadItemConfig', 'FailedItem', 'Fkout', 'GlobalOptions', 'LevelFilter', 'Locked', 'MAXFD', 'MakeRss', 'SaveInfo', 'SaveProcessor', 'StringIO', 'ThreadLink', '_USER_AGENT', '__author__', '__copyright__', '__file__', '__package__', '__version__', '_action', '_configInstance', '_main', '_runOnce', 'bdecode', 'callDaemon', 'callUserFunction', 'checkFileSize', 'checkRegEx', 'checkRegExDown', 'checkRegExGFalse', 'checkRegExGTrue', 'checkScanTime', 'checkSleep', 'cliOptions', 'codecs', 'commentConfig', 'configFile', 'configFileNotes', 'convertKDEToMoz', 'convertMoz3ToNet', 'convertSafariToMoz', 'cookieHandler', 'cookielib', 'createDaemon', 'division', 'downloadFile', 'downloader', 'email', 'encodeQuoteUrl', 'feedparser', 'findNewFile', 'getConfig', 'getFileSize', 'getFilenameFromHTTP', 'getSaved', 'getVersion', 'getopt', 'helpMessage', 'htmlUnQuote', 'httplib', 'isRunning', 'killDaemon', 'logging', 'main', 'make_handler', 'mechRetrievePage', 'mechanize', 'mimetypes', 'minidom', 'natsorted', 'netscapeHeader', 'nonCoreDependencies', 'noprint', 'operator', 'os', 'percentIsQuoted', 'percentNeedsQuoted', 'percentQuote', 'percentQuoteDict', 'percentUnQuote', 'percentunQuoteDict', 'pickle', 'random', 're', 'resource', 'rss', 'rssparse', 'run', 'saved', 'searchFailed', 'securityIssues', 'setDebug', 'setLogging', 'sgmllib', 'signal', 'signalHandler', 'socket', 'sqlite3', 'sys', 'time', 'traceback', 'unQuoteReQuote', 'unicodeC', 'urllib', 'urllib2', 'urllib2RetrievePage', 'urlparse', 'userFunctHandling', 'userFunctions', 'validFileName', 'writeNewFile', 'xmlUnEscape'
    check docstrings/source for use notes on these reserved words."""
    global userFunctions
    bypassGlobalsList = set(('__builtins__', '__name__', '__doc__'))
    g = globals()
    keys = set(g.keys()).difference(bypassGlobalsList)
    if userFunctions: #may be None
      for key in keys: setattr(userFunctions, key, g[key])
    return sorted(list(keys))

def getVersion():
    u"""returns the version of the program"""
    global __version__
    return __version__

def noprint(*args, **kwds): 
    pass

class Fkout(object):
    error=warning=info=debug=write=flush=close = noprint

class LevelFilter(logging.Filter):
    def __init__(self, levels): self.level = levels
    def filter(self, record): 
        return self.level[0] <=  record.levelno <= self.level[1]

def make_handler(h, f, l, *o):
    handler = h(*o)
    handler.setFormatter(logging.Formatter(f, datefmt='%Y%m%d.%H:%M'))
    handler.addFilter(LevelFilter(l))
    return handler

def setLogging(reset=False):
    global _action, logging
    if _action == 'daemon': sys.stderr = sys.stdout = Fkout()
    z = {0:0, 1:50, 2:40, 3:30, 4:20, 5:10}
    v = z[getConfig()['global']['verbose']]
    l = z[getConfig()['global']['log']]
    if reset: reload(logging)
    logging.basicConfig(level=10, stream=Fkout())
    logging.addLevelName(30, '')
    if v:
        logging.getLogger('').addHandler(make_handler(logging.StreamHandler,
            '%(levelname)s %(lineno)d %(message)s', [max(40,v),50],
            sys.stderr))
        logging.getLogger('').addHandler(make_handler(logging.StreamHandler,
            '%(levelname)s %(message)s', [max(v,10),30], sys.stdout))
    if l:
        logging.getLogger('').addHandler(make_handler(logging.FileHandler,
            '%(asctime)s %(levelname)-8s %(message)s', [max(l,10),50], 
            getConfig()['global']['logFile'],'a'))
    
# # # # #
#Daemon
# # # # #
def isRunning(file=None):
    u"""Returns pid of another rssdler, if running with current config. 0 if not
    POSIX only."""
    pid = 0
    if not file: 
        file = os.path.join(getConfig()['global']['workingDir'], 
            getConfig()['global']['daemonInfo'])
    try: pid = int(codecs.open( file, 'r', 'utf-8').read())
    except (TypeError, ValueError, IOError), m: pass
    if not pid: return 0
    try: state = os.kill(pid, 0)
    except (AttributeError, OSError), m: state = unicodeC(m)
    if not state: return pid
    else:
        if 'No such process' in state: return 0 # process died
        else: return pid #means we do not have the perms on the pid, 
def killDaemon( pid ):
    u"""kills the daemon. do not call from within a running instance of main().
    it could loop forever"""
    while True:
        getSaved()
        try:
            getSaved().lock()
            getSaved().unlock()
            break
        except Locked:
            global saved
            del saved
            print( u"Save Processor is in use, waiting for it to unlock" )
            time.sleep(2)
    try:  codecs.open(os.path.join(getConfig()['global']['workingDir'], 
        getConfig()['global']['daemonInfo']), 'w', 'utf-8').write('')
    except IOError, m: print('could not rewrite pidfile %s' % pidfile)
    os.kill(pid,9)

def createDaemon():
    u"""Detach a process from the controlling terminal and run it in the
    background as a daemon.
    """
    try:        pid = os.fork()
    except OSError, e:
        logging.critical(u"s [%d]" % (e.strerror, e.errno))
        raise OSError
    if pid == 0:    # The first child.
        os.setsid()
        try: pid = os.fork() # Fork a second child.
        except OSError, e: raise OSError(u"%s [%d]" % (e.strerror, e.errno))
        if (pid == 0):  pass # The second child.
        else: os._exit(0) # Exit parent (the first child) of the second child
    else: os._exit(0) 
    global resource
    import resource     # Resource usage information.
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if maxfd == resource.RLIM_INFINITY:     maxfd = MAXFD
    for fd in range(0, maxfd):
        try:    os.close(fd)
        except OSError: pass    # ERROR, fd wasn't open to begin with (ignored)
##    os.open(REDIRECT_TO, os.O_RDWR) # standard input (0)
##    os.dup2(0, 1)           # standard output (1)
##    os.dup2(0, 2)           # standard error (2)
    return 0

def callDaemon():
    u"""setup a daemon"""
    if isRunning(): 
        raise SystemExit(u"already running")
    retCode = createDaemon()

def signalHandler(signal, frame):
    u"""take the signal, find a stopping point for the program 
    (ok, the signal kills all processing, so save current state) then exit."""
    global rss
    if isinstance(getSaved(), SaveProcessor):  
        # signal will be blocked by i/o, so we are safe in terms of the saved 
        # file will be fully read, files written, then signal passed
        getSaved().save()
        try: getSaved().unlock()
        except: pass #we'll unlock when we exit in two seconds
    if rss:
        rss.close(length=getConfig()['global']['rssLength'])
        rss.write()
    try: codecs.open(os.path.join(getConfig()['global']['workingDir'],
        getConfig()['global']['daemonInfo']), 'w', 'utf-8').write('')
    except IOError, m: pass
    raise SystemExit, u"exiting due to exit signal %s" % signal

# # # # #
#Running
# # # # #
def rssparse(tName):
    u"""loops through the rss feed, searching for downloadable files"""
    page = None
    try: page = downloader(getConfig()['threads'][tName]['link'])
    except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException, ):   
        logging.critical(''.join((traceback.format_exc(), os.linesep,
          u'error grabbing url %s' % getConfig()['threads'][tName]['link'])))
        return None
    if not page: 
        logging.critical( u"failed to grab url %s" % getConfig()['threads'][tName]['link'])
        return None
    try: pr = page.read()
    except Exception, m:
        logging.critical(''.join((traceback.format_exc(), os.linesep, u"could not grab rss feed")))
        return None
    try: ppage = feedparser.parse(pr)
    except Exception, m: # feedparser does not seem to throw exceptions properly, is a dictionary of some kind
        logging.critical(''.join((traceback.format_exc(), os.linesep,
          u"page grabbed was not a parseable rss feed")))
        return None
    if 'ttl' in ppage['feed'] and ppage['feed']['ttl'] != '' and not (
      getConfig()['threads'][tName]['scanMins'] > int(ppage['feed']['ttl'])):
        logging.debug(u"setting ttl")
        getSaved().minScanTime[tName] = (time.time(), int(ppage['feed']['ttl']))
    elif getConfig()['threads'][tName]['scanMins']:
        getSaved().minScanTime[tName] = (time.time(), getConfig()['threads'][tName]['scanMins'] )
    if getConfig()['threads'][tName]['noSave']:
        for entry in ppage['entries']:
            if ( 'enclosures' in entry
                and len(entry['enclosures']) 
                and 'href' in entry['enclosures'][0]
                #and not getConfig()['threads'][tName]['preferLink'] # proposed configuration option
                ):
                    entry['link']=unQuoteReQuote(entry['enclosures'][0]['href'])
            else: entry['link'] = unQuoteReQuote( entry['link'] )
            getSaved().downloads.append(entry['link'])
    else:
        if getConfig()['threads'][tName]['preScanFunction']:
          callUserFunction( getConfig()['threads'][tName]['preScanFunction'], pr, ppage, page.geturl(), tName )
        for i in range(len(ppage['entries'])):
            # deals with feedparser bug with not properly uri unquoting/xml unescaping links from some feeds
            if 'link' not in ppage['entries'][i]: continue
              #and (
              #'enclosures' not in ppage['entries'][i] or 
              #not ppage['entries'][i]['enclosures'] or 
              #'href' not in ppage['entries'][i]['enclosures'][0]): continue
            ppage['entries'][i]['oldlink'] = ppage['entries'][i]['link']
            if ( 'enclosures' in ppage['entries'][i]  
                and len(ppage['entries'][i]['enclosures']) 
                and 'href' in ppage['entries'][i]['enclosures'][0]
                #and not getConfig()['threads'][tName]['preferLink'] # proposed configuration option
                ):
                    ppage['entries'][i]['link'] = unQuoteReQuote( ppage['entries'][i]['enclosures'][0]['href'] )
            else: ppage['entries'][i]['link'] = unQuoteReQuote( ppage['entries'][i]['link'] )
            #if we have downloaded before, just skip (but what about e.g. multiple rips of about same size/type we might download multiple times)
            if ppage['entries'][i]['link'] in getSaved().downloads: 
                logging.debug(u"already downloaded %s" % ppage['entries'][i]['link'])
                continue
            # if it failed before, no reason to believe it will work now, plus it's already queued up
            if searchFailed( ppage['entries'][i]['link'] ): 
                logging.debug(u"link was in failedDown")
                continue
            dirDict = checkRegEx(tName, ppage['entries'][i])
            if not dirDict: continue
            userFunctArgs = downloadFile(ppage['entries'][i]['link'], tName, ppage['entries'][i], dirDict)
            if userFunctArgs == None: continue # size was inappropriate == None
            elif userFunctArgs == False: # was supposed to download, but failed
                logging.debug(u"adding to failedDown: %s" % ppage['entries'][i]['link'] )
                getSaved().failedDown.append( FailedItem(ppage['entries'][i]['link'], tName, ppage['entries'][i], dirDict) )
            elif userFunctArgs: # should have succeeded
                logging.debug(u"adding to saved downloads: %s" % ppage['entries'][i]['link'] )
                getSaved().downloads.append( ppage['entries'][i]['link'] )
                if isinstance(dirDict, DownloadItemConfig) and dirDict['Function']:
                    callUserFunction( dirDict['Function'], *userFunctArgs )
                elif getConfig()['threads'][tName]['postDownloadFunction']: 
                    callUserFunction( getConfig()['threads'][tName]['postDownloadFunction'], *userFunctArgs )
    if getConfig()['threads'][tName]['postScanFunction']:
        callUserFunction( getConfig()['threads'][tName]['postScanFunction'], pr, ppage, page.geturl(), tName )

def checkScanTime( threadName , failed=False):
    u"""looks for a reason to not scan the thread, through minScanTime, checkTime."""
    if threadName in getSaved().minScanTime and getSaved().minScanTime[threadName ][0]  > ( int(time.time()) - getSaved().minScanTime[threadName][1]*60 ):
        logging.info(u"""RSS feed "%s" has indicated that we should wait \
greater than the scan time you have set in your configuration. Will try again \
at next configured scantime""" % threadName)
        return False
    if not failed and len(getConfig()['threads'][threadName]['checkTime']) != 0: # if it was from failed, don't worry about user set scan time
        timeTuple = time.localtime().tm_wday, time.localtime().tm_hour
        badTime = True
        for timeCheck in getConfig()['threads'][threadName]['checkTime']:
            timeLess = timeCheck[0], timeCheck[1]
            timeMore = timeCheck[0], timeCheck[2]
            if timeLess <= timeTuple <= timeMore:
                badTime = False
                break
        if badTime: return False
    return True
    
def checkSleep( totalTime ):
    u"""let's us know when we need to stop sleeping and rescan"""
    logging.debug(u'checking sleep')
    time.sleep(totalTime)

def run():
    u"""Provides main functionality -- scans threads."""
    global saved, rss, downloader, _action
    getConfig(filename=configFile, reload=True)
    if isinstance(getConfig()['global']['umask'], int): 
        os.umask( getConfig()['global']['umask'] )
    if not getConfig()['global']['urllib'] and mechanize: 
      downloader = mechRetrievePage
    else: downloader  = urllib2RetrievePage
    getSaved(unset=1)
    getSaved(getConfig()['global']['saveFile'])
    try:    getSaved().lock()
    except Locked:
        logging.error( u"Savefile is currently in use.")
        raise
    try: getSaved().load()
    except (EOFError, IOError, ValueError, IndexError), m: 
        logging.debug(traceback.format_exc() +u"""didn't load SaveProcessor. \
Creating new saveFile.""")
    logging.debug(u"checking working dir, maybe changing dir")
    if os.getcwd() != getConfig()['global']['workingDir'] or (os.getcwd() != 
        os.path.realpath( getConfig()['global']['workingDir'] )): 
            os.chdir(getConfig()['global']['workingDir'])
    sys.path.insert(0, getConfig()['global']['workingDir']) # import userFunct
    if getConfig()['global']['runOnce'] and ( getSaved().lastChecked > 
        ( int(time.time()) - (getConfig()['global']['scanMins']*60) )):
        raise  SystemExit(u"Threads have already been scanned.")
    if getConfig()['global']['rssFeed']:
        logging.debug(u'trying to generate rss feed')
        if getConfig()['global']['rssFilename']:
            logging.debug(u'rss filename set')
            rss = MakeRss(filename=getConfig()['global']['rssFilename'])
            if os.path.isfile( getConfig()['global']['rssFilename'] ):
                logging.debug(u'loading rss file')
                rss.parse()
            (rss.channelMeta['title'], rss.channelMeta['description'], 
                rss.channelMeta['link'] ) = (getConfig()['global']['rssTitle'],
                getConfig()['global']['rssDescription'], 
                getConfig()['global']['rssLink'])
        else:  logging.critical(u"no rssFilename set, cannot write feed to a file")
    userFunctHandling()
    if getSaved().failedDown:
        logging.info(u"Scanning previously failed downloads")
        for i in  xrange( len( getSaved().failedDown) - 1, -1, -1 ):
            if not checkScanTime(getSaved().failedDown[i]['threadName'],
                failed=1): continue
            logging.info(u"  Attempting to download %s" % getSaved().failedDown[i]['link'])
            if downloadFile( **getSaved().failedDown[i] ):
                logging.info(u"Success!")
                del getSaved().failedDown[ i ]
                getSaved().save()
            else:
                logging.info(u"Failure on %s in failedDown" % getSaved().failedDown[i]['link'])
    logging.info( u"Scanning threads")
    for key in getConfig()['threads'].keys():
        if not getConfig()['threads'][key]['active']:  continue 
        if not checkScanTime( key, failed=False): continue
        logging.info( u"finding new downloads in thread %s" % key)
        rssparse(key) 
    if rss:
        rss.close(length=getConfig()['global']['rssLength'])
        rss.write()
    getSaved().lastChecked = int(time.time()) -30
    getSaved().save()
    getSaved().unlock()

def main( ):
    global _runOnce, userFunctions
    setLogging()
    logging.info( u"--- RSSDler %s" % getVersion() )
    if isRunning() and os.name != 'nt':
        logging.critical('RSSDler is already running. exiting.')
        raise SystemExit(1)
    logging.debug(u"writing daemonInfo")
    try: codecs.open( os.path.join(getConfig()['global']['workingDir'], getConfig()['global']['daemonInfo']), 'w', 'utf-8').write(unicodeC(os.getpid()))
    except IOError: 
        logging.critical(''.join((traceback.format_exc(),os.linesep, 
          u"Could not write to, or not set, daemonInfo")))
    if not _runOnce:
        _runOnce = getConfig()['global']['runOnce']
    try: import userFunctions
    except ImportError: pass
    while True:
        try:
            logging.info( u"[Waking up] %s" % time.asctime() )
            if mechanize: mechanize._opener = None
            urllib2._opener = None
            startTime = time.time()
            run()
            logging.info( u"Processing took %d seconds" % (time.time() - startTime) )
        except Exception, m:
            logging.critical("Unexpected Error: %s" % traceback.format_exc() )
            getSaved().save()
            getSaved().unlock()
            raise
        if _runOnce:
            logging.info( u"[Complete] %s" % time.asctime() )
            break
        logging.info( u"[Sleeping] %s" % time.asctime() )
        checkSleep( getConfig()['global']['scanMins'] * 60 )

helpMessage=u"""RSSDler is a Python based program to automatically grab the 
    link elements of an rss feed, aka an RSS broadcatcher. 

http://code.google.com/p/rssdler/

It happens to work just fine for grabbing RSS feeds of torrents, so called 
    torrent broadcatching. It may also used with podcasts and such. 
    Though designed with an eye toward rtorrent, it should work with any
    torrenting program that can read torrent files written to a directory. It 
    does not explicitly interface with rtorrent in anyway and therefore has no 
    dependency on it. 


Effort has been put into keeping the program from crashing from random errors
    like bad links and such. Try to be careful when setting up your 
    configuration file. If you are having problems, try to start with a very
    basic setup and slowly increase its complexity. You need to have a basic 
    understanding of regular expressions to setup the regex and download<x> 
    options, which is probably necessary to broadcatch in an efficient manner.
    If you do not know what and/or how to use regular expressions, google is 
    your friend. If you are having problems that you believe are RSSDler's 
    fault, post an issue:
    http://code.google.com/p/rssdler/issues/list 
    or post a message on: 
    http://groups.google.com/group/rssdler. 
    Please be sure to include as much information as you can.

%s

%s
    
%s

Configuration File:
%s

Global Options:
%s

    
Thread options:
%s

Most options can be altered during runtime (i.e. by editing then saving the
    config file. Those that require a restart include: 
    - config file location
    - verbosity/logging level ; log file location
    - daemonInfo
    - debug
    - changes to userFunctions

A Netscape cookies file must have the proper header that looks like this:
%s
cookiedata ....

%s

Contact for problems, bugs, and/or feature requests: 
  http://groups.google.com/group/rssdler or 
  http://code.google.com/p/rssdler/issues/list or
Author: %s
""" % (cliOptions, nonCoreDependencies, securityIssues, configFileNotes, GlobalOptions.__doc__, ThreadLink.__doc__, netscapeHeader, __copyright__, __author__)

def _main(arglist):
    try: 
        (argp, rest) =  getopt.gnu_getopt(arglist[1:], "sdfrokc:h", 
            longopts=["state", "daemon", "full-help", "run", "runonce", "kill", 
            "config=", "set-default-config=", "help", "list-failed", 
            "list-saved", "purge-saved", "purge-failed", "comment-config"])
    except  getopt.GetoptError:
            print >> sys.stderr, helpMessage
            sys.exit(1)
    global _action, _runOnce, configFile, REDIRECT_TO, saved
    for param, argum in argp:
        if param == "--daemon" or param == "-d":    _action = "daemon"      
        elif param == "--run" or param == "-r": _action = "run"
        elif param == "--runonce" or param == "-o":
            _action = "run"
            _runOnce = True
        elif param =="--state" or param == "-s": _action = 'state'
        elif param == "--kill" or param == "-k":    _action = "kill"
        elif param == "--config" or param == "-c": configFile = argum
        elif param == "--purge-failed": _action="purge-failed"
        elif param == "--help" or param == "-h":  _action = 'help'
        elif param == "--full-help" or param == "-f": _action = 'fullhelp'
        elif param == "--set-default-config": _action ='set-default-config'
        elif param == "--list-failed":  _action = 'list-failed'
        elif param == "--list-saved": _action = 'list-saved'
        elif param == "--purge-saved": _action = 'purge-saved'
        elif param == "--comment-config": _action = 'comment-config'
    signal.signal(signal.SIGINT, signalHandler)
    sys.excepthook = setDebug #this is NOT supposed to be called!
    if _action == 'comment-config':
        print(commentConfig)
        raise SystemExit
    elif _action == "daemon":
        getConfig(filename=configFile, reload=True)
        if os.name == u'nt' or os.name == u'dos' or os.name == u'ce':
            print >> sys.stderr,  u"daemon mode not supported on Windows. will try to continue, but this is likely to crash"
        elif os.name == u'mac' or os.name == u"os2":
            print >> sys.stderr,  (
u"""daemon mode may have issues on your platform. will try to continue, but may 
crash. feel free to submit a ticket with relevant output on this issue""" )
        if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): 
            os.chdir(getConfig()['global']['workingDir'])
        if isinstance(getConfig()['global']['umask'], int ):    
            try: os.umask( getConfig()['global']['umask'] )
            except (AttributeError, ValueError), m:
                print >> sys.stderr, (
u"""cannot set umask. Umask must be an integer value. Umask only available on 
some platforms. %s""" % traceback.format_exc() )
        callDaemon()
        main()
    elif _action == 'fullhelp':
        print(helpMessage)
        raise SystemExit
    elif _action == 'help':
        print(cliOptions)
        raise SystemExit
    elif _action == "kill":
        getConfig(filename=configFile, reload=True)
        pid = isRunning()
        if pid: killDaemon(pid)
        else: print(u"* No rssdler process found, exiting without killing")
        raise SystemExit
    elif _action == "list-failed":
        getConfig(filename=configFile, reload=True)
        if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): 
            os.chdir(getConfig()['global']['workingDir'])
        while 1:
            getSaved( getConfig()['global']['saveFile'] )
            try: 
                getSaved().lock()
                getSaved().load()
                break
            except (Locked, IOError, ValueError, IndexError):
                global saved
                del saved
                time.sleep(3)
                continue
        for failure in  getSaved().failedDown:
            print( failure['link'] )
        getSaved().unlock()
        raise SystemExit
    elif _action == "list-saved":
        getConfig(filename=configFile, reload=True)
        if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): 
            os.chdir(getConfig()['global']['workingDir'])
        while 1:
            getSaved( getConfig()['global']['saveFile'] )
            try: 
                getSaved().lock()
                getSaved().load()
                break
            except (Locked, IOError, ValueError, IndexError):
                del saved
                time.sleep(3)
                continue
        for down in  getSaved().downloads:
            print( down )
        getSaved().unlock()
        sys.exit()
    elif _action == "purge-failed":
        getConfig(filename=configFile, reload=True)
        if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): 
            os.chdir(getConfig()['global']['workingDir'])
        if os.umask != None:    
            try: os.umask( getConfig()['global']['umask'] )
            except (AttributeError, ValueError), m:
                logging.error( u'cannot set umask. Umask must be an integer value. Umask only available on some platforms. %s' % traceback.format_exc())
        while 1:
            getSaved( getConfig()['global']['saveFile'] )
            try: 
                getSaved().lock()
                getSaved().load()
                break
            except (Locked, IOError, ValueError, IndexError):
                del saved
                time.sleep(3)
                continue
        while getSaved().failedDown:
            getSaved().downloads.append( getSaved().failedDown.pop()['link'] )
        getSaved().save()
        getSaved().unlock()
        sys.exit()
    elif _action == "purge-saved":
        getConfig(filename=configFile, reload=True)
        if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): 
            os.chdir(getConfig()['global']['workingDir'])
        if os.umask != None:    
            try: os.umask( getConfig()['global']['umask'] )
            except (AttributeError, ValueError):
                logging.error( u'cannot set umask. Umask must be an integer value. Umask only available on some platforms. %s' % traceback.format_exc())
        while 1:
            getSaved( getConfig()['global']['saveFile'] )
            try: 
                getSaved().lock()
                getSaved().load()
                break
            except (Locked, IOError, ValueError, IndexError):
                del saved
                time.sleep(3)
                continue
        getSaved().downloads = []
        getSaved().save()
        raise SystemExit
    elif _action == "run":
        getConfig(filename=configFile, reload=True)
        if os.getcwd() != getConfig()['global']['workingDir'] or os.getcwd() != os.path.realpath( getConfig()['global']['workingDir'] ): 
            os.chdir(getConfig()['global']['workingDir'])
        if isinstance(getConfig()['global']['umask'], int ):    
            try: os.umask( getConfig()['global']['umask'] )
            except (AttributeError, ValueError), m:
                logging.error( u'cannot set umask. Umask must be an integer value. Umask only available on some platforms. %s' % traceback.format_exc())
        main()
    elif _action == 'set-default-config':
        raise SystemExit(u'--set-default-config option is now obsolete')
    elif _action == 'state':
        pid = isRunning()
        if pid: print('%s' % unicodeC(pid) )
        else: raise SystemExit(1)
    else:
        print(u"use -h/--help to print the short help message")
        raise SystemExit

if __name__ == '__main__':   
    sys.stdout = codecs.getwriter( "utf-8" )( sys.stdout, "replace" )
    sys.stderr = codecs.getwriter( "utf-8" )( sys.stderr, "replace" )
    _main(sys.argv)
