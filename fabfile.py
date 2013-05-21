from fabric.api import run, env, put, sudo

env.user = 'ubuntu'

def find_libra():
    run('sudo  ps -aux | grep libra')

def find_haproxy():
    run('sudo ps -aux | grep haproxy')

def stop_libra_worker():
    run('sudo killall libra_worker')

def start_libra_worker():
    run('sudo libra_worker -c /etc/libra.cfg')

def put_file(file, dest):
    put(file, dest) # it's copied into the target directory

def remove_file(file):
    run('rm %s' %file)

