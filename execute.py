import os

# Set working directory
abspath = os.path.abspath(__file__)
dir_name = os.path.dirname(abspath)
os.chdir(dir_name)

# Define list of scripts in the order to be executed in.
scripts = ['query.py', 'process.py', 'multitemporal.py']

# Execute each script in the list
for script in scripts:
    print(f'executing {script}')
    try:
        script_code = open(script, 'r', encoding='utf-8').read()
        exec(script_code)
        print(f'{script} successfully executed')
    except FileNotFoundError:
        print(f'{script} not found.')
    except Exception as error:
        print(f'Error executing {script}: {error}')
