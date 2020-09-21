import paramiko, encodings, scp
from .string_lib import universal_decode
from . import io_lib

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
        self.keys = keys

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        if self.keys:
            self.ssh.connect(self.server, username=self.username, password=self.password)
        else:
            self.ssh.connect(self.server, username=self.username, password=self.password, look_for_keys=False)
        connected = self.test()
        if connected:
            self.scp = scp.SCPClient(self.ssh.get_transport())
        return connected

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.disconnect()

        if exc_type:
            print(f'exc_type: {exc_type}')
            print(f'exc_value: {exc_value}')
            print(f'exc_traceback: {exc_traceback}')

    def disconnect(self):
        """Close ssh connection."""
        if self.test(): 
            self.ssh.close()
        self.scp.close()  # Coming later

    def test(self):
        return self.ssh.get_transport() is not None and self.ssh.get_transport().is_active()

    def wait(self):
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command('')
        while not ssh_stdout.channel.exit_status_ready():
            pass

    def list_files(self,directory):
        output = self.execute_cmd('ls -l %s'%directory)
        files = io_lib.get_list_file(output)
        return files

    def execute_cmd(self,cmd,decode=True):
        inputs, output, err = '', '', ''
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd, get_pty=True)

        return str(ssh_stdout.read())

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
            if inputs != '' and self.log:    self.log.info('inputs:',inputs)
            if err != '' and self.log:       self.log.error('err:',err)
        return output
