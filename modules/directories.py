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
    return os.path.join(remote['path'], socket.gethostname(), 'directories',timemode['type'])

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

def sync(src,dest):
    cmd = ["rsync","-a" , "--delete","--numeric-ids",  src,dest]
    result = 1
    try:
        cmdrun = subprocess.Popen(cmd)
        cmdrun.wait(1800)
        result = cmdrun.returncode
    except subprocess.TimeoutExpired:
        log("timeout during sync '%s' to '%s'" % (src,dest), file=sys.stderr)
        return False
    if result != 0:
        log("error during sync  '%s' to '%s'" % (src,dest), file=sys.stderr)
        return False
    return True


def backup(dest, timemode, params):
    log("backup")
    if 'time' in params:
        timemode = params['time']
    path = _get_path(dest,timemode)
    for src in params:
        if src != "time":
            src = "%s/"% src
            path_src = src
            if path_src[0] == "/":
                path_src = path_src[1:]
            path_src = os.path.join(path,path_src)
            _valid_folder(dest['host'],path_src)
            remote_path = "%s:%s" % (dest['host'],path_src)
            log("%s to %s" % (src,remote_path))
            sync(src,remote_path)

def restore(src,timemode, params,time):
    log("restore backup from %s" % time)
    if 'time' in params:
        timemode = params['time']
    path = _get_path(src,timemode)
    _valid_folder(src['host'],path)
    for dest in params:
        if dest != "time":
            path_dest = "%s/"% dest
            if path_dest[0] == "/":
                path_dest = path_dest[1:]
            path_dest = os.path.join(path,path_dest)
            remote_path = "%s:%s" % (src['host'],path_dest)
            log("%s to %s" % (remote_path,dest))
            sync(remote_path,dest)
