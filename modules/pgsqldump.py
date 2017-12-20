import socket
import os
import subprocess
import sys

def log(*args, **kwargs):
    print("[%s]"% __name__.split(".")[-1],*args,**kwargs)

def _get_path(remote,timemode):
    if 'host' not in remote:
        log("error no host in remote", file=sys.stderr)
        return None
    if 'path' not in remote:
        log("error no path in remote", file=sys.stderr)
        return None
    if 'type' not in timemode:
        log("error no time type", file=sys.stderr)
        return None

    if timemode['type'] != "full":
        log("error time type '%s' not supported" % timemode['type'], file=sys.stderr)
        return None
    return [os.path.join(remote['path'], socket.gethostname(), 'pgsql',timemode['type']), "dumpall.sql.gz"]

def _valid_folder(host,path):
    cmd = ["ssh", host, "mkdir -p %s" % path]
    result = 1
    try:
        cmdrun = subprocess.Popen(cmd)
        cmdrun.wait(300)
        result = cmdrun.returncode
    except subprocess.TimeoutExpired:
        log("timeout create folder on '%s' at '%s'" % (host,path), file=sys.stderr)
        return False
    if result != 0:
        log("error create folder on '%s' at '%s'" % (host,path), file=sys.stderr)
        return False
    return True


def backup(remote, timemode, params):
    log("backup")
    if 'time' in params:
        timemode = params['time']
    path,filename = _get_path(remote,timemode)
    _valid_folder(remote['host'],path)
    full_path = os.path.join(path,filename)
    log("%s to %s" % (remote['host'],full_path))

    result = 1
    try:
        cmd = ["pg_dumpall"]
        if 'user' in params:
            cmd.append("-U")
            cmd.append(params['user'])
        if 'host' in params:
            cmd.append("-h")
            cmd.append(params['host'])
        getdata = subprocess.Popen(cmd,stdout = subprocess.PIPE)
        compress = subprocess.Popen(['gzip', '-9'],  stdin = getdata.stdout, stdout = subprocess.PIPE)
        cmdrun = subprocess.Popen(["ssh", remote['host'], "cat > %s" % full_path], stdin = compress.stdout, stdout = subprocess.PIPE)
        cmdrun.wait(1800)
        result = cmdrun.returncode
    except subprocess.TimeoutExpired:
        log("timeout during backup to '%s'" % (full_path), file=sys.stderr)
    if result != 0:
        log("error during backup to '%s'" % (full_path), file=sys.stderr)

def restore(remote,timemode, params,time):
    log("no restore of pgsqldump possible", file=sys.stderr)
