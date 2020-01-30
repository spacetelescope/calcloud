import json
import subprocess
import sys
import time

def lambda_handler(event, context):
    print(f'Received event: {json.dumps(event, indent = 4)}')

    print('Calling process.py')
    proc = subprocess.Popen(['python process.py'], shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    while proc.poll() is None:
        time.sleep(0.1)
        print(proc.stdout.read())
    print(proc.returncode)
