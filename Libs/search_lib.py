from bs4 import BeautifulSoup

from serpapi.google_search_results import GoogleSearchResults
from googlesearch import search

class GoogleSearch():
    def scrap_api(self,search_string):
        print('scrap api')
        apikey = 'f22df9d6edeba41d3888a7384a4d945ed099efc202535f81ca4a58f6c7557afd'

        params = {
            "q" : search_string,
            "location" : "Grenoble, France",
            "hl" : "fr",
            "gl" : "fr",
            "google_domain" : "google.fr",
            "api_key" : apikey,
            "num":100
        }

        query               = GoogleSearchResults(params)
        dictionary_results  = query.get_dictionary()

    def analyse(self):
        """for key, config in dictionary_results.items():
            print(key,'\n', config)"""
            
        if 'produt_result' in dictionary_results:
            self.product = dictionary_results['produt_result']

        if 'organic_results' in dictionary_results:
            for element in dictionary_results['organic_results']:
                """for key,value in element.items():
                    print(key)
                    print('   ',value)"""

                self.process_sequence(element['title'])
                self.process_sequence(element['snippet'])

                if 'rich_snippet' in element:
                    if 'top' in element['rich_snippet']:
                        if 'extensions' in element['rich_snippet']['top']:
                            self.process_list(element['rich_snippet']['top']['extensions'])

    def scrap(self,search_string):
        if search_string == '': return

        print('Scrapping ...',self.code)

        URL     = "https://www.google.com/search?"
        PARAMS  = {'q':self.code, 'num':100}
        proxy = next(proxy_pool)
        #headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0'}

        r       = requests.get(url = URL, params = PARAMS,timeout=0.5) #,proxies={"http": proxy, "https": proxy} 
        html    = r.text

        with open('/tmp/trash/tmp.html','w') as f:
            f.write(html)

        soup = BeautifulSoup(r.text,"html.parser")

        mydivs = soup.findAll("div", {"class": "BNeawe"})

        self.process_list(mydivs)

    def process_sequence(self,sequence):
        self.process_list([sequence])

    def process_list(self,list_to_process):
        self.prices = []
        i = 0
        for div in list_to_process:
            #print('process %s / %s'%(i,len(list_to_process)))

            div_content = re.sub('<[^>]*>', '', str(div))
            #print(div_content)

            prices = re.findall("(\d+.\d+,\d+ €|\d+,\d+ €|\d+.\d+ €)", div_content)
            if len(prices) != 0:
                for price in prices:
                    try:
                        rpl = price.replace('€','').replace(' ','').replace(',','.')
                        a = float(rpl)
                        self.prices.append(a)
                    except Exception as ex:
                        print(ex)
                    #print('   ',div_content)
                    div_content = div_content.replace(price,'')

            words = get_words(div_content)

            for word in words:
                word = word.lower()
                if not word in self.words:
                    self.words[word] = 1
                else:
                    self.words[word] += 1