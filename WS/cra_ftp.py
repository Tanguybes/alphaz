from ftplib import FTP
from io import BytesIO 
import datetime, collections

from Libs import ftp_lib, scp_lib
import scp

file_path   = "C:\Git\alpha\WS\CRA002_MON_SEQBLK.BIN;9010"

if False:
    hostname    = "cr2sx20140.cr2.st.com"
    username    = "elkusr"
    password    = "62A!!1ance2018"
    port        = 22
    """
    hostname    = "srv-apf.cr2.st.com"
    username    = "apf"
    password    = "apf"
    port        = 22
    """
    source = file_path
    target = '/data/elk/workstream_dbms_logs/from_ws/test.BIN'

    import paramiko
    scp_lib.scp_to_server(file_path,host=hostname, username=username,password=password)
    exit()

    connect     = FTP("cr2sx20140.cr2.st.com","elkusr","62A!!ance2018")
    print(connect.pwd())
    exit()

    ftp = ftp_lib.AlphaFtp(host="cr2sx20140.cr2.st.com",user="elkusr",password="62A!!1ance2018")
    valid = ftp.test_cnx()
    print(valid)

    if valid:
        files = ftp.list_dir('/data/elk/workstream_dbms_logs/from_ws')
        print(files)
    exit()

d           = datetime.date.today()

prod        = True

host        = "crv025.cro.st.com" if not prod else "cra003.cro.st.com"
user        = "wsm" # votre identifiant

month       = str(d.month)[-2:]
month       = month if len(month) == 2 else "0"+month
password    = "hobbit%s%s"%(month,str(d.year)[-2:])

path        = 'HISTODB1:[TEMP.SEQBLK]'
paths        = ['BACKUPDB1:[CROLLES.backup1]','BACKUPDB1:[CROLLES.backup2]']
ftp         = ftp_lib.AlphaFtp(host=host,user=user,password=password,sftp=True)
valid       = ftp.test_cnx()

most_recent = None
most_recent_time = None
if valid:
    for path in paths:
        files = ftp.list_dir(path)
        for file in files:
            print(file.filename,file.st_mtime)
            if most_recent_time is None or most_recent_time < file.st_mtime:
                most_recent_time = file.st_mtime
                most_recent      = path

print(most_recent, most_recent_time)

exit()

connect     = FTP(host,user,password) # on se connecte

print(connect.pwd())

# BDD CROLLES
connect.cwd('HISTODB1:[TEMP.SEQBLK]')
dirs    = connect.nlst()

print(connect.pwd())

files_per_node, file_per_node = {}, {}

for path in dirs:
    if 'MON_SEQBLK.BIN;' in path:
        #print(path)
        node    = path.split('_MON_SEQBLK')[0]
        version = path.split('MON_SEQBLK.BIN;')[1]

        if not node in files_per_node:
            files_per_node[node] = {}

        files_per_node[node][version] = path


for node, files in files_per_node.items():
    od                  = collections.OrderedDict(sorted(files.items(),reverse=True))
    file_per_node[node] = od[list(od.keys())[-1]]

    #flocal = BytesIO()
    flocal  =  open('tmp.BIN','wb')
    connect.retrbinary('RETR ' + file_per_node[node], flocal.write)

#print(dirs)

connect.quit()