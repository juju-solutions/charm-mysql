#!/usr/bin/python3

import amulet
from charmhelpers.contrib.amulet.deployment import (
    AmuletDeployment
)
import logging
import sys

try:
    import pymysql
except ImportError:
    import pymysql3  # noqa


class MySQLBasicDeployment(AmuletDeployment):
    def __init__(self, series=None):
        self.log = self._get_logger()
        self.max_connections = '30'
        # the default of 80% eats too much resources in a CI environment
        self.dataset_size = '25%'

        self.d = amulet.Deployment(series=series)

        self.d.add('mysql')
        self.d.configure(
            'mysql', {
                        'max-connections': self.max_connections,
                        'dataset-size': self.dataset_size,
                     },
        )
        self.d.expose('mysql')

        try:
            self.d.setup(timeout=900)
            self.d.sentry.wait()
        except amulet.helpers.TimeoutError:
            amulet.raise_status(amulet.SKIP,
                                msg="Environment wasn't stood up in time")

        # Allow connections from outside
        mysqlmaster = self.d.sentry['mysql'][0]
        mysqlmaster.run(
            "echo 'GRANT ALL ON *.* to root@\"%\"'\""
            " IDENTIFIED BY '`cat /var/lib/mysql/mysql.passwd`'\"|"
            "mysql -u root --password=`cat /var/lib/mysql/mysql.passwd`"
        )

    def _get_logger(self, name="deployment-logger", level=logging.DEBUG):
        """Get a logger object that will log to stdout."""
        log = logging
        logger = log.getLogger(name)
        fmt = log.Formatter("%(asctime)s %(funcName)s "
                            "%(levelname)s: %(message)s")

        handler = log.StreamHandler(stream=sys.stdout)
        handler.setLevel(level)
        handler.setFormatter(fmt)

        logger.addHandler(handler)
        logger.setLevel(level)

        return logger

    def test_100_connect(self):
        """Verify that we can connect to the deployed MySQL instance"""
        self.log.info('Verify that we can connect to the deployed MySQL '
                      'instance')
        mysql_server = self.d.sentry['mysql'][0]
        mysql_password = mysql_server.file_contents(
                            '/var/lib/mysql/mysql.passwd')
        try:
            self.mysql_conn = pymysql.connect(
                user='root',
                password=mysql_password,
                host=mysql_server.info['public-address'],
                database='mysql')
        except pymysql.OperationalError:
            amulet.raise_status(amulet.FAIL, msg='Unable to connect to MySQL')
        self.log.info('OK')

    def test_110_check_variables(self):
        """Verify that configured variables are reflected back to us when
        asking MySQL server about them."""
        self.log.info('Verify that configured variables are reflected back to '
                      'us when asking MySQL server about them.')
        cur = self.mysql_conn.cursor()
        cur.execute("SHOW VARIABLES LIKE 'max_connections'")
        for row in cur:
            if row[0] == 'max_connections':
                if row[1] == self.max_connections:
                    self.log.info('OK')
                    return
                else:
                    amulet.raise_status(
                        amulet.FAIL,
                        msg="max_connections='{}', expected '{}'"
                            "".format(row[1], self.max_connections))
        amulet.raise_status(
            amulet.FAIL,
            msg='Unable to retrieve value for max_connections from server')
