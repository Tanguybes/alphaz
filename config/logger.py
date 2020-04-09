import traceback, inspect, os, time, sys, uuid, datetime
import mysql.connector, inspect
from Libs import sql_lib

class Logger():

    def __init__(self, cnx_fct=None, log_file=None):
        self.CNX_FCT     = cnx_fct
        self.LOG_FILE    = log_file

        self.PROCESSES   = {}
        
    def info(self, text):
        text = get_current_short_date() + ' - ' + text
        print('INFO  : ',text)
        #append_log(text)
        
    def warning(self, text):
        text = get_current_short_date() + ' - ' + text
        print('WARNING: ' + text)
        #append_log(text)
        
    def error(self, text, save=True):
        if isinstance(text, Exception):
            text    = traceback.format_exc()

        frame       = inspect.stack()[1]
        module      = inspect.getmodule(frame[0])
        origin      = "Unknowned"
        if module is not None:
            origin  = os.path.basename(module.__file__)
        if save:
            self.__log_in_db(text, origin=origin, type="error")
        text        = get_current_short_date() + ' - ' + str(text)
        print("ERROR: ",text)
        if save:
            self.append_log(text)

    def process_start(self,name,parameters):
        uuid_process                    = str(uuid.uuid4())
        self.PROCESSES[uuid_process]    =  {'uuid':uuid,'name':name, 'parameters':parameters,'datetime':datetime.datetime.now()}
        self.process_log(uuid_process, name, parameters, 'START')
        return uuid_process

    def process_end(self, uuid_process, name, parameters, error=None):
        PROCESS_INFOS                   = None
        if uuid_process in self.PROCESSES:
            PROCESS_INFOS               = self.PROCESSES[uuid_process] 

        status = 'INFOS'
        if PROCESS_INFOS is not None:
            if name != PROCESS_INFOS['name']:
                status      = 'NAME'
            elif parameters != PROCESS_INFOS['parameters']:
                status      = 'PARAM'
            name        = PROCESS_INFOS['name']
            parameters  = PROCESS_INFOS['parameters']
            status      = 'END'

        if error is not None:
            status = str(error)

        if uuid_process is not None:
            self.process_log(uuid_process, name, parameters, status)

    def process_log(self, uuid_process, name, parameters, status):
        if type(parameters) != str:
            parameters = ';'.join([str(x) for x in parameters])

        query       = "INSERT INTO `processes_logs` (`uuid`, `name`, `parameters`, `status`) VALUES (%s,%s,%s,%s)"
        parameters  = [uuid_process, name, parameters, status]

        self.__execute_query('process_log',query, parameters)

    def processes_clean(self):
        cnx     = self.CNX_FCT()
        if cnx is None:
            return
        
        query       = "select distinct `name` from `processes_logs`"
        names       = cnx.get_query_results(query, None, unique=True, close_cnx=False)

        limit       = 2*50

        for name in names:
            query       = "select distinct `uuid` from `processes_logs` where `name` = %s order by `update_date` desc limit %s"
            uuids       = cnx.get_query_results(query, [name, limit], unique=True, close_cnx=False)
            uuids.append('') # So that len(uuids) >= 1)

            in_statement = '(' + ','.join(["'%s'"%x for x in uuids]) + ')'
            query       = "delete from `processes_logs` where `name` = %s and `uuid` not in " + in_statement
            parameters  = [name]
            cnx.execute_query(query,parameters, close_cnx=False)
        try:    
            cnx.close()
        except:
            pass

    def append_log(self, text):
        log_path = self.LOG_FILE
        if log_path is None:
            return
        with open(log_path, 'a+') as flog:
            flog.write(text+'\n')
    
    def print_error(self, error_msg, raise_exception=True):
        '''Display the last error catched'''
        if (str(error_msg)[:3] == '-W-'):
            print('#-# WARNING #-#: ' + str(error_msg)[3:])
        else:
            error_msg = '#-# ERROR #-#: ' + str(error_msg)
            error_msg += ' -----> ' + str(sys.exc_info()[0])
            self.error(error_msg)
            if raise_exception == True:
                raise Exception(0,'#-# ERROR #-#')
    
    def trace_show(self):
        traceback.print_exc()
    
    def __log_in_db(self, message, origin="unspecified", type="unspecified"):
        # Connect to db
        stackraw    = traceback.format_stack()
        stack       = ''.join(stackraw) if stackraw is not None else ''
        try:
        #         cnx     = mysql.connector.connect(user=Core.LOGIN, password=Core.PWD, host=Core.HOST, database=Core.DATABASE)
            cnx     = None if self.CNX_FCT is None else self.CNX_FCT()
            if cnx is None:
                return

            query   = ("INSERT INTO golliath_logs (type, origin, message, stack, date) VALUES (%s, %s, %s, %s, UTC_TIMESTAMP())")
            cursor  = cnx.cursor()
            cursor.execute(query, (type, origin, message, stack))
            cnx.commit()
            cursor.close()
        except mysql.connector.Error as err:
            # The only one place where we don't want to call error()
            print("ERROR (log in db): ", err)
        
        try:
            cnx.close() 
        except:
            pass

    def __execute_query(self, name, query,values):
        try:
            cnx     = self.CNX_FCT()
            if cnx is None:
                return
            cursor  = cnx.cursor()
            cursor.execute(query, values)
            cnx.commit()
            cursor.close()
        except mysql.connector.Error as err:
            print("ERROR (%s): %s"%(name, str(err)))
        
        try:
            cnx.close() 
        except:
            pass

def exception_to_string(excp,short=False):
    if not short:
        stack   = traceback.extract_stack()[:-3] + traceback.extract_tb(excp.__traceback__)
    else:
        stack   =  traceback.extract_tb(excp.__traceback__)
    pretty  = traceback.format_list(stack)
    return ''.join(pretty) + '\n  {} {}'.format(excp.__class__,excp)

def get_current_short_date():
    ''' Get the current date in short format '''
    date_ref = time.strftime('%Y-%m-%d %H:%M:%S')
    return date_ref
        
log = Logger()
