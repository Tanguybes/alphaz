import argparse

from importsP import *
from imports import *

class GolliathBatch(argparse.ArgumentParser):
    args = None
    name = None
    process_uuid = None
    parameters = []

    def __init__(self,name,description='',prog='Golliath'):
        self.name = name
        super().__init__(prog=prog, description=prog + ' ' + description, epilog=prog)

        self.add_argument('--currencies', '-C', nargs='+', help='List of currencies to analyze')
        self.add_argument('--intervals', '-I', nargs='+', help='Intervals to use')

        self.add_argument('--currency', '-c', help='Currency to analyze')
        self.add_argument('--interval', '-i', help='Interval to use')

        self.add_argument('--debug', '-d', action='store_true', help='Debug mode')
        self.add_argument('--test', '-t', action='store_true', help='Test mode')

        self.add_argument('--verbose', '-v', action='store_true', help='Verbose mode')

        self.add_argument('--markets', '-M', help='Markets', nargs='+')
        self.add_argument('--market', '-m', help='Market')

        self.add_argument('--platform', '-p', help='Platform')

        self.add_argument('--strategies', '-s', help='Strategies', nargs='+')
        self.add_argument('--categories', '-Cat', help='Categories', nargs='+')
        self.add_argument('--category', '-cat', help='Category')

        self.add_argument('--new', '-n', action='store_true', help='New mode')

    def start(self,parameters=[]):
        parameters          = [self.name] + [ x if type(x) != list else ';'.join(x) for x in parameters]
        self.parameters     = parameters
        self.process_uuid   = log.process_start(self.name, self.parameters)
        lib.tic()

    def end(self,error=None):
        lib.tac()
        log.process_end(self.process_uuid, self.name, self.parameters,error=error)

    def kill(self):
        self.end('KILL')

    def error(self,error=''):
        log.error(str(error),save=True)
        self.end('ERROR')

    def set_args(self):
        self.args = super().parse_args()
        return self.args

    def add_argument(self,*kargs, **kwargs):
        super().add_argument(*kargs, **kwargs)

    def get_platform(self):
        from CryptosApis import cryptosapis

        if not 'platform' in vars(self.args):
            log.error('Missing platform argument definition')
            custom_exit()

        platforms       = cryptosapis.apis()
        if self.args.platform is None:
            log.error('You have to specify a platform in: %s'%(', '.join(platforms)))
            custom_exit()
        PLATFORM_NAME   = self.args.platform.capitalize()
        if PLATFORM_NAME not in platforms:
            log.error('Wrong platform name <%s>, it is not in: %s!'%(PLATFORM_NAME, ', '.join(platforms)))
            custom_exit()
        PLATFORM                        = cryptosapis.apis()[PLATFORM_NAME]

        return PLATFORM, PLATFORM_NAME

    def get_value(self,default=None, value=None, name=''):
        if value is None:
            if default is None:
                log.error('You have to specify a market')
                custom_exit()     
            return default
        return value     

    def get_values(self,defaults=None, value=None, values=None, name=''):
        if values is None:
            if value is None:
                if defaults is None:
                    log.error('You have to specify a %s'%name)
                    custom_exit()
                return defaults
            return [value]
        
        return [x for x in values if x != '']

    def get_interval(self,base=False):
        authorized_interval = CoreS.BASE_INTERVALS_TO_USE if base else CoreS.INTERVALES_TO_USE

        if self.args.interval is None or self.args.interval not in authorized_interval:
            log.error('You have to specify an interval in: %s'%(', '.join(authorized_interval)))
            custom_exit()

        return self.args.interval

    def get_intervals(self,base=False):
        authorized_interval = CoreS.BASE_INTERVALS_TO_USE if base else CoreS.INTERVALES_TO_USE

        if self.args.intervals is None:
            return [self.get_interval()]
            #list_intervals          = CoreS.INTERVALES_TO_USE
            log.error('You have to specify an interval in: %s'%(', '.join(authorized_interval)))
            custom_exit()

        return self.args.intervals

    def get_market(self,default=None):
        return get_value(self,default=default, value=self.args.market, name='market')

    def get_markets(self,defaults=None):
        return self.get_values(defaults=defaults,value=self.args.market,values=self.args.markets,name='market')

    def get_category(self,default=None):
        return get_value(self,default=default, value=self.args.category, name='category')

    def get_categories(self,defaults=None):
        return self.get_values(defaults=defaults,value=self.args.category,values=self.args.get_categories,name='category')
