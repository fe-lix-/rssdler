def ifTorrent(directory, filename, rssItemNode, retrievedLink, downloadDict, 
  threadName):
    u"""Confirms that downloaded data is valid bencoded (torrent) data
    If not, executes failedProcedure
    """
    try: fd = open(os.path.join(directory, filename), 'rb')
    except IOError, m:
        logging.error( unicode(m) + 
          u" could not even open our just written file. leaving function..")
        return None
    try: fdT = bdecode( fd.read() )
    except ValueError: fdT = False
    if fdT:     return True
    else:
        failedProcedure(u"The file %s wasn't actually torrent data. Attempting to remove from queue. Will add to failedDown" % filename , directory, filename, threadName, rssItemNode, downloadDict )
        return False

def currentOnly(directory, filename, rssItemNode, retrievedLink, downloadDict, 
  threadName):
    u"""checks to make sure that the item was added recently. 
    Useful for feeds that get messed up on occasion."""
    try: maxage = getConfig().getint(threadName, 'maxage')
    except (ValueError, ConfigParser.NoOptionError): maxage = 86400
    if time.time() - time.mktime( rssItemNode['updated_parsed'] ) > maxage:
        try: os.unlink( os.path.join(directory, filename) )
        except OSError: 
          logging.critical(u"could not remove file from disk: %s" % filename)
        global rss
        if rss: rss.delItem()
    
def noRss(*args):
    u"""removes the downloaded item from RSS, 
    in case you do not want to generate an rss feed of some downloaded items"""
    global rss
    if rss: rss.delItem()

def saveFeed(page, ppage, retrievedLink, threadName):
    u"""Uses MakeRss to generate an archive of rss items.
    Useful for later perusal by a human read rss reader,
    without having to hit up the server multiple times.
    Set the filename with the config option 'rssfile'; length with 'rsslength'
    in your THREAD's configuration section (for each thread you want to save)
    otherwise, defaults to sectionName.xml and 100.
    WILL generate an invalid feed that may break some readers. 
    See issue #3 (link below).
    http://code.google.com/p/rssdler/issues/detail?id=3
    """
    try: filename= getConfig().get(threadName, 'rssfile') 
    except ConfigParser.NoOptionError: filename = "%s.xml" % threadName
    try: length = getConfig().getint(threadName, 'rsslength')
    except ConfigParser.NoOptionError: length = 100
    rssl = MakeRss(filename=filename, parse=True)
    rssl.channelMeta = ppage['feed']
    links = [ x['link'] for x in rssl.itemsQuaDict ]
    for x in reversed(ppage['entries']):
      if x['link'] not in links: rssl.addItem(x)
    rssl.close(length=length)
    rssl.write()

def rewriteFeed(*args):
  u"""Rewrite Description to make links to profile page,
  uses options rewriteregex, rewritelink, and rewritetext to
  manipulate entries."""
  page, ppage, retrievedLink, threadName = args
  try: search = getConfig().get(threadName, 'rewriteregex')
  except ConfigParser.NoOptionError: saveFeed(*args)
  try: baselink = getConfig().get(threadName, 'rewritelink')
  except ConfigParser.NoOptionError: saveFeed(*args)
  try: addtext = getConfig().get(threadName, 'rewritetext')
  except ConfigParser.NoOptionError: saveFeed(*args)
  for i, entry in enumerate(ppage['entries']):
    try: link = "%s%s" % (baselink, re.search(search, entry['link']).group(1))
    except AttributeError: link = baselink
    text = """<a href="%s">%s</a> """ % (link, addtext)
    ppage['entries'][i]['description'] = "%s %s" %( text, entry['description'])
  saveFeed(page, ppage, retrievedLink, threadName)

def downloadFromSomeSite( directory, filename, rssItemNode, retrievedLink, 
  downloadDict, threadName ):
  """download a file from an html page. 
  set two options in your thread configuration 
  baselink: the baseurl of the site (should include a trailing /
    example: http://cnn.com/
  urlsearch: a string that will be present in the url for any given download. 
    e.g. /download/, /torrent/, gettorrent.php, etc.
    by default, this is not a regular expression, but a code snippet is provided
    in the source if you want to treat it as one.
    depends on libxml2dom
    assumes you want to grab a torrent file. 
    Comment out last two lines if you want a non-torrent file
    """
  try:
    baselink = getConfig().get(threadName, 'baselink')
    urlsearch = getConfig().get(threadName, 'urlsearch')
  except ConfigParser.NoOptionError:
    logging.critical("""To use downloadFromSomeSite function, \
you must provide options baselink and urlsearch in your config""")
    return None
  global libxml2dom
  try: libxml2dom
  except NameError: import libxml2dom
  try: a = codecs.open( os.path.join( directory, filename ), 'rb' )
  except IOError, m:
    failedProcedure( u"""%s: could not even open our just written file.leaving \
function..""" % m, directory, filename, threadName, rssItemNode, downloadDict) 
    return None
  p = libxml2dom.parseString( a.read(), html=True)
  try: link = "%s%s" % (baselink ,  [x.getAttribute('href') for x in
    p.getElementsByTagName('a') if x.hasAttribute('href') and
    x.getAttribute('href').count(urlsearch) ][0] )
    # if you want a regex. Then, instead of
    # x.getAttribute('href').count(urlsearch) do:
    # re.search(urlsearch, x.getAttribute('href'))
  except IndexError, m:
    failedProcedure( u"""%s: could not find href for downloaded %s item for \
redownload""" % (m, threadName), directory, filename, threadName, 
      rssItemNode, downloadDict)
    return None
  try: d = downloader(link)
  except (urllib2.HTTPError, urllib2.URLError, httplib.HTTPException), m:
    failedProcedure( '%s: could not download torrent from site' % m,
      directory, filename, threadName, rssItemNode, downloadDict)
    return None
  newfilename = getFilenameFromHTTP( d.info(), d.geturl() )
  newfilename = writeNewFile( newfilename, directory, d )
  # assume we want a torrent file
  if ifTorrent( directory, newfilename, rssItemNode, retrievedLink,
    downloadDict, threadName):
    os.unlink( os.path.join(directory, filename) )

def failedProcedure( message, directory, filename, threadName, rssItemNode, 
  downloadDict ):
    u"""A function to take care of failed downloads.
    cleans up saved, failed, rss, the directory/filename, and prints to the log.
    should be called from other functions here, not directly from RSSDler."""
    global saved
    logging.critical(unicodeC(message))
    saved.failedDown.append( FailedItem( saved.downloads.pop(), threadName, 
      rssItemNode, downloadDict) )
    try: os.unlink(os.path.join(directory, filename))
    except OSError: 
      logging.critical(u"could not remove file from disk: %s" % filename)
    if rss: rss.delItem()

def advanceEpisode(downloadDict, threadName, regex=r'^(\D+\d+\D+)(\d+)(\D*)$',
  regNum=2, regSub=r'\g<1>%02d\g<3>'):
  u"""The intent is to advance the episode implicitly defined in a filter.
  The function works simply by using the regex to get the episode number,
  the matching parentheses of which is defined by regNum. 
  The function then advances the episode number by 1 and
  substitutes it back into the space defined by regSub,
  which means you should have ONE interpolation (%d, etc.) defined 
  
  It then changes the config dictionary, pushes it into the ConfigParser and
  saves it to the config file, which will kill the organization and comments of
  your config file (blame ConfigParser).
  
  The defaults will NOT work if you have numbers in the name of the show.
  The function should not be called directly as a postDownloadFunction
  but rather make your own wrappers for specific episodes and content type. e.g.
  def weeds(*args):
    if ifTorrent(*args): advanceEpisode( args[4], args[5])
  you can, of course, define custom regular expressions to match your own
  filters and use them in the call to advanceEpisode.
    
  This function expects the format of the filter to be something like:
    name.of.the.show.SEASONbreakNumberMaybesomeMore
    e.g. weeds.*4.*01.*hdtv
    as indicated, the '.*hdtv' part is optional.
  if this does not fit your show syntax
  you will need to customize the regular expressions."""
  global configFile
  if ( downloadDict['localTrue'] == None or 
    not getConfig()['threads'][threadName]['downloads'].count(downloadDict)):
      return # no episode to match
  index = getConfig()['threads'][threadName]['downloads'].index(downloadDict)
  try: e = int(re.search(regex, downloadDict['localTrue']).group(regNum)) +1
  except (ValueError, IndexError): return # no episode to match
  s = re.sub(regex,regSub % e, downloadDict['localTrue'])
  getConfig()['threads'][threadName]['downloads'][index]['localTrue'] = s
  getConfig().push()
  getConfig().write(configFile)
  #getConfig(reload=True) # SHOULD be unnecessary
  
  
