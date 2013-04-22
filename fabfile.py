from fabric.api import run, env, put

env.user = 'ubuntu'

def find_libra():
    run('sudo  ps -aux | grep libra')

def find_haproxy():
    run('sudo ps -aux | grep haproxy')

def stop_libra_worker():
    run('sudo killall libra_worker', pty=True)

def start_libra_worker():
    run('sudo libra_worker -c /etc/libra.cfg', pty=True)

