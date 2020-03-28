'''
Created on 24 juin 2018

@author: aurele
'''
import re, os, copy, traceback

from ..libs.converter_lib import to_int
from ..libs import py_lib, io_lib
from .logger import AlphaLogger

def reload_modules(verbose=False):
    reload_path = os.getcwd()
    #print('Reload modules at %s'%reload_path)
    py_lib.reload_modules(reload_path,verbose=verbose)
    reload_path = os.sep.join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[:-1])
    #print('Reload modules at %s'%reload_path)
    py_lib.reload_modules(reload_path,verbose=verbose)

class SelectionMenu():
    name = None
    save_directory = None

    def __init__(self, name, parameters, save_directory, config_file=None, config_folder='config/menus', gui=False,log=None):
        if log is None:
            log = AlphaLogger('selection_menu')
        self.name           = name
        self.save_directory = save_directory

        self.parameters     = parameters        
        self.returnValue    = None

        self.exit           = False
        self.log            = log

        self.PASS_ARG       = "pass:"

        self.config_folder  = config_folder
        self.config_file    = config_file
        
        self.load_default_values()
        
    def debugPrint(self,string):
        if self.get_value("debug_menu"):
            print(__name__,string)

    def debugInfo(self,string):
        if self.get_value("debug_menu"):
            self.log.info(string)

    def getIntersectionWithDict(self,dictI):
        backtestValues = {}
        backtestParameters = dictI.keys()
        for backtestParameter in backtestParameters:
            if self.exist(backtestParameter):
                backtestValues[backtestParameter] = self.get_value(backtestParameter)
        return backtestValues
        
    def run(self):
        while not self.exit:
            self.execute(self.parameters)
            input('Press enter to continue ...')
        return self.returnValue
        
    def execute(self,conf):
        try:
            reload_modules()

            if "before" in conf:        self.execute(conf["before"])

            # BETWEEN
            if 'set' in conf:
                for key, value in conf['set'].items():
                    self.set_value(key, self.convertArgument(value)) #,convert=self.getParameterValue(config,'convert'))

            if 'switch' in conf:
                if type(conf['switch']) == dict:
                    for key in conf['switch']:
                        self.switch_value(key)
                else:
                    self.switch_value(conf['switch'])

            self.functionsEvaluate(conf)
            self.printEvaluate(conf)

            if "input" in conf:
                value                                       = input("\nValue: ")
                self.set_value(conf['set'], self.convertArgument(value,convert=self.getParameterValue(conf,'convert')) )

            """if 'selected' in MODE:
                self.execute({})"""
            if "quit" in conf or "exit" in conf:
                self.exit                                   = True

            # set returning value
            if 'return' in conf:
                self.returnValue                            = self.convertArgument(conf['return'])

            # SELECTIONS
            if "selections" in conf:    self.select(conf["selections"]) 
            if "after" in conf:         self.execute(conf["after"]) 
        except Exception as ex:
            text    = traceback.format_exc()
            print('ERROR:\n\n',str(text))

        """if self.getParameterValue(executingConfig,'bypass') is not None:
            conf                                      = executingConfig  
        else:
            conf                                      = self.select(executingConfig)"""
             
        #self.valueEvaluate(conf)
              
        ### SELECTION MENU  
        """if 'selection' in MODE:
            selectionValues                             = self.getParameterValue(conf,'selection_values')
            multiple                                    = 'selections'  in MODE
            key_mode                                    = 'key'         in MODE
            #             selectionValues = self.getParameterValue(conf,'selection_values')
            if selectionValues is not None:
                newConfig                               = self.getConfigFromValues(conf,selectionValues,multiple=multiple,key_mode=key_mode)
            else:
                newConfig                               = conf['selection_config']"""
           
    def select(self,selections_config):
        commands_selections     = self.get_commands()
        formatStr               = '{:7} {:40} {:30} {}'

        conf     = {}
        selected = None
        while selected is None:
            self.debugPrint('      VALUES:%s'%str(self.values))
            i                       = 0
            selections              = {x['key']:x for x in commands_selections if 'key' in x}
        
            select_list             = copy.copy(commands_selections)
            select_list.extend(selections_config)

            for conf in select_list:
                if type(conf) == dict:
                    desc                = self.getString(conf,'description')
                    name                = self.getString(conf,'name')

                    if "header" in conf:
                        print("\n"+formatStr.format("","== " + conf['header'] + " ==","",desc)+"\n")
                        continue

                    #activate            = conf['mode'] == 'activate' if 'mode' in conf.keys() else False
                    #self.debugPrint("name - select configuration: %s"%conf)

                    #self.valueEvaluate(conf,start=True)
                    #self.functionsEvaluate(conf,start=True)

                    key                 = conf['key'] if 'key' in conf.keys() else str(i)
                    
                    # DEFAULT VALUE
                    #if not self.getParameterValue(conf, 'no_default'):
                    default         = "" if not 'name' in conf else self.get_value(conf['name'])
                    if default is None and 'value' in conf:
                        default     = conf['value']
                    elif default is None:
                        default     = ""

                    if type(default) == bool:
                        switch      = 'switch' in conf.keys()
                        if switch:
                            default = 'ON' if default else 'OFF'
                        else:
                            default = "Y" if default else "N"

                    """if 'mode' in conf.keys() and conf['mode'] == 'activate':
                        default = str(key) in str(default).split(',')"""
                                                                    
                    show = True
                    if 'show' in conf.keys():
                        show            = conf['show']
                        vshow           = self.get_value(show)
                        show            = vshow if vshow is not None else show
                        
                    if show:
                        print(formatStr.format(str(key),name,str(default),desc))
                    
                    self.printEvaluate(conf)
                    
                    selections[key]     = conf

                    if not 'key' in conf:
                        i += 1
                else:
                    self.set_value('selected', conf)
                        
            selection            = input(("DEBUG MODE: " if self.get_value("debug_menu") else "")+ "\nSelection > ").lower()

            """if re.match("([0-9]+$)", rawSelection):
                selection, ok       = to_int(rawSelection)
            else:
                selection, ok       = rawSelection, True"""
                        
            #if ok:
            is_command           = re.match("(^[^0-9]+$)", str(selection))
            if is_command:
                commands            = [x['key'] for x in select_list if 'key' in x]

                if selection in commands:
                    conf            = [x for x in select_list if 'key' in x and x['key'] == selection][0]
                else:
                    commandFounds   = 0
                    for command in commands:
                        m           = re.match("("+selection+"[^0-9]+$)", command.lower())
                        if m:
                            commandFound  = m.groups()[0]
                            commandFounds += 1
                            
                    if commandFounds != 1:
                        print('\n>>>> ERROR: command not recognized be more specific !')
                        continue
                    else:
                        conf          = selections[commandFound]
            else:
                if not selection in selections.keys():
                    continue
                
                """if activate:    
                    activated_values = str(self.values[conf['set']]).split(',')
                    
                    if str(selection) in activated_values:
                        activated_values.remove(str(selection))
                        self.values[conf['set']] = ','.join(activated_values)
                    else:
                        old                         = self.values[conf['set']]
                        self.values[conf['set']]  = str(old) + ',' + str(selection) if str(old) != '' else str(selection)
                        
                    print('SELECTED: %s'%self.values[conf['set']])
                    continue
                else:"""
                conf = selections[selection]

            selected = True
        
        print('SELECTED: ',conf)
        self.execute(conf)

    def get_commands(self):
        selections = []
        selections.append({'header':"COMMANDS"})
        selections.append({'key':'q','function':self.quit,'name':'Quit','description':"Quit the menu"})
        selections.append({'key':'dm',"value":False,'switch':'debug_menu','name':'Debug menu','description':"Turn ON/OFF the menu debug mode"})
        selections.append({'key':'d',"value":False,'name':'Debug','switch':'debug','description':"Turn ON/OFF the debug mode"})
        selections.append({'key':'s','function':self.save_config,'name':'Save configuration','description':"Save the current configuration"})
        selections.append({'key':'m',"value":False,'switch':'more','name':'More','description':"Show more configurations"})
        selections.append({'key':'r','name':'Reload','description':"Reload modules","function":reload_modules})
        selections.append({'key':'b','name':'Back','description':"Go back"})

        print('   >>> CONFIG')
        for s in selections:
            if 'value' in s and 'name' in s and self.get_name(s['name']) not in self.values:
                self.set_value(s['name'],s['value'])

        return selections

    def get_name(self,name):
        return name.lower().replace(' ','_')

    def set_value(self,name,value):
        name = self.get_name(name)
        print('   Set value %s to %s'%(name,value))
        self.values[name] = value

    def switch_value(self,name):
        print('                      1 VALUES, ',self.values)
        name = self.get_name(name)
        if name in self.values and type(self.values[name]) == bool:
            print('   Switch value %s from %s to %s'%(name,self.values[name],not self.values[name]))
            self.values[name] = not self.values[name]
            print('                      4 VALUES, ',self.values)

    """def valueEvaluate(self,conf,start=False):
        start           = "start:" if start else ""
        set_key         = 'set_key' in conf
        keyRaw          = 'value' if not set_key else 'key'
        
        key             = start + keyRaw
        keySet          = start + 'set'
        
        parameters      = conf.keys()    
        
        #### VALUE
        value           = conf[key] if key in parameters else (conf[keyRaw] if keyRaw in parameters else None)

        # set a value
        if keySet in parameters and value is not None:
            self.values[conf[keySet]] = value"""

    def functionsEvaluate(self,conf):
        functions_config = []
        if 'function' in conf:
            functions_config.append(conf['function'])
        if 'functions' in conf:
            functions_config.extend(conf['functions'])

        if len(functions_config) != 0:
            print('EXEC',functions_config)
            print('                      2 VALUES, ',self.values)
            for config in functions_config:
                kwargs = {}
                if type(config) == dict:
                    if  'kwargs' in config.keys():
                        raw_kwargs                                  = config[ 'kwargs']
                        kwargs                                      = self.convertArguments(raw_kwargs)
                    
                    if 'method' in config.keys():
                        fct                                         = config['method']
                        fct                                         = self.convertArgument(fct) if type(fct) == str else fct
                else:
                    fct = config

                if fct is not None:
                    functionReturn = fct(**kwargs)
                    self.set_value('return',functionReturn)

                    if type(config) == dict and 'name' in config:
                        self.set_value(config['name'],functionReturn)

    def printEvaluate(self,conf):
        pass
        """
        key                                             = 'print'

        parameters                                      = conf.keys()
        ### PRINT
        if key in parameters:
            output                                      = self.formatString(conf[key])
            print("\nOUTPUT: " + output + "\n")
            
        key                                             = 'infos'
        if key in parameters:
            output                                      = self.formatString(conf[key])
            print(output + "\n")
        """
                            
    def getConfigFromValues(self,valuesConfig,values,multiple=False,key_mode=False):
        parameters = valuesConfig.keys()

        self.debugInfo("Getting configuration from values: %s"%values)
        
        choices = {}
        i = 0
        if not type(values) == dict:
            for value in values:
                choices[i] = value
                i += 1
        else:
            choices = values
        
        conf = {}
        for key, value in choices.items():
            subConfig = dict()

            subConfig['value']      = value
            subConfig['key']        = key
            subConfig['no_default'] = not multiple
            if key_mode:
                subConfig['set_key']    = True 
            if multiple:
                subConfig['mode']       = 'activate'

            for key in parameters:
                if self.PASS_ARG in key:
                    self.setFromTo(valuesConfig,subConfig,key)
            conf[value] = subConfig
            self.debugPrint("sub configuration %s"%subConfig.keys())
        return conf
        
    def convertArguments(self,args):
        convertedArgs = {}
        for key, value in args.items():
            convertedArgs[key] = self.convertArgument(value)
        return convertedArgs

    def convertArgument(self,rawValue,convert=None):
        value = rawValue
        
        if type(rawValue) == dict:
            return rawValue

        # List
        elementList = False
        regex = "\[\d+\]"
        m = re.search(regex, str(rawValue))
        if m is not None:
            group = m.group(0)
            positionRaw = group.replace('[','').replace(']','')
            position = self.convertArgument(positionRaw,convert=int)
            rawValue = rawValue.replace(group,'')
            elementList = True

        # Range
        regex = "\[.*:.*\]"
        m = re.search(regex, str(rawValue))
        if m is not None:
            values = m.group(0).replace('[','').replace(']','').split(':')
            v1 = self.convertArgument(values[0],convert=int)
            v2 = self.convertArgument(values[1],convert=int)
            value = range(v1,v2)
            return value
        
        # Call dynamically a method from this class
        if rawValue in dir(self):
            value = getattr(self, rawValue)
            
        if '$' in str(rawValue):
            value = rawValue.replace('$','')
            if value in self.values.keys():
                value = self.values[value]

        #if elementList:
        #    print("%s > %s %s"%(rawValue,value,self.values.keys()))

        if elementList:
            value = value[position]
                
        if convert == int:
            convertion, ok = to_int(value)
            if ok:
                value = convertion

        return value

    def quit(self):
        print('   QUIT')
        self.exit = True
    
    def getString(self,conf,key):
        if key in conf.keys():
            return self.formatString(conf[key])
        return ''
    
    def isParameter(self,conf,parameter):
        return parameter in conf.keys()
    
    def get_value(self,parameter):
        parameter = parameter.lower()
        if not parameter in self.values.keys():
            return None
        return self.convertArgument(self.values[parameter])
    
    def getParameterValue(self,conf,parameter):
        if not self.isParameter(conf,parameter):
            return None
        return self.convertArgument(conf[parameter])
    
    def setFromTo(self,conf,newConfig,parameter):
        if parameter in conf.keys():
            subParameter = parameter.replace(self.PASS_ARG,'')
            newConfig[subParameter] = conf[parameter]
        
    def formatString(self,conf):
        if type(conf) == str:
            return conf
        args = self.convertArguments(conf['values']).values()

        return conf['str'].format(*args)
                
    def save_config(self):
        """defaultsValues = {}
        for key, value in self.values.items():
            if key in self.defaultskeys:
                defaultsValues[key] = value"""
        filename = self.save_directory + os.sep + self.name
        io_lib.archive_object(self.values,filename)
    
        #TODO: fix
        #write_menu_defaults_config_files(self.config_file,defaultsValues,test=False,directory=self.config_folder)

    def load_default_values(self):
        defaults        = {}
        filename        = self.save_directory + os.sep + self.name
        values          = io_lib.unarchive_object(filename)
        if values is not None:
            defaults = values
        else:
            self.log.error("No default values are specified")

        self.values = defaults
        self.defaultskeys   = list(defaults.keys())
        
        #TODO: change
        #defaults                            = load_config_file(config_file,directory=config_folder,sectionHeader=False,test=False)
        
    def showValue(self):
        for key, value in self.values.items():
            print("Menu values: %s: %s"%(key,value))
            
    def exist(self,name):
        return name in self.values.keys()
