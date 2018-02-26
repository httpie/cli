import sys

def has_branched(function_name,  id):
    with open(function_name + '.txt', 'a') as f:
        f.write(str(id) + '\n')

def write_info(function_name, total_branches):
    with open(function_name + '.txt', 'a') as f:
        f.write(total_branches + '\n')
