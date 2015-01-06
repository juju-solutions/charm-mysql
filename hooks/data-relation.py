#!/usr/bin/env python

import sys

from charmhelpers.core import hookenv


hooks = hookenv.Hooks()


@hooks.hook('data-relation-joined', 'data-relation-changed')
def data_relation():
    config = hookenv.config()
    if 'backup_dir' in config and config.get('backup_schedule', None):
        hookenv.log('Requesting storage for {}'.format(config['backup_dir']))
        hookenv.relation_set(mountpoint=config['backup_dir'])
    else:
        hookenv.log('Backup schedule not set, skipping storage request.')

if __name__ == '__main__':
    hooks.execute(sys.argv)
