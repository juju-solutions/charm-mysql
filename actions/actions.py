#!/usr/bin/python

import os
import sys
import subprocess
import traceback
import MySQLdb
from contextlib import contextmanager
from time import gmtime, strftime

sys.path.append('hooks')

from charmhelpers.core.hookenv import (
    action_get,
    action_set,
    action_fail,
    leader_set,
    is_leader,
)

from common import (
    get_db_helper,
)

@contextmanager
def open_mysql():
    """ Opens up a new MySQL connection """

    db_helper = get_db_helper()
    password = db_helper.get_mysql_root_password()

    con = MySQLdb.connect(
        host="localhost",
        user="root",
        passwd=password,
    )
    yield con
    con.close()


@contextmanager
def open_mysql_cursor(connection):
    """ Opens up a new MySQL cursor """

    cur = connection.cursor()
    yield cur
    cur.close()


def validate_parameters(params, required_keys):
    for key in required_keys:
        if not params.get(key):
            raise Exception("Missing required parameter: {}".format(key))


def user_exists(connection, username):

    with open_mysql_cursor(connection) as cursor:
        cursor.execute(
            "SELECT count(1) FROM mysql.user WHERE user = %s ;",
            (username, )
        )
        if cursor.fetchone()[0] == 1:
            return True
    return False


def create_user(params):
    validate_parameters(params, ["username", "password"])
    username = params["username"]
    password = params["password"]

    with open_mysql() as con:
        if user_exists(con, username):
            raise Exception("User already exists: {}".format(username))

        with open_mysql_cursor(con) as cursor:
            cursor.execute(
                "CREATE USER %s@'%%' IDENTIFIED BY %s ;",
                (username, password)
            )
            cursor.execute(
                "GRANT ALL PRIVILEGES ON *.* TO %s@'%%' ;",
                (username, )
            )
    action_set(dict(result="Created user: {}".format(username)))


def set_user_password(params):
    validate_parameters(params, ["username", "password"])

    username = params["username"]
    password = params["password"]
    with open_mysql() as con:
        if not user_exists(con, username):
            raise Exception("User does not exist: {}".format(username))

        with open_mysql_cursor(con) as cursor:
            cursor.execute(
                "ALTER USER %s@'%%' IDENTIFIED BY %s ;",
                (username, password)
            )
    action_set(dict(result="Password updated for user: {}".format(username)))


def delete_user(params):
    validate_parameters(params, ["username", ])

    username = params["username"]
    with open_mysql() as con:
        if not user_exists(con, username):
            action_set(dict(result="User does not exist: {}".format(username)))
            return

        with open_mysql_cursor(con) as cursor:
            cursor.execute(
                "DELETE FROM mysql.user WHERE User = %s ;",
                (username, )
            )
    action_set(dict(result="Deleted user: {}".format(username)))


def create_database(params):
    validate_parameters(params, ["database", ])

    database_name = params["database"]
    with open_mysql() as con:
        with open_mysql_cursor(con) as cursor:
            cursor.execute(
                "SELECT count(1) FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s ;",
                (database_name, )
            )
            if cursor.fetchone()[0] != 0:
                action_set(dict(
                    result="Database already exists: {}".format(database_name)
                ))
                return
            cursor.execute("CREATE DATABASE `{}` ;".format(database_name))
    action_set(dict(result="Database created: {}".format(database_name)))


# A dictionary of all the defined actions to callables (which take
# parsed arguments).
ACTIONS = {
    "create-user": create_user,
    "delete-user": delete_user,
    "set-user-password": set_user_password,
    "create-database": create_database,
}


def main(args):
    action_name = os.path.basename(args[0])
    try:
        action = ACTIONS[action_name]
    except KeyError:
        action_fail("Action {} undefined".format(action_name))
    else:
        try:
            params = action_get()
            action(params)
        except Exception as e:
            action_fail("Action {} failed: {}".format(action_name, str(e)))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
