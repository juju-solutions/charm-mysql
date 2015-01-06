#!/usr/bin/env python

import sys

import common
from charmhelpers.core import hookenv


hooks = hookenv.Hooks()
mountpoint = '/srv/mysql'


@hooks.hook('data-relation-joined', 'data-relation-changed')
def data_relation():
    if hookenv.relation_get('mountpoint') == mountpoint:
        # Other side of relation is ready
        common.migrate_to_mount(mountpoint)
    else:
        # Other side not ready yet, provide mountpoint
        hookenv.log('Requesting storage for {}'.format(mountpoint))
        hookenv.relation_set(mountpoint=mountpoint)


@hooks.hook('data-relation-departed')
def data_relation_gone():
    if hookenv.relation_get('mountpoint') == mountpoint:
        hookenv.log('Mount point {} going away. Moving data back to'
                    'local disk.'.format(mountpoint))
        common.migrate_to_disk(mountpoint)


if __name__ == '__main__':
    hooks.execute(sys.argv)
