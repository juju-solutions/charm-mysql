#!/usr/bin/env python

import sys
from charmhelpers.core.hookenv import (
    log,
    relations_of_type,
    Hooks, UnregisteredHookError
)
from charmhelpers.contrib.charmsupport.nrpe import NRPE


hooks = Hooks()


def update_nrpe_checks():
    log('Refreshing nrpe checks')
    # Find out if nrpe set nagios_hostname
    hostname = None
    for rel in relations_of_type('nrpe-external-master'):
        if 'nagios_hostname' in rel:
            hostname = rel['nagios_hostname']
            break
    nrpe = NRPE(hostname=hostname)
    nrpe.add_check(
        shortname='mysql_proc',
        description='Check MySQL process',
        check_cmd='check_procs -c 1:1 -C mysqld'
    )
    nrpe.write()


@hooks.hook('nrpe-external-master-relation-changed')
@hooks.hook('nrpe-external-master-relation-joined')
def add_nrpe_relation():
    update_nrpe_checks()


if __name__ == '__main__':
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))
