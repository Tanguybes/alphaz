import pysftp, ftplib

class AlphaFtp():
    cnx = None
    valid = False
    sftp = False

    def __init__(self,host,user,password=None,port=22,key=None,sftp=False):
        self.cnopts = pysftp.CnOpts()
        self.cnopts.hostkeys = None

        self.host = host
        self.port = port
        self.user = user
        self.key = key
        self.password = password
        self.sftp = sftp
        
        self.test_cnx()

    def get_cnx(self):
        if self.sftp:
            if self.key is None:
                cnx = pysftp.Connection(self.host, port=self.port, username=self.user, password=self.password, cnopts=self.cnopts)
            else:
                cnx = pysftp.Connection(self.host, port=self.port, username=self.user, password=self.password, cnopts=self.cnopts, private_key=self.key)
        else:
            cnx = ftplib.FTP(host=self.host,user=self.user,passwd=self.password)
        return cnx

    def test_cnx(self):
        try:
            with self.get_cnx() as sftp:
                print ("Connection succesfully established ... ")
                self.valid = True
        except Exception as ex:
            print(ex)
            self.valid = False
        return self.valid

    def list_dir(self,directory):
        with self.get_cnx() as sftp:
            # Switch to a remote directory
            sftp.cwd(directory) #'/home/gollnwnw'

            # Obtain structure of the remote directory '/var/www/vhosts'
            if self.sftp:
                directory_structure = sftp.listdir_attr()

                # Print data
                for attr in directory_structure:
                    print (attr.filename, attr)
            else:
                directory_structure = sftp.nlst()

                # Print data
                for attr in directory_structure:
                    print (attr)

            if len(directory_structure) == 0:
                print('No files in directory')
            return directory_structure

    def upload(self,sourcepath,remotepath):
        with self.get_cnx() as sftp:
            sftp.put(sourcepath,remotepath)

    def uploads(self,files_list):
        with self.get_cnx() as sftp:
            for file_dict in files_list:
                sftp.put(file_dict['sourcepath'],file_dict['remotepath'])

    def makedirs(self,remote_directory):
        with self.get_cnx() as sftp:
            sftp.makedirs(remote_directory)