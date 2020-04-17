import argparse, os, sys

sys.path.append(os.getcwd())

parser = argparse.ArgumentParser(prog='Golliath', description='Alpha', epilog='Alpha')

parser.add_argument('--mobba', '-m', action='store_true', help='Full mode')
parser.add_argument('--stitch', '-st', action='store_true', help='Full mode')
parser.add_argument('--groups', '-g', help='Groups', nargs='+')

args            = parser.parse_args()

if args.stitch:
    from stitch import Stitch
    prog = Stitch('Test')
    prog.set_driver('firefox')
    prog.process('init')

    