import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='Golliath', description='Alpha', epilog='Alpha')

    parser.add_argument('--mobba', '-m', action='store_true', help='Full mode')
    parser.add_argument('--groups', '-g', help='Groups', nargs='+')

    args            = parser.parse_args()

    if args.mobba:
        from main import mobba
        mobba()

    