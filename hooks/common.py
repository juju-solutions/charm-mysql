# vim: syntax=python

import os
import MySQLdb
import subprocess
import shutil
from charmhelpers.core import hookenv, host
from charmhelpers.core.templating import render


def get_service_user_file(service):
    return '/var/lib/mysql/%s.service_user2' % service


def get_service_user(service):
    if service == '':
        return (None, None)
    sfile = get_service_user_file(service)
    if os.path.exists(sfile):
        with open(sfile, 'r') as f:
            return (f.readline().strip(), f.readline().strip())
    (suser, service_password) = \
        subprocess.check_output(['pwgen', '-N 2', '15']).strip().split("\n")
    with open(sfile, 'w') as f:
        f.write("%s\n" % suser)
        f.write("%s\n" % service_password)
        f.flush()
    return (suser, service_password)


def cleanup_service_user(service):
    os.unlink(get_service_user_file(service))


relation_id = os.environ.get('JUJU_RELATION_ID')
change_unit = os.environ.get('JUJU_REMOTE_UNIT')

# We'll name the database the same as the service.
database_name_file = '.%s_database_name' % (relation_id)
# change_unit will be None on broken hooks
database_name = ''
if change_unit:
    database_name, _ = change_unit.split("/")
    with open(database_name_file, 'w') as dbnf:
        dbnf.write("%s\n" % database_name)
        dbnf.flush()
elif os.path.exists(database_name_file):
    with open(database_name_file, 'r') as dbname:
        database_name = dbname.readline().strip()
else:
    print 'No established database and no REMOTE_UNIT.'
# A user per service unit so we can deny access quickly
user, service_password = get_service_user(database_name)
connection = None
lastrun_path = '/var/lib/juju/%s.%s.lastrun' % (database_name, user)
slave_configured_path = '/var/lib/juju.slave.configured.for.%s' % database_name
slave_configured = os.path.exists(slave_configured_path)
slave = os.path.exists('/var/lib/juju/i.am.a.slave')
broken_path = '/var/lib/juju/%s.mysql.broken' % database_name
broken = os.path.exists(broken_path)


def get_mysql_root_passwd():
    return open("/var/lib/mysql/mysql.passwd").read().strip()


def get_db_cursor():
    # Connect to mysql
    passwd = get_mysql_root_passwd()
    connection = MySQLdb.connect(user="root", host="localhost", passwd=passwd)
    return connection.cursor()


def database_exists(db_name):
    cursor = get_db_cursor()
    try:
        cursor.execute("SHOW DATABASES")
        databases = [i[0] for i in cursor.fetchall()]
    finally:
        cursor.close()
    return db_name in databases


def create_database(db_name):
    cursor = get_db_cursor()
    try:
        cursor.execute("CREATE DATABASE {}".format(db_name))
    finally:
        cursor.close()


def grant_exists(db_name, db_user, remote_ip):
    cursor = get_db_cursor()
    priv_string = "GRANT ALL PRIVILEGES ON `{}`.* " \
                  "TO '{}'@'{}'".format(db_name, db_user, remote_ip)
    try:
        cursor.execute("SHOW GRANTS for '{}'@'{}'".format(db_user,
                                                          remote_ip))
        grants = [i[0] for i in cursor.fetchall()]
    except MySQLdb.OperationalError:
        print "No grants found"
        return False
    finally:
        cursor.close()
    return priv_string in grants


def create_grant(db_name, db_user,
                 remote_ip, password):
    cursor = get_db_cursor()
    try:
        cursor.execute("GRANT ALL PRIVILEGES ON {}.* TO '{}'@'{}' "
                       "IDENTIFIED BY '{}'".format(db_name,
                                                   db_user,
                                                   remote_ip,
                                                   password))
    finally:
        cursor.close()


def cleanup_grant(db_user,
                  remote_ip):
    cursor = get_db_cursor()
    try:
        cursor.execute("DROP FROM mysql.user WHERE user='{}' "
                       "AND HOST='{}'".format(db_user,
                                              remote_ip))
    finally:
        cursor.close()


def migrate_to_mount(new_path):
    """Invoked when new mountpoint appears. This function safely migrates
    MySQL data from local disk to persistent storage (only if needed)
    """
    old_path = '/var/lib/mysql'
    if os.path.islink(old_path):
        hookenv.log('{} is already a symlink, skipping migration'.format(
            old_path))
        return True
    os.chmod(new_path, 0700)
    if os.path.isdir('/etc/apparmor.d/local'):
        render('apparmor.j2', '/etc/apparmor.d/local/usr.sbin.mysqld',
               context={'path': os.path.join(new_path, '')})
        host.service_reload('apparmor')
    host.service_stop('mysql')
    host.rsync(os.path.join(old_path, ''),  # Ensure we have trailing slashes
               os.path.join(new_path, ''),
               options=['--archive'])
    shutil.rmtree(old_path)
    os.symlink(new_path, old_path)
    host.service_start('mysql')
