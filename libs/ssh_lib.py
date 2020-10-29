import paramiko, encodings, scp, re
from typing import List

from ..models.main import AlphaFile
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

    def list_files(self,directory:str) -> List[AlphaFile]:
        """[summary]

        Args:
            directory (str): [description]

        Returns:
            List[AlphaFile]: [description]
        """
        output = self.execute_cmd('ls -l %s'%directory)
        files = io_lib.get_list_file(output)
        return files

    def list_files_names(self,directory:str,pattern:str=None) -> List[str]:
        cmd = 'ls -l -f %s'%directory
        output = self.execute_cmd(cmd)
        lines = str(output).split('\\r\\n')
        if pattern is not None:
            """filtered = []
            for line in lines:
                matchs = re.findall(pattern,line)
                if matchs:
                    filtered.append(line)
            lines = filtered"""
            lines = [x for x in lines if len(re.findall(pattern,x)) != 0]
        return [ x for x in lines if x.replace('.','') != '']

    def list_directories(self,directory:str) -> List[AlphaFile]:
        """[summary]

        Args:
            directory (str): [description]

        Returns:
            List[AlphaFile]: [description]
        """
        output = self.execute_cmd('ls -l %s'%directory)
        directories = io_lib.get_list_file(output)
        return directories

    def list_directories_names(self,directory:str) -> List[str]:
        output = self.execute_cmd('ls -l -f %s'%directory)
        lines = str(output).split('\\r\\n')
        return [ x for x in lines if x.replace('.','') != '']

    def get_file_content(self,filepath:str,decode=False):
        output = self.execute_cmd('cat %s'%filepath,decode=decode)
        return output

    def execute_cmd(self,cmd,decode=True):
        inputs, output, err = '', '', ''
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(cmd, get_pty=True)
        output = ssh_stdout.read()
        if decode:
            output = output.decode('utf-8').encode('ascii')
            output = str(output)
            if output[:2] == "b'":
                output = output[2:-1]
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
            if inputs != '' and self.log:    self.log.info('inputs:',inputs)
            if err != '' and self.log:       self.log.error('err:',err)
        return output
