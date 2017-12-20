import socket
import os
import subprocess
import sys

#max_wal_senders = 1
#archive_mode = on
#archive_command = 'test ! -f /var/lib/postgres/archive/%f && cp %p /var/lib/postgres/archive/%f'
#wal_level = hot_standby
#wal_level = replica

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
    return [os.path.join(remote['path'], socket.gethostname(), 'pgsql',timemode['type']), "data.tar.gz"]

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
        cmd = ["pg_basebackup"]
        if 'user' in params:
            cmd.append("-U")
            cmd.append(params['user'])
        if 'host' in params:
            cmd.append("-h")
            cmd.append(params['host'])
        cmd.append("--xlog")
        cmd.append("-D")
        cmd.append("-")
        cmd.append("-Ft")
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
    log("restore backup from %s" % time)
    cmd = ["psql"]
    if 'user' in params:
        cmd.append("-U")
        cmd.append(params['user'])
    if 'host' in params:
        cmd.append("-h")
        cmd.append(params['host'])
    cmd.append("--tuples-only")
    cmd.append("-P")
    cmd.append("format=unaligned")
    cmd.append("-c")
    cmd.append("SHOW data_directory;")
    data_path = subprocess.Popen(cmd, stdout=subprocess.PIPE).stdout.read().decode().replace("\n","")
    if len(data_path) <= 1:
        data_path = "/var/lib/postgres/data"
    try:
        subprocess.Popen(["systemctl","stop","postgresql"])
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            subprocess.Popen(["/etc/init.d/postgresql","stop"])
        else:
            log("error during stoping postgresql", file=sys.stderr)
            return false
    log("stopped postgresql")
    path,filename = _get_path(remote,timemode)
    full_path = os.path.join(path,filename)
    result = 1
    log("cleanup '%s'" % data_path)
    subprocess.Popen(["rm","-fR","%s/*" % data_path])
    log("recieve backup to '%s'" % data_path)
    try:
        getdata = subprocess.Popen(["ssh", remote['host'], "cat %s" % full_path], stdout = subprocess.PIPE)
        extract = subprocess.Popen(['tar', 'xz','-C',data_path],  stdin = getdata.stdout, stdout = subprocess.PIPE)
        extract.wait(1800)
        result = extract.returncode
        subprocess.Popen(["chmod","-R","go-rx",data_path])
        subprocess.Popen(["chown","-R","postgres:postgres",data_path])
    except subprocess.TimeoutExpired:
        log("timeout during restore to '%s'" % (full_path), file=sys.stderr)
    if result != 0:
        log("error during restore to '%s'" % (full_path), file=sys.stderr)
    log("start postgresql")
    try:
        subprocess.Popen(["systemctl","start","postgresql"])
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            subprocess.Popen(["/etc/init.d/postgresql","start"])
        else:
            log("error during stoping postgresql", file=sys.stderr)
            return false
