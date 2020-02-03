import subprocess

proc = subprocess.Popen(
    ['/var/task/hstcal/bin/calacs.e', '--version]'], shell = True,
    stdout = subprocess.PIPE, stderr = subprocess.PIPE
)
(stdout, stderr) = proc.communicate()
print(f'stdout: {stdout}')
