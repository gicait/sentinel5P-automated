scripts = ["query.py", "process.py", "multitemporal.py"]

for script in scripts:
    print(f'executing {script}')
    try:
        script_code = open(script, 'r', encoding='utf-8').read()
        exec(script_code)
        print(f'{script} successfully executed')
    except FileNotFoundError:
        print(f"{script} not found.")
    except Exception as error:
        print(f"Error executing {script}: {error}")
