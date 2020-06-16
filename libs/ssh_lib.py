import paramiko, encodings

black_list = ['cp037','utf_16_be','cp1252','hz','ascii','utf_32','cp500','cp1140','gb2312',
'euc_jis_2004','cp865','ptcp154','cp860','cp437','koi8_r','cp1256','cp863','cp1125','gbk','iso8859_11',
'mac_iceland','mac_latin2','iso8859_8','iso2022_jp_ext','mac_greek','big5hkscs','cp949','cp866','mac_turkish',
'iso2022_jp_2','mac_roman','cp1250','cp950','kz1048','shift_jisx0213','cp1258','cp1253','big5','cp932',
'cp852','quopri_codec','bz2_codec','iso2022_jp_1','euc_kr','cp862','cp858','cp861','tis_620','cp869',
'cp855','shift_jis_2004','cp775','cp1026','zlib_codec', 'utf_16','cp1254','iso8859_7','cp850','iso8859_6',
'shift_jis','utf_16_le','utf_32_be','mac_cyrillic','cp273','mbcs','uu_codec','utf_32_le','cp1251','iso2022_kr',
'cp857']

def universal_decode(txt,blacklist=[]):
    encodings_methods = list(set(encodings.aliases.aliases.values()))
    
    result, decoded = txt, False
    for encoding_method in encodings_methods:
        if encoding_method not in blacklist:
            try:
                result = txt.decode(encoding_method)
                decoded = True
            except:
                pass
            if decoded:
                return result
    return result

class AlphaSsh():
    server = None
    username = None
    password = None
    ssh = None

    def __init__(self,server, username, password,log=None):
        self.server = server
        self.username = username
        self.password = password
        self.log = log

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.server, username=self.username, password=self.password)

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
            if inputs != '':print('i:',inputs)
            if err != '':print('err:',err)
        return output

