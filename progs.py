import argparse, os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Golliath', description='Golliath - Calculate bricks', epilog='Golliath')
    parser.add_argument('--prog', '-p', help='Prod mode')

    args                    = parser.parse_args()

    prog = args.prog

    if prog is None:
        print('You have to specify a program')
    elif prog = 'fdt':
        pass