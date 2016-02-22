pysar
=====

Small Python utility to provide system activity reports from the
`sysstat` package as PostgreSQL foreign tables.

Provides a generator to parse the output of the `sadf` tool into named
tuples and a Multicorn Foreign Data Wrapper for the next hop into a
PostgreSQL database.

	sadf/sysstat --> Python --> PostgreSQL foreign table

Scope is limited as this was written purely to allow a common,
SQL-based entry point to these data (specifically device IO currently)
but it should be easily extendable to similar use cases.


Install
-------

> NOTE: Instructions are Debian-focused and semi-tested.

There are a number of ways of setting this up depending on how you
want to obtain the packages and where you want to install, but
something like the following should work.

### Dependencies 

There are no dependencies for the first hop, but the second requires
Multicorn (Python3; Python2 is untested). 

#### Install sysstat

	user@host:~$ sudo apt-get install sysstat

Enable data collection:

	user@host:~$ sudo sed -i 's/ENABLED="false"/ENABLED="true"/' /etc/default/sysstat


#### Install Multicorn

	user@host:~$ sudo apt-get install postgresql-9.4-python3-multicorn

> You can only have either the python or python3 deb installed.


### Install pysar

	user@host:~$ sudo su - postgres
	postgres@host:~$ mkdir -p ~/.local/lib/python3.4/site-packages
	postgres@host:~$ cd /tmp; wget https://github.com/corriander/pysar.git
	postgres@host:/tmp$ cd pysar
	postgres@host:/tmp/pysar$ python3 setup.py install --user


### Restart DB Cluster

	postgres@host:~$ pg_ctlcluster 9.4 main restart


Uninstall
---------

	rm -rf /var/lib/postgresql/.local/lib/python3.4/site-packages/pysar*


Example Usage
-------------

	user@host:~$ createdb sysstat
	user@host:~$ psql sysstat
	sysstat=# CREATE EXTENSION multicorn;
	CREATE EXTENSION
	sysstat=# \i /tmp/pysar/sql/create_server_pysar_devio.sql
	CREATE SERVER
	sysstat=# \i /tmp/pysar/sql/create_table_device_io.sql
	CREATE FOREIGN TABLE
	sysstat=# SELECT * FROM device_io;
