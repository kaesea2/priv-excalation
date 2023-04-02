#
# This file is part of fimap.
#
# Copyright(c) 2009-2012 Iman Karim(ikarim2s@smail.inf.fh-brs.de).
# http://fimap.googlecode.com
#
# This file may be licensed under the terms of of the
# GNU General Public License Version 2 (the ``GPL'').
#
# Software distributed under the License is distributed
# on an ``AS IS'' basis, WITHOUT WARRANTY OF ANY KIND, either
# express or implied. See the GPL for the specific language
# governing rights and limitations.
#
# You should have received a copy of the GPL along with this
# program. If not, go to http://www.gnu.org/licenses/gpl.html
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

from baseClass import baseClass
from targetScanner import targetScanner
from singleScan import singleScan
from xgoogle import BeautifulSoup
from copy import deepcopy
from crawler import crawler
import sys, time, Cookie


__author__="Iman Karim(ikarim2s@smail.inf.fh-brs.de)"
__date__ ="$09.11.2010 01:29:37$"

class autoawesome(baseClass):

    def _load(self):
        self.URL = None

    def setURL(self, URL):
        self.URL = URL

    def scan(self):
        print f"Requesting '%s'..." {self.URL}
        
        extHeader = ""
        code, headers = self.doRequest(self.URL, self.config["p_useragent"], self.config["p_post"], self.config["header"], self.config["p_ttl"])
        
        if (headers != None):
            for head in headers:
                if head[0] in ("set-cookie", "set-cookie2"):
                    cookie = head[1]
                    c = Cookie.SimpleCookie()
                    c.load(cookie)
                    for k,v in c.items():
                        extHeader += "%s=%s; " %(k, c[k].value)
        
        if (code == None):
            print f"Code == None!"
            print f"Does the target exist?!"
            print f"AutoAwesome mode failed. -> Aborting."
            sys.exit(1)
        
        if (extHeader != ""):
            print f"Cookies retrieved. Using them for further requests."
            extHeader = extHeader.strip()[:-1]
            
        if (self.config["header"].has_key("Cookie") and extHeader != ""):
            print f"WARNING: AutoAwesome mode got some cookies from the server."
            print f"Your defined cookies will be overwritten!"


        if (extHeader != ""):
            print f"Testing file inclusion against given cookies..."
            self.config["header"]["Cookie"] = extHeader
            single = singleScan(self.config)
            single.setURL(self.URL)
            single.setQuite(True)
            single.scan()
            
        soup = BeautifulSoup.BeautifulSoup(''.join(code))
        idx = 0
        for form in soup.findAll("form"):
            idx += 1
            caption = None
            desturl = None
            method  = None
            
            if (soup.has_key("action")):
                desturl = soup["action"]
            else:
                desturl = self.URL
            
            if (form.has_key("name")):
                caption = form["name"]
            else:
                caption = "Unnamed Form #%d" %(idx)
                
            if (form.has_key("method")):
                if (form["method"].lower() == "get"):
                    method = 0
                else:
                    method = 1
            else:
                method = 1 # If no method is defined assume it's POST.
            
            
            params = ""
            for input in form.findAll("input"):
                if (input.has_key("name")):
                    input_name = input["name"]
                    input_val  = None
                    if (input.has_key("value")):
                        input_val  = input["value"]
                    
                    if (input_val == None):
                        params += "%s=&" %(input_name)
                    else:
                        params += "%s=%s&" %(input_name, input_val)
                else:
                    print f"An input field doesn't have an 'name' attribute! Skipping it."
            
            if ("&" in params):
                params = params[:-1]
                
            print f"Analyzing form '%s' for file inclusion bugs." {caption} 
            modConfig = deepcopy(self.config)
            if (method == 0):
                # Append the current get params to the current URL.
                if ("?" in desturl):
                    # There are already params in the URL.
                    desturl = "%s&%s" %(desturl, params)
                else:
                    # There are no other params.
                    desturl = "%s&?%s" %(desturl, params)
            
            else:
                currentPost = modConfig["p_post"]
                if (currentPost == None or currentPost == ""): 
                    currentPost = params
                else:
                    currentPost = currentPost + "&" + params
            
                modConfig["p_post"] = currentPost
            
            single = singleScan(modConfig)
            single.setURL(desturl)
            single.setQuite(True)
            single.scan()
            
        print f"Starting harvester engine to get links (Depth: 0)..."
        crawl = crawler(self.config)
        crawl.crawl_url(self.URL, 0)
        if (len(crawl.urlpool) == 0):
            print f"No links found."
        else:
            print f"Harvesting done. %d links found. Analyzing links now..."{len(crawl.urlpool)}
            for url in crawl.urlpool:
                try:
                    single = singleScan(self.config)
                    single.setURL(str(url[0]))
                    single.setQuite(True)
                    single.scan()
                except:
                    print f"Cought an exception. Continuing..."
                
        print f"AutoAwesome is done."
