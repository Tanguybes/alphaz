import argparse, os, sys

# redifine path
sys.path.append('../')
#paths       = [x for x in sys.path if not 'alphaz' in x]
#sys.path    = paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.getcwd())

from alphaz.libs import test_lib, py_lib, files_lib, nav_lib
from alphaz.utils.selectionMenu import SelectionMenu
from alphaz.libs import test_lib, py_lib, files_lib, nav_lib
from alphaz.config.config import AlphaConfig

from core import core
api = core.api

GOLLIATH_MENU_PARAMETERS = {
    "selections": [
        {'header':"TESTS"},
        {   
            'name':'all_tests',
            'description':"All tests mode",
            "selections": ['execute','save'],
            "after": {
                "function":{
                    'method':test_lib.operate_all_tests_auto,
                    'kwargs':{
                        'directory':core.config.get(['tests','auto_directory']),
                        "import_path": core.config.get(['tests','auto_import']),
                        'output':True,
                        'verbose':True,
                        'action':"{{selected}}",
                        "log": core.log
                    }
                }
            }
        },
    ]                 
}

if __name__ == "__main__":
    #test_lib.save_all_tests_auto('tests/auto',output=True,verbose=False,refresh=True,name='api')
    #test_lib.execute_all_tests_auto('tests/auto',output=True,verbose=False,refresh=True,name='api')
    #exit()

    parser          = argparse.ArgumentParser(description='Alpha')
    parser.add_argument('--configuration', '-c', help='Set configuration')
    parser.add_argument('--prod','-p',action='store_true')

    args            = parser.parse_args()

    #os.chdir(os.path.dirname(__file__))
    
    #api.init(config_path='api',configuration=args.configuration)

    test_lib.operate_all_tests_auto(
        directory   = core.config.get(['tests','auto_directory']), 
        import_path = core.config.get(['tests','auto_import']),
        output      = True,
        verbose     = True,
        action      = 'execute',
        log         = core.log
        )
    exit()

    m                       = SelectionMenu("Alpha",GOLLIATH_MENU_PARAMETERS,save_directory= core.config.get(["menus","save_directory"]))
    m.run()

    os.chdir(current_folder)  

    """if args.stitch:
        from stitch import Stitch
        prog = Stitch('Test')
        prog.set_driver('firefox')
        prog.process('init')"""