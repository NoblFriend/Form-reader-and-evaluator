"""Copyright 2023 Alexey Rebrikov
rebrikov-av@phystech.com
"""
import sys
import os

from app.source.set_manager import SetManager

if __name__ == '__main__':
    sm = SetManager(f'{os.getcwd()}/sets/')
    name = sys.argv[1]
    action = sys.argv[2]
    if action == 'create':
        sm.create_set(name)
    elif action == 'generate':
        sm.generate_set(name)
    elif action == 'recognize':
        sm.get_answers(name)
    elif action == 'grade':
        sm.get_results(name)
    else:
        print(
            f"Invalid action: {action}. Allowed actions: create, get_answers, get_results")
