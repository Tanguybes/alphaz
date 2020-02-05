#!flask/bin/python
from flask import Flask
import os, signal, argparse, configparser

alpha_api = Flask(__name__)

@alpha_api.route('/')
def index():
    return "Hello, World!"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Golliath', description='Golliath - Calculate bricks', epilog='Golliath')
    parser.add_argument('--prod', '-p', action='store_true', help='Prod mode')
    parser.add_argument('--debug', '-d', action='store_true', help='Debug mode')
    parser.add_argument('--test', '-t', action='store_true', help='Test mode')
    parser.add_argument('--start', '-s', action='store_true', help='Start api')
    parser.add_argument('--stop', '-k', action='store_true', help='Stop api')

    CONFIG_FILE_PATH = 'api.ini'
            
    args                    = parser.parse_args()

    config = configparser.ConfigParser()

    if args.start:
        pid = os.getpid()

        config['MAIN'] = {'process': pid}
        
        with open(CONFIG_FILE_PATH,'w') as f:
            config.write(f)

        alpha_api.run(debug=True)

    if args.stop:
        config.read(CONFIG_FILE_PATH)

        pid = config['MAIN']['process']
        pid = int(pid)

        os.kill(pid, 9)

        print('Process n°%s killed'%pid)