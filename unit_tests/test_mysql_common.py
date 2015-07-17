import mock
import unittest
import sys

sys.modules['MySQLdb'] = mock.Mock()

# NOTE(beisner): unit tests should not attempt to actually apt-get install
# anything.  By importing common here, __init__ tries to apt-get install
# things, assuming sudo privs.  CI tests are not run with sudo (expect
# this to fail).
import common  # noqa


class CommonTests(unittest.TestCase):

    @mock.patch.object(common, 'MySQLHelper', spec=common.MySQLHelper)
    def test_get_db_helper(self, mock_helper):
        common.get_db_helper()
        kwargs = {'rpasswdf_template': '/var/lib/mysql/mysql.passwd',
                  'upasswdf_template': '/var/lib/mysql/mysql-{}.passwd',
                  'delete_ondisk_passwd_file': False}
        mock_helper.assert_called_with(**kwargs)
