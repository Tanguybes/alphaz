# coding: utf8

import sys, time, datetime, encodings
from telnet import Telnet

def cmd(commande):
    return commande.encode('ascii')
    
def universal_decode(txt,blacklist=[]):
    encodings_methods = list(set(encodings.aliases.aliases.values()))
    
    result, decoded = txt, False
    for encoding_method in encodings_methods:
        if encoding_method not in blacklist:
            try:
                result = txt.decode(encoding_method)
                print('Encoding %s works'%encoding_method)
                decoded = True
            except:
                pass
            if decoded:
                return result
    return result
    
def test_decode(txt):
    encodings_methods = list(set(encodings.aliases.aliases.values()))
    
    for encoding_method in encodings_methods:
        try:
            result = txt.decode(encoding_method)
            #print('Encoding %s works: %s'%(encoding_method, result))
            return result
        except:
            pass
    return None
            
class VMS:
    host        = "crv025.cro.st.com"
    user        = "wsm"

    d = datetime.date.today()
    password    = "hobbit%s%s"%('{:02d}'.format(d.month),str(d.year)[-2:])

    last_output = ""

    def __init__(self):
        self.reset_timer()
        print('Connecting to %s ...'%self.host)
        #self.cnx = telnetlib.Telnet(self.host)
        self.cnx = Telnet(self.host)
        self.cnx.set_debuglevel(2)
        print('   Connected')
        self.login()
        #self.set_terminal()
        
    def go_to(self,txt):
        self.cnx.read_until(cmd(txt))
        #self.cnx.expect([cmd(txt)],1)
        
    def read(self):
        return self.cnx.read_all().decode('utf-8')
        
    def write(self,txt):
        self.cnx.write(cmd(txt))
        
    def input(self,txt):
        self.write(txt + "\r\n")
        
    def close(self):
        self.cnx.close()
        
    def login(self):
        print('Login to user %s ...'%self.user)
        self.cnx.expect([cmd("Username: ")],1)
        self.input(self.user)

        self.cnx.expect([cmd("Password:")],1)
        self.input(self.password)
        print('   Logged')
        #self.write('SET TERMINAL/DEVICE=VT500')

    def set_terminal(self):
        self.write('set teminal/inquire')
    
    def reset_timer(self):
        self.timer          = datetime.datetime.now()
        
    def get_current_str_time(self):
        return self.timer.strftime("%d/%m/%Y %H:%M:%S")
        
    def get_timeshift(self):
        time_shift          = datetime.datetime.now() - self.timer
        time_shift_seconds  = time_shift.total_seconds()
        return time_shift_seconds
        
    def timed_out(self,timeout):
        time_shift = self.get_timeshift()
        return time_shift > timeout

    def output(self,output):
        self.last_output = output
        print(output)

    def read_all(self,until=None,until_raw=None):
        if until is not None:
            print('SEARCH: ',cmd(until))
            
        self.reset_timer()
        timeout             = 60 # 5s
        print(self.get_current_str_time(),':')
        
        i, found = 0, False
        raw_output = ''
        full_output = b''
        
        while not self.timed_out(timeout) and not found:
            #l = self.cnx.read_until(b'\n')
            raw_output = self.cnx.read_very_eager()
            if raw_output == b'':
                i += 1
                continue
            
            if until is not None and cmd(until) in raw_output:
                found = True
            if until_raw is not None and until_raw in raw_output:
                found = True
                
            try:
                output = raw_output.decode('ascii')
                self.output(output)
            except:
                #print('ERROR decoding:',raw_output)
                output = test_decode(raw_output)
                output = raw_output
                self.output(output)
                
            
            full_output += raw_output
            
            #print(self.get_current_str_time(),':',i,output)
            
            i += 1
            
            """
            if raw_output == b'':
                print(i,'end')
                #return 
            

                
            if output != '':
                print(i,output)
            i += 1"""

        #print(full_output.decode('ascii'))
        print(self.get_timeshift(),'s limit end')

        return found
        
class WS(VMS):

    def __init__(self):
        VMS.__init__(self)

        #self.read()       
        
        print('    STARTED')
        #self.cnx.expect([cmd("WSM>")],1)
        self.read_all(until='WSM>')
        self.input("ou")
        self.input("isrun isswriter")
        
        notFound = self.read_all(until='Process non trouv')
        if notFound:
            self.input("set def isslive")
            self.input("ou")
            apfFolder = self.read_all(until='APF')

            if apfFolder:
                self.input("Sd start_writer.COM*")

                startWriterFound = self.read_all(until='START_WRITER.COM')

                if startWriterFound:
                    self.input("@start_writer")

                    writerStarted = self.read_all(until="identification")
            
        #self.read_all(until='WSM>')
        #self.cnx.interact()
        exit()
        self.cnx.interact()

        
        #vms.interact()

        exit()
        #self.go_to("WSISS25")
        
        print('Connecting to ws ...')
        self.input("ws")
        self.read_all()
        
        #self.input("0")
        #self.input("0")
        
ws      = WS()
#ws.input("CALCOMETS")
#ws.input("CALCOMETS")
#ws.go_to("USER")

print('yy')
ws.read_all()

l = ws.cnx.read_lazy()
print(l)

ws.close()
exit()


crv025.close()
exit()

crv025.write("\r")
crv025.input("ws")
crv025.go_to('SELECTION:')
crv025.input("0")
crv025.input("0")

l = crv025.read()

crv025.close()

#tn.write(user)
#tn.write(password)

print(l)

print('END')