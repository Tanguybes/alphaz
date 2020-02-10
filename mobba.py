

class Mobba():
    filepath    = ''
    code        = ''

    prices      = []

    words       = {}

    count       = 5

    top_words = {}

    valid = False

    api = True

    product = {}

    origin = None
    distance = None
    filepath= None

    test = False

    barre = None

    title = None

    def __init__(self,filepath):
        self.words = {}
        self.top_words = {}
        self.prices = []
        self.product = {}
        self.valid = False
        self.code = ''
        self.origin = None
        self.distance = None
        self.filepath = None
        self.barre = None
        self.title = None
        self.filepath = filepath

        code = barcode_lib.get_barcode(filepath)

        if code is not None:
            self.valid = True
            gf          = str(code).replace('b','').replace("'",'')
            self.code   = gf
            self.barre  = copy.copy(gf)

            self.try_decode()

            country_str = 'France'
            country     = self.code[:3]
            for COUNTRIE in COUNTRIES:
                nb = int(COUNTRIE)
                try:
                    nb = int(country)
                except:
                    self.valid = False
                    return
                if int(country) >= nb:
                    country_str = COUNTRIES[COUNTRIE]

            if country_str not in ORIGINS:
                location = geolocator.geocode(country_str.split('-')[0])
                if location is not None:
                    ORIGINS[country_str] = (location.latitude, location.longitude)
                else:
                    ORIGINS[country_str] = (0,0)

            self.origin   = country_str
            self.distance = int(geodesic(ORIGIN, ORIGINS[country_str]).km)

            if not self.test:
                self.scrap()

                self.code = self.get_top()

                print(len(self.words),self.code)

                self.scrap()

                self.code = self.get_top(self.count*2)

                print(len(self.words),self.code)

                #print(self.words)
            else:
                self.words = {'The':20,'Boisson':15,'Noir':10,'Fuze':5}
                self.prices = [2.5,3,2.1]
                self.get_top(4)

            self.valid = True
        else:
            print('Code not recognized ...')
            try:
                os.remove(self.filepath)
            except:
                pass

    def get_data(self):
        data = {}
        data['file'] = self.filepath
        data['valid'] = False

        if not self.valid:
            return data

        data['valid'] = True

        SUM = 0
        for cnt in list(self.top_words.values()):
            if cnt > 20:
                SUM += cnt
                #print(cnt)

        data['title']       = self.title
        data['barre']       = self.barre
        data['code']        = self.code.split('-')[0]
        data['words']       = list(self.top_words.keys())
        data['score']       = [ int((x / SUM) * 100) for x in list(self.top_words.values())]
        data['origin']      = self.origin
        data['distance']    = self.distance
        data['product']     = self.product
        data['prices']      = None
        data['CO2']         = get_CO2_from_distance(self.distance)
        data['score']       = random.choice(SCROES)
        if len(self.prices) > 1:
            data['prices'] = {'values':self.prices, 'min':np.min(self.prices), 'max': np.max(self.prices), 'std': np.std(self.prices), 'mean': np.mean(self.prices)}

        data['price']     = 0 if data['prices'] is None else data['prices']['mean']

        return data