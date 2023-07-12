"""Copyright 2023 Alexey Rebrikov
rebrikov-av@phystech.com
"""
import os
import argparse

from app.source.set_manager import SetManager

actions = [
    'create',
    'generate',
    'recognize',
    'grade'
    ]

if __name__ == '__main__':
    sm = SetManager(f'{os.getcwd()}/sets/')
    ap = argparse.ArgumentParser()
    ap.add_argument("-m", 
                    metavar='mode', 
                    choices=actions, 
                    required=True,
                    help=f'one of {actions} modes')
    ap.add_argument("-s", 
                    metavar='set', 
                    type=str, 
                    required=True,
                    help=f'problem set name at dir ./sets/')
    args = vars(ap.parse_args())
    print(args)

    
    if args['m'] == 'create':
        sm.create_set(args['s'])
    elif args['m'] == 'generate':
        sm.generate_set(args['s'])
    elif args['m'] == 'recognize':
        sm.get_answers(args['s'])
    elif args['m'] == 'grade':
        sm.get_results(args['s'])
   