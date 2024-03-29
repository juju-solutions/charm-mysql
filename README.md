# DEPRECATION NOTICE

This charm has been superseded by `Charmed MySQL` (machine charm) and `Charmed MySQL K8s` (k8s charm).

- For [Charmed MySQL](https://charmhub.io/mysql), please report issues in the [mysql-operator repo](https://github.com/canonical/mysql-operator).
- For [Charmed MySQL K8s](https://charmhub.io/mysql-k8s), please report issues in the [mysql-k8s-operator repo](https://github.com/canonical/mysql-k8s-operator).

This repo is now archived and remains for historical purposes only.

-----

# Overview

[MySQL](http://www.mysql.com) is a fast, stable and true multi-user, multi-threaded SQL database server. SQL (Structured Query Language) is the most popular database query language in the world. The main goals of MySQL are speed, robustness and ease of use.

This charm also can deploy [Percona Server](http://www.percona.com/software/percona-server) is fork of MySQL by Percona Inc. which focuses on maximizing performance, particularly for heavy workloads. It is a drop-in replacement for MySQL and features XtraDB, a drop-in replacement for the InnoDB storage engine.

# Usage

## General Usage

To deploy a MySQL service:

    juju deploy mysql

Once deployed, you can retrieve the MySQL root user password by logging in to the machine via `juju ssh` and readin the `/var/lib/mysql/mysql.passwd` file. To log in as root MySQL User at the MySQL console you can issue the following:

    juju ssh mysql/0
    mysql -u root -p`sudo cat /var/lib/mysql/mysql.passwd`

## Backups

The charm supports simple backups. To enable them set `backup_schedule` option. Optionally you can override default `backup_dir` and/or `backup_retention_count`:

    juju config mysql backup_schedule="45 5 * * *" # cron formatted schedule
    juju config mysql backup_dir="/mnt/backup"
    juju config mysql backup_retention_count=28

# Scale Out Usage 

## Replication

MySQL supports the ability to replicate databases to slave instances. This
allows you, for example, to load balance read queries across multiple slaves or
use a slave to perform backups, all whilst not impeding the master's
performance.

To deploy a slave:

    # deploy second service
    juju deploy mysql mysql-slave

    # add master to slave relation
    juju add-relation mysql:master mysql-slave:slave

Any changes to the master are reflected on the slave.

Any queries that modify the database(s) should be applied to the master only.
The slave should be treated strictly as read only.

You can add further slaves with:

    juju add-unit mysql-slave

## Monitoring

This charm provides relations that support monitoring via either [Nagios](https://jujucharms.com/precise/nagios) or [Munin](https://jujucharms.com/precise/munin/). Refer to the appropriate charm for usage.

# Configuration

You can tweak various options to optimize your MySQL deployment:

* max-connections - Maximum connections allowed to server or '-1' for default.

* preferred-storage-engine - A comma separated list of storage engines to
  optimize for. First in the list is marked as default storage engine. 'InnoDB'
  or 'MyISAM' are acceptable values.

* tuning-level - Specify 'safest', 'fast' or 'unsafe' to choose required
  transaction safety. This option determines the flush value for innodb commit
  and binary logs. Specify 'safest' for full ACID compliance. 'fast' relaxes the
  compliance for performance and 'unsafe' will remove most restrictions.

* dataset-size - Memory allocation for all caches (InnoDB buffer pool, MyISAM
  key, query). Suffix value with 'K', 'M', 'G' or 'T' to indicate unit of
  kilobyte, megabyte, gigabyte or terabyte respectively. Suffix value with '%'
  to use percentage of machine's total memory.

* query-cache-type - Specify 'ON', 'DEMAND' or 'OFF' to turn query cache on,
  selectively (dependent on queries) or off.

* query-cache-size - Size of query cache (no. of bytes) or '-1' to use 20%
  of memory allocation.

Each of these can be applied by running:

    juju config <service> <option>=<value>

e.g.

    juju config mysql preferred-storage-engine=InnoDB
    juju config mysql dataset-size=50%
    juju config mysql query-cache-type=ON
    juju config mysql query-cache-size=-1

Deploying Percona Server is an option in this charm, you can do so by editing the `flavor` option:

    juju config mysql flavor=percona

WARNING: Migrating from MySQL to Percona Server in this fashion is currently a one-way migration, once you migrate you cannot migrate back via Juju. 

To change the source that the charm uses for packages:

  juju config mysql source="cloud:precise-icehouse"

This will enable the Icehouse pocket of the Cloud Archive and upgrade the install of any 'cloud' packages to the new version.

The source option can be used in a few different ways:

  source="ppa:james-page/testing" - use the testing PPA owned by james-page
  source="http://myrepo/ubuntu main" - use the repository located at the provided URL

The charm also supports use of arbitary archive key's for use with private repositories:

  juju config mysql key="C6CEA0C9"

Note that in clustered configurations, the upgrade can be a bit racey as the services restart and re-cluster; this is resolvable using:

  juju resolved mysql/1

# Caveats 

When deploying MySQL on the local provider, there is a known memory exhaustion issue. To work around this until the issue is patched:

    juju config mysql dataset-size='512M'
    juju resolved mysql/#

# MySQL and Percona Server Contact Information

- [MySQL Homepage](http://www.mysql.com)
- [MySQL Bug Tracker](http://bugs.mysql.com/)
- [Percona Server Homepage](http://www.percona.com/software/percona-server)
- [Percona Server Bug Tracker](https://bugs.launchpad.net/percona-server/)
- [MySQL mailing lists](http://lists.mysql.com/)
