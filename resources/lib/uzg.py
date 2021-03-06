'''
    resources.lib.uzg
    ~~~~~~~~~~~~~~~~~

    An XBMC addon for watching Uitzendinggemist(NPO)
   
    :license: GPLv3, see LICENSE.txt for more details.

    Uitzendinggemist (NPO) = Made by Bas Magre (Opvolger)    
    based on: https://github.com/jbeluch/plugin.video.documentary.net

'''
import urllib2 ,re ,time ,json
from datetime import datetime

class Uzg:
        #
        # Init
        #
        def __init__( self):
            self.overzichtcache = 'leeg'
            self.items = 'leeg'            

        def __overzicht(self):        
            req = urllib2.Request('http://apps-api.uitzendinggemist.nl/series.json')
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
            response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            json_data = json.loads(link)
            uzgitemlist = list()
            for serie in json_data:
                uzgitem = { 'label': serie['name'], 'nebo_id': serie['nebo_id'], 'thumbnail': serie['image'] }
                uzgitemlist.append(uzgitem)                
            self.overzichtcache = sorted(uzgitemlist, key=lambda x: x['label'], reverse=False)
            
        def __items(self, nebo_id):
            req = urllib2.Request('http://apps-api.uitzendinggemist.nl/series/'+nebo_id+'.json')
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
            response = urllib2.urlopen(req)
            link=response.read()
            response.close()
            json_data = json.loads(link)
            uzgitemlist = list()
            for aflevering in json_data['episodes']:
                urlcover = ''
                if not aflevering['stills']:
                    urlcover = ''
                else:
                    urlcover = aflevering['stills'][0]['url']
                uzgitem = { 'label': aflevering['name']
                            , 'date': self.__stringnaardatumnaarstring(datetime.fromtimestamp(int(aflevering['broadcasted_at'])).strftime('%Y-%m-%dT%H:%M:%S'))
                            , 'TimeStamp': datetime.fromtimestamp(int(aflevering['broadcasted_at'])).strftime('%Y-%m-%dT%H:%M:%S')
                            , 'thumbnail': urlcover
                            , 'serienaam': json_data['name']
                            , 'whatson_id': aflevering['whatson_id']}
                uzgitemlist.append(uzgitem)
            self.items = uzgitemlist

        def __get_data_from_url(self, url):
            req = urllib2.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:25.0) Gecko/20100101 Firefox/25.0')
            response = urllib2.urlopen(req)
            data=response.read()
            response.close()
            return data    

        def get_ondertitel(self, whatson_id):
            return 'http://apps-api.uitzendinggemist.nl/webvtt/'+whatson_id+'.webvtt'
            
        def get_play_url(self, whatson_id):
            ##token aanvragen
            data = self.__get_data_from_url('http://ida.omroep.nl/npoplayer/i.js')
            token = re.compile('.token\s*=\s*"(.*?)"', re.DOTALL + re.IGNORECASE).search(str(data)).group(1)
            ##video lokatie aanvragen
            data = self.__get_data_from_url('http://ida.omroep.nl/odi/?prid='+whatson_id+'&puboptions=adaptive&adaptive=yes&part=1&token='+self.__get_newtoken(token))
            json_data = json.loads(data)
            ##video file terug geven vanaf json antwoord
            streamdataurl = json_data['streams'][0]
            streamurl = str(streamdataurl.split("?")[0]) + '?extension=m3u8'
            data = self.__get_data_from_url(streamurl)
            json_data = json.loads(data)
            url_play = json_data['url']
            return url_play
            
        def __get_newtoken(self, token):
            # site change, token invalid, needs to be reordered. Thanks to rieter for figuring this out very quickly.
            first = -1
            last = -1
            for i in range(5, len(token) - 5, 1):	
                if token[i].isdigit():
                    if first < 0:
                        first = i                
                    elif last < 0:
                        last = i                
                        break

            newtoken = list(token)
            if first < 0 or last < 0:
                first = 12
                last = 13
            newtoken[first] = token[last]
            newtoken[last] = token[first]
            newtoken = ''.join(newtoken)    
            return newtoken            


        def get_overzicht(self):
            self.items = 'leeg' ##items weer leeg maken
            if (self.overzichtcache == 'leeg'):
                self.__overzicht()
            return self.overzichtcache            


        def get_items(self, nebo_id):
            if (self.items == 'leeg'):
                self.__items(nebo_id)
            return [self.__build_item(i) for i in self.items]
    
        def __build_item(self, post):    
            ##item op tijd gesorteerd zodat ze op volgorde staan.
            if (len(post['label']) == 0):
                titelnaam = post['serienaam']
            else:
                titelnaam = post['label']

            item = {
                'label': '(' + post['TimeStamp'].split('T')[1] + ') - ' + titelnaam,
                'date': post['date'],
                'thumbnail': post['thumbnail'],
                'whatson_id': post['whatson_id'],
            }
            return item

        def __stringnaardatumnaarstring(self, datumstring):
            b = datetime(*(time.strptime(datumstring.split('T')[0], "%Y-%m-%d")[0:6]))
            return b.strftime("%d-%m-%Y")