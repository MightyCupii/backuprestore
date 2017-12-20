# backuprestore

Here should be created a little modular backup and restore software.

- It should save files with rsync on another computer (and play back)
- also it should create postgresql dump files (and the possibilty to restore them)

## Installation
```
git clone https://github.com/genofire/backuprestore /opt/backuprestore
ln -s /opt/backuprestore/br-console /usr/local/bin/br-console
ln -s /opt/backuprestore/br-backup /usr/local/bin/br-backup
```
**create cronjob (if systemd-timer did not exists)**

*/etc/cron.d/br-backup* :
```
# create backup after midnight
#
0 5 * * * root br-backup
```
### Configuration
Create Configuration file under
*/etc/backuprestore.conf* :

```
[remote]
host = "genofire@firestore.firenet.sum7.eu"
path = "/tank/genofire/backup/test"

[time]
# timestemp to backup -> current only 'full' supported
type = "full"

[modules]

# directories modul
directories = [ "/tmp/a"]

# a failed modul -> did not exists
notFoundDummy = "nil"

[modules.pgsqldump]
# pgsql dumpall modul
host = "localhost"
user = "postgres"

[modules.pgsqlreplica]
# pgsql replica modul
host = "localhost"
user = "postgres"
```


## Tipps
### Configuration of *postgresql* for the pgsqlreplica modul of backuprestore
Change/uncomment the following lines in the *postgresql.conf*:
```
max_wal_senders = 3
archive_mode = on
wal_level = hot_standby
```

Give the privilegs in *pg_hba.conf* maybe for pgsqlreplica:
```
local   replication     postgres                                trust
```

### Configuration of *postgresql* for the pgsqldump modul of backuprestore
Give the privilegs in *pg_hba.conf* maybe for pgsqldump:
```
local   all             postgres                                trust
```
