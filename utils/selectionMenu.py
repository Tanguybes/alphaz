'''
Created on 24 juin 2018

@author: aurele
'''
import re

from ..libs.converter_lib import to_int
from .logger import AlphaLogger

class SelectionMenu():

    debug = False
    def __init__(self, parameters, config_file=None, config_folder='config/menus', gui=False,log=None):
        if log is None:
            log = AlphaLogger('selection_menu')
            
        self.parameters     = parameters        
        self.returnValue    = None

        self.exit           = False
        self.log            = log

        self.PASS_ARG       = "pass:"

        self.config_folder  = config_folder
        self.config_file    = config_file
        
        #TODO: change
        #defaults                            = load_config_file(config_file,directory=config_folder,sectionHeader=False,test=False)
        defaults            = {}

        self.defaultskeys   = list(defaults.keys())
        
        self.values         = defaults if defaults is not None else {}
        if defaults is None:
            self.log.error("No default values are specified",False)
        
    def debugPrint(self,string):
        if self.debug:
            print(__name__,string)

    def debugInfo(self,string):
        if self.debug:
            log.info(string)

    def switchDebug(self):
        self.debug = not self.debug

    def getIntersectionWithDict(self,dictI):
        backtestValues = {}
        backtestParameters = dictI.keys()
        for backtestParameter in backtestParameters:
            if self.exist(backtestParameter):
                backtestValues[backtestParameter] = self.getValue(backtestParameter)
        return backtestValues
        
    def run(self):
        while not self.exit:
            self.execute(self.parameters)
            input('Press enter to continue ...')
        return self.returnValue
        
    def valueEvaluate(self,conf,start=False):
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
            self.values[conf[keySet]] = value

    def functionEvaluate(self,conf,start=False):
        start                                           = "start:" if start else ""
        key                                             = start + 'function'
        keyArgs                                         = start + 'function:args'
        parameters                                      = conf.keys()
        
        ### FUNCTION
        arg = {}
        if keyArgs in parameters:
            rawArg                                      = conf[keyArgs]
            arg                                         = self.convertArguments(rawArg)
        
        if key in parameters:
            fct                                         = conf[key]
            fct                                         = self.convertArgument(fct) if type(fct) == str else fct
            
            if fct is not None:
                functionReturn = fct(**arg)
                if 'function:set' in parameters:
                    self.values[conf['function:set']] = functionReturn
                self.values['function:return']          = functionReturn

        key                                             = start + 'functions'
        keyArgs                                         = start + 'functions:args'

        ### FUNCTIONS        
        # args for functions
        functionArgs = []
        if keyArgs in parameters:
            for args in conf[keyArgs]:
                functionArgs.append(self.convertArguments(args))

        if key in parameters:
            i = 0
            for fct in conf[key]:
                fct                                     = self.convertArgument(fct)
                args                                    = functionArgs[i]
                functionReturn                          = fct(**args)

                if key+':set' in parameters:
                    self.values[conf[key+':set'][i]]  = functionReturn
                i                                       += 1

    def printEvaluate(self,conf,start=False):
        start                                           = "start:" if start else ""
        key                                             = start + 'print'

        parameters                                      = conf.keys()
        ### PRINT
        if key in parameters:
            output                                      = self.formatString(conf[key])
            print("\nOUTPUT: " + output + "\n")
            
        key                                             = start + 'infos'
        if key in parameters:
            output                                      = self.formatString(conf[key])
            print(output + "\n")

    def execute(self,executingConfig):
        if self.getParameterValue(executingConfig,'bypass') is not None:
            conf                                      = executingConfig  
        else:
            conf                                      = self.select(executingConfig)
             
        self.debugPrint('Selection options: %s'%conf)
        parameters                                      = conf.keys()
        
        mode                                            = conf['mode'] if 'mode' in parameters else ''
        
        if 'preset' in parameters:
            for key, value in conf['preset'].items():
                self.values[key]                       = self.convertArgument(value)#,convert=self.getParameterValue(config,'convert'))

        # set returning value
        if 'return' in parameters:
            self.returnValue                            = self.convertArgument(conf['return'])

        if mode == 'switch':
            if 'set' in parameters:
                self.values[conf['set']]              = not self.values[conf['set']]

        self.valueEvaluate(conf)
        self.functionEvaluate(conf)
        self.printEvaluate(conf)
              
        ### SELECTION MENU  
        if 'selection' in mode:
            selectionValues                             = self.getParameterValue(conf,'selection_values')
            multiple                                    = 'selections'  in mode
            key_mode                                    = 'key'         in mode
#             selectionValues = self.getParameterValue(conf,'selection_values')
            if selectionValues is not None:
                newConfig                               = self.getConfigFromValues(conf,selectionValues,multiple=multiple,key_mode=key_mode)
            else:
                newConfig                               = conf['selection_config']
            self.execute(newConfig)
        elif 'selected' in mode:
            print('SELECTED')
            self.execute({})
        elif mode == "continue":
            self.exit                                   = True
        elif mode == "value":
            value                                       = input("\nValue: ")
            self.values[conf['set']]                  = self.convertArgument(value,convert=self.getParameterValue(conf,'convert'))
                
    def setCommands(self,formatStr,selections):
        selections['quit']      = {'function':self.quit,'name':'Quit','description':"Quit the menu"}
        selections['menu']      = {'function':self.switchDebug,'name':'Menu debug','description':"Turn ON/OFF the menu debug mode"}
        selections['debug']     = {'name':'Debug','mode':'switch','set':'debug','description':"Turn ON/OFF the debug mode"}
        selections['save']      = {'function':self.save_config,'name':'Save configuration','description':"Save the current configuration"}
        selections['more']      = {'mode':'switch','set':'more','name':'More','description':"Show more configurations"}
        selections['back']      = {'mode':'','name':'Back','description':"Go back"}
        
        # === COMMANDS ===
        self.commands                = list(selections.keys())
        
        for key, conf in selections.items():
            switch              = False if not 'mode' in conf.keys() else conf['mode'] == 'switch'
            state               = "" if not switch else ('ON' if self.getValue(conf['set']) else 'OFF')
            print(formatStr.format(key,conf['name'],state,conf['description']))
        print('\n')
                
    def select(self,executingConfig):
        conf = {}
        selected = False
        while not selected:
            print('\n===== MENU =====\n')
            
            i                       = 0
            selections              = {}
            formatStr               = '{:7} {:40} {:30} {}'

            self.setCommands(formatStr,selections)

            for name, conf in executingConfig.items():
                activate            = conf['mode'] == 'activate' if 'mode' in conf.keys() else False
                
                self.debugPrint("name - select configuration: %s"%conf)

                self.valueEvaluate(conf,start=True)
                self.functionEvaluate(conf,start=True)

                desc                = "" if self.getDescription(conf) == "" else self.getDescription(conf)
                
                key                 = conf['key'] if 'key' in conf.keys() else i
                
                # DEFAULT VALUE
                default = ""
                if not self.getParameterValue(conf, 'no_default'):
                    if 'set' in conf.keys(): 
                        default     = self.getValue(conf['set'])
                    elif self.PASS_ARG+'set' in conf.keys():
                        default     = self.getValue(conf[self.PASS_ARG+'set'])
                        
                    if 'mode' in conf.keys() and conf['mode'] == 'activate':
                        default = str(key) in str(default).split(',')
                    
                    if type(default) == bool:
                        default     = "Y" if default else "N"
                
                if "header:" in str(name):
                    print("\n"+formatStr.format("","== " + name.replace('header:','') + " ==",str(default),desc)+"\n")
                    continue
                                
                show = True
                if 'show' in conf.keys():
                    show            = conf['show']
                    vshow           = self.getValue(show)
                    show            = vshow if vshow is not None else show
                if show:
                    print(formatStr.format(str(key),name,str(default),desc))
                
                self.printEvaluate(conf,start=True)
                self.printEvaluate(conf)
                
                selections[key]     = conf
                i                   += 1
                
            rawSelection            = input(("DEBUG MODE: " if self.debug else "")+ "\nSelection > ").upper()

            if re.match("([0-9]+$)", rawSelection):
                selection, ok       = to_int(rawSelection)
            else:
                selection, ok       = rawSelection, True
                        
            if ok:
                isCommand           = re.match("(^[^0-9]+$)", str(selection))

                if isCommand:
                    commandFounds   = 0
                    for command in self.commands:
                        m           = re.match("("+selection.lower()+"[^0-9]+$)", command.lower())
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
                    
                    if activate:    
                        activated_values = str(self.values[conf['set']]).split(',')
                        
                        if str(selection) in activated_values:
                            activated_values.remove(str(selection))
                            self.values[conf['set']] = ','.join(activated_values)
                        else:
                            old                         = self.values[conf['set']]
                            self.values[conf['set']]  = str(old) + ',' + str(selection) if str(old) != '' else str(selection)
                            
                        print('SELECTED: %s'%self.values[conf['set']])
                        continue
                    else:
                        conf = selections[selection]

                selected = True
                
        return conf
        
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
        exit()
    
    def getReturn(self):
        return self.getValue('function:return')
                  
    def getDescription(self,conf):
        if 'description' in conf.keys():
            return self.formatString(conf['description'])
        return ''
    
    def isParameter(self,conf,parameter):
        return parameter in conf.keys()
    
    def getValue(self,parameter):

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
        defaultsValues = {}
        for key, value in self.values.items():
            if key in self.defaultskeys:
                defaultsValues[key] = value
        
        #TODO: fix
        #write_menu_defaults_config_files(self.config_file,defaultsValues,test=False,directory=self.config_folder)

    def showValue(self):
        for key, value in self.values.items():
            print("Menu values: %s: %s"%(key,value))
            
    def getConfigValue(self,name):
        key = name.lower()
        if not key in self.values.keys():
            return None
        return self.values[key]

    def exist(self,name):
        return name in self.values.keys()
