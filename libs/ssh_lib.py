import paramiko, encodings, scp
from .string_lib import universal_decode
#class SshLog(SSHClient):

class AlphaSsh():
    server = None
    username = None
    password = None
    ssh = None

    def __init__(self,server, username, password,log=None,keys=True):
        self.server = server
        self.username = username
        self.password = password
        self.log = log

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if keys:
            self.ssh.connect(self.server, username=self.username, password=self.password)
        else:
            self.ssh.connect(self.server, username=self.username, password=self.password, look_for_keys=False)
        self.scp = scp.SCPClient(self.ssh.get_transport())

    def disconnect(self):
        """Close ssh connection."""
        self.ssh.close()
        self.scp.close()  # Coming later

    def test(self):
        return True

    def wait(self):
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command('')
        while not ssh_stdout.channel.exit_status_ready():
            pass

    def execute_cmd(self,cmd,decode=True):
        inputs, output, err = '', '', ''
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd)

        while not ssh_stdout.channel.exit_status_ready():
            #Print data whena available
            if ssh_stdout.channel.recv_ready():
                alldata =  ssh_stdout.channel.recv(1024)
                prevdata = b"1"
                while prevdata:
                        prevdata = ssh_stdout.channel.recv(1024)
                        alldata += prevdata
                output += str(alldata)

        """if ssh_stdin.readable():
            try:
                inputs = ssh_stdin.read()
                pass
            except Exception as ex:
                print('Error:',ex)
        if ssh_stdout.readable():
            try:
                output = ssh_stdout.read()
                #print('2',output)
            except Exception as ex:
                print('Error:',ex)
        if ssh_stderr.readable():
            try:
                err = ssh_stderr.read()
                pass
            except Exception as ex:
                print('Error:',ex)"""

        if decode:
            inputs, output, err = universal_decode(inputs), universal_decode(output), universal_decode(err)
            if inputs != '':    print('i:',inputs)
            if err != '':       print('err:',err)
        return output

    def execute_cmd_interactive(self,cmd,decode=True):
        inputs, output, err = '', '', ''
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd)

        i, limit = 0,100
        while not ssh_stdout.channel.exit_status_ready() and i < limit:
            #Print data whena available
            if ssh_stdout.channel.recv_ready():
                alldata =  ssh_stdout.channel.recv(1024)
                prevdata = b"1"
                while prevdata:
                        prevdata = ssh_stdout.channel.recv(1024)
                        alldata += prevdata
                output += str(alldata)
            i += 1

        if decode:
            inputs, output, err = universal_decode(inputs), universal_decode(output), universal_decode(err)
            if inputs != '':    print('i:',inputs)
            if err != '':       print('err:',err)
        return output
