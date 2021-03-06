# -*- coding: utf-8 -*-

'''
    Genesis Add-on
    Copyright (C) 2015 lambda

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import re,urllib,urlparse,base64

from resources.lib.libraries import cleantitle
from resources.lib.libraries import cloudflare
from resources.lib.libraries import client
from resources.lib import resolvers


class source:
    def __init__(self):
        self.base_link = 'http://yify-streaming.com'
        self.moviesearch_link = '/?cat=5%2C14%2C10%2C3&s='
        self.tvsearch_link = '/?cat=2&s='


    def get_movie(self, imdb, title, year):
        try:
            query = urlparse.urljoin(self.base_link, self.moviesearch_link + urllib.quote_plus(title))

            result = cloudflare.source(query)

            r = client.parseDOM(result, 'li', attrs = {'class': 'first element.+?'})
            r += client.parseDOM(result, 'li', attrs = {'class': 'element.+?'})
            r += client.parseDOM(result, 'header', attrs = {'class': 'entry-header'})

            title = cleantitle.movie(title)
            years = ['(%s)' % str(year), '(%s)' % str(int(year)+1), '(%s)' % str(int(year)-1)]

            result = [(client.parseDOM(i, 'a', ret='href'), client.parseDOM(i, 'a')) for i in r]
            result = [(i[0][0], i[1][0]) for i in result if len(i[0]) > 0 and len(i[1]) > 0]
            result = [(i[0], re.compile('(.+? [(]\d{4}[)])').findall(i[1])) for i in result]
            result = [(i[0], i[1][0]) for i in result if len(i[1]) > 0]
            result = [i for i in result if title == cleantitle.movie(i[1])]
            result = [i[0] for i in result if any(x in i[1] for x in years)][0]

            try: url = re.compile('//.+?(/.+)').findall(result)[0]
            except: url = result
            url = client.replaceHTMLCodes(url)
            url = url.encode('utf-8')
            return url
        except:
            return


    def get_show(self, imdb, tvdb, tvshowtitle, year):
        try:
            url = tvshowtitle
            url = client.replaceHTMLCodes(url)
            url = url.encode('utf-8')
            return url
        except:
            return


    def get_episode(self, url, imdb, tvdb, title, date, season, episode):
        try:
            if url == None: return

            season = '%01d' % int(season)
            episode = '%01d' % int(episode)

            query = '%s "Season %s" "Episode %s"' % (url, season, episode)
            query = urlparse.urljoin(self.base_link, self.tvsearch_link + urllib.quote_plus(query))

            result = cloudflare.source(query)

            r = client.parseDOM(result, 'li', attrs = {'class': 'first element.+?'})
            r += client.parseDOM(result, 'li', attrs = {'class': 'element.+?'})
            r += client.parseDOM(result, 'header', attrs = {'class': 'entry-header'})

            tvshowtitle = cleantitle.tv(url)

            result = [(client.parseDOM(i, 'a', ret='href'), re.compile('(.+?): Season (\d*).+?Episode (\d*)').findall(i)) for i in r]
            result = [(i[0][0], i[1][-1]) for i in result if len(i[0]) > 0 and len(i[1]) > 0]
            result = [(i[0], i[1][0].split('>')[-1], i[1][1], i[1][2]) for i in result]
            result = [i for i in result if season == '%01d' % int(i[2]) and episode == '%01d' % int(i[3])]
            result = [i[0] for i in result if tvshowtitle == cleantitle.tv(i[1])][0]

            try: url = re.compile('//.+?(/.+)').findall(result)[0]
            except: url = result
            url = client.replaceHTMLCodes(url)
            url = url.encode('utf-8')
            return url
        except:
            return


    def get_sources(self, url, hosthdDict, hostDict, locDict):
        try:
            sources = []

            if url == None: return sources

            url = urlparse.urljoin(self.base_link, url)

            result = cloudflare.source(url)
            
            result = client.parseDOM(result, 'a', ret='href')
            result = [i for i in result if '.php' in i and 'i=' in i]
            result = [client.replaceHTMLCodes(i) for i in result]

            try:
                url = []
                for i in result:
                    try: url.append(base64.decodestring(urlparse.parse_qs(urlparse.urlparse(i).query)['i'][0]))
                    except: pass
                url = [i for i in url if i.startswith('http')][0]
                if not 'google' in url: raise Exception()
                url = resolvers.request(url)
                for i in url: sources.append({'source': 'GVideo', 'quality': i['quality'], 'provider': 'YIFYstream', 'url': i['url']})
            except:
                pass

            try:
                url = [i for i in result if 'p=shtml' in i][0]
                url = client.source(url)

                try: sources.append({'source': 'GVideo', 'quality': '1080p', 'provider': 'YIFYstream', 'url': [i for i in client.parseDOM(url, 'source', ret='src', attrs = {'data-res': '1080'}) if 'google' in i][0]})
                except: pass
                try: sources.append({'source': 'GVideo', 'quality': 'HD', 'provider': 'YIFYstream', 'url': [i for i in client.parseDOM(url, 'source', ret='src', attrs = {'data-res': '720'}) if 'google' in i][0]})
                except: pass
                try: sources.append({'source': 'GVideo', 'quality': 'SD', 'provider': 'YIFYstream', 'url': [i for i in client.parseDOM(url, 'source', ret='src', attrs = {'data-res': '480'}) if 'google' in i][0]})
                except: sources.append({'source': 'GVideo', 'quality': 'SD', 'provider': 'YIFYstream', 'url': [i for i in client.parseDOM(url, 'source', ret='src', attrs = {'data-res': '360'}) if 'google' in i][0]})
            except:
                pass

            try:
                url = [i for i in result if 'p=open' in i][0]
                url = urlparse.parse_qs(urlparse.urlparse(i).query)['i'][0]
                url = 'https://openload.io/f/%s' % url
                url = resolvers.request(url)
                if url == None: raise Exception()
                sources.append({'source': 'Openload', 'quality': 'HD', 'provider': 'YIFYstream', 'url': url})
            except:
                pass

            return sources
        except:
            return sources


    def resolve(self, url):
        try:
            if not 'google' in url: return url

            if url.startswith('stack://'): return url

            url = client.request(url, output='geturl')
            if 'requiressl=yes' in url: url = url.replace('http://', 'https://')
            else: url = url.replace('https://', 'http://')
            return url
        except:
            return

