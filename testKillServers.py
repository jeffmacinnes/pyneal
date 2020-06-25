import subprocess
import re 

pattern = '(?<=Python  )[0-9]*'

def killServers():
    ports = ['5557', '5556', '5555']

    for p in ports:
        print('port: {}'.format(p))
        try:
            # get list of all PIDs bound to this port
            results = subprocess.run([
                'lsof',
                '-i',
                ':{}'.format(p),
            ], stdout=subprocess.PIPE).stdout.decode('utf-8')


            # check if 'LISTEN' in any of the PIDs
            for l in results.split('\n'):
                if l.find('(LISTEN)') != -1:
                    pid = re.search(pattern, l)
                    print('port {} using PID {}'.format(p, pid.group()))    
        except:
            pass

if __name__ == '__main__':
    killServers()
# Python  88638 jeff  20u  IPv4 0x9031a52d278acb17      0t0  TCP localhost:personal-agent (LISTEN)