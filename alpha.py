import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Golliath', description='Alpha', epilog='Alpha')

    parser.add_argument('--test', '-t', action='store_true', help='Full mode')
    parser.add_argument('--groups', '-g', help='Groups', nargs='+')

    args            = parser.parse_args()

    print(args.test)