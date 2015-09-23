#!/usr/bin/python

import amulet

from charmhelpers.contrib.openstack.amulet.deployment import (
    OpenStackAmuletDeployment
)

from charmhelpers.contrib.openstack.amulet.utils import (
    OpenStackAmuletUtils,
    DEBUG,
    # ERROR
)

# Use DEBUG to turn on debug logging
u = OpenStackAmuletUtils(DEBUG)


class MySQLBasicDeployment(OpenStackAmuletDeployment):
    """Amulet tests on a basic MySQL deployment."""

    def __init__(self, series=None, openstack=None, source=None,
                 git=False, stable=True):
        """Deploy the test environment."""
        super(MySQLBasicDeployment, self).__init__(series, openstack,
                                                   source, stable)
        self.git = git
        self._add_services()
        self._add_relations()
        self._configure_services()
        self._deploy()
        self._initialize_tests()

    def _add_services(self):
        """Add services

           Add the services that we're testing, where MySQL is local,
           and the rest of the service are from lp branches that are
           compatible with the local charm (e.g. stable or next).
           """
        this_service = {'name': 'mysql'}
        other_services = [{'name': 'keystone'}]
        super(MySQLBasicDeployment, self)._add_services(this_service,
                                                        other_services)
        self.d.expose('keystone')
        self.d.expose('mysql')

    def _add_relations(self):
        """Add all of the relations for the services."""
        relations = {'mysql:shared-db': 'keystone:shared-db'}
        super(MySQLBasicDeployment, self)._add_relations(relations)

    def _configure_services(self):
        """Configure all of the services."""

        mysql_config = {}
        keystone_config = {'admin-password': 'openstack',
                           'admin-token': 'ubuntutesting'}

        configs = {'mysql': mysql_config,
                   'keystone': keystone_config}
        super(MySQLBasicDeployment, self)._configure_services(configs)

    def _initialize_tests(self):
        """Perform final initialization before tests get run."""
        # Access the sentries for inspecting service units
        self.mysql_sentry = self.d.sentry['mysql'][0]
        self.keystone_sentry = self.d.sentry['keystone'][0]

        self.keystone_sentry.run('open-port 5000')
        self.keystone_sentry.run('open-port 35357')
        self.keystone_sentry.run('open-port 8888')
        self.keystone_sentry.run('open-port 35347')
        self.keystone_sentry.run('open-port 4990')
        self.mysql_sentry.run('open-port 3306')
        # Authenticate keystone admin
        self.keystone = u.authenticate_keystone_admin(self.keystone_sentry,
                                                      user='admin',
                                                      password='openstack',
                                                      tenant='admin')

    def test_100_services(self):
        """Verify the expected services are running on the corresponding
           service units."""
        services = {
            self.mysql_sentry: ['mysql'],
            self.keystone_sentry: ['keystone']
        }
        ret = u.validate_services_by_name(services)
        if ret:
            amulet.raise_status(amulet.FAIL, msg=ret)

    def test_120_mysql_keystone_database_query(self):
        """Verify that the user table in the keystone mysql database
           contains an admin user with a specific email address."""

        cmd = ("export FOO=$(sudo cat /var/lib/mysql/mysql.passwd);"
               "mysql -u root -p$FOO -e "
               "\"SELECT extra FROM keystone.user WHERE name='admin';\"")

        output, retcode = self.mysql_sentry.run(cmd)
        u.log.debug('command: `{}` returned {}'.format(cmd, retcode))
        u.log.debug('output:\n{}'.format(output))

        if retcode:
            msg = 'command `{}` returned {}'.format(cmd, str(retcode))
            amulet.raise_status(amulet.FAIL, msg=msg)

        if 'juju@localhost' not in output:
            msg = ('keystone mysql database query produced '
                   'unexpected data:\n{}'.format(output))
            amulet.raise_status(amulet.FAIL, msg=msg)

    def test_150_mysql_shared_db_relation(self):
        """Verify the mysql shared-db relation data"""
        unit = self.mysql_sentry
        relation = ['shared-db', 'keystone:shared-db']
        expected_data = {
            'allowed_units': self.keystone_sentry.info['unit_name'],
            'private-address': u.valid_ip,
            'password': u.not_null,
            'db_host': u.valid_ip
        }
        ret = u.validate_relation_data(unit, relation, expected_data)
        if ret:
            message = u.relation_error('mysql shared-db', ret)
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_200_mysql_default_config(self):
        """Verify some important confg data in the mysql config file's
           mysqld section."""
        unit = self.mysql_sentry
        conf = '/etc/mysql/my.cnf'
        expected = {
            'user': 'mysql',
            'socket': '/var/run/mysqld/mysqld.sock',
            'port': '3306',
            'basedir': '/usr',
            'datadir': '/var/lib/mysql',
            'myisam-recover': 'BACKUP',
            'query_cache_size': '0',
            'query_cache_type': '0',
            'tmpdir': '/tmp',
            'bind-address': '0.0.0.0',
            'log_error': '/var/log/mysql/error.log',
            'character-set-server': 'utf8'
        }
        section = 'mysqld'

        ret = u.validate_config_data(unit, conf, section, expected)
        if ret:
            message = 'mysql config error: {}'.format(ret)
            amulet.raise_status(amulet.FAIL, msg=message)

    def test_900_restart_on_config_change(self):
        """Verify that mysql is restarted when the config is changed."""
        sentry = self.mysql_sentry
        service = 'mysql'

        # Expected default and alternate value
        set_default = {'dataset-size': '80%'}
        set_alternate = {'dataset-size': '50%'}

        # Config file affected by juju set config change
        conf_file = '/etc/mysql/my.cnf'

        # Make config change, check for service restarts
        u.log.debug('Making config change on {}...'.format(service))
        self.d.configure(service, set_alternate)

        u.log.debug('Checking that the service restarted: {}'.format(service))
        if not u.service_restarted(sentry, service, conf_file, sleep_time=30):
            self.d.configure(service, set_default)
            msg = 'svc {} did not restart after config change'.format(service)
            amulet.raise_status(amulet.FAIL, msg=msg)

        self.d.configure(service, set_default)
