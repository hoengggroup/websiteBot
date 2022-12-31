# Database Setup (Linux)



## 0. Preliminaries

Assumptions of this guide:

- You have `sudo` access on your system and are willing to use it should some commands require it.
- A version of PostgreSQL is already installed on the system by whatever method.
- The main target of this guide is a Linux system running Ubuntu, but other distros will most likely work the same or similarly, and some remarks about Raspberry Pi (RPI) systems are included as well.
- The system will be used as a deployment and production environment.




## 1. Preparation

- Usually, an install method creates a default database, which may then already be linked to a service one can enable. In the case of an install via `apt` for example, the following default database named "`main`" is created:
  - Database location: `/var/lib/postgresql/<major version>/main/`
  - Configurations location: `/etc/postgresql/<major version>/main/`
  - PID file location: `/var/run/postgresql/`
  - `systemctl` service name: `postgresql@<major version>-main.service`.

- It is not recommended to run more than one database cluster at a time. Inspect whether a server process is already running using `ps -ef | grep postgres` or the Ubuntu/Debian-specific command `pg_lsclusters`.
- This guide will concentrate on using the default cluster for live deployment and production. For that purpose, skip the crossed-out sections which are only provided to provide further insight.



## ~~2. Creating a new database cluster~~

**This is highly discouraged, as there are numerous workarounds and permissions issues you will have to deal with!**

1. Create a folder in the project directory with a git-ignored name (`websiteBot/postgresql_database/`, `websiteBot/db/`, `websiteBot/db_data/`) or a folder with any name outside the project file structure.

2. Use the Ubuntu/Debian-specific command `pg_createcluster`:

   ```shell
   pg_createcluster <major version> <new cluster name> -d <new cluster folder location> [-u <username>] [-- <initdb-style options, e.g. -A trust>]
   ```

   This will create a new database cluster owned by the specified user in the specified location (if the `-u` flag is omitted, the default user and owner will be `postgres`). The configuration files location and the `systemctl` service name will be analogous to the default case. A problem that will be encountered is that the (unchangeable) PID file location is owned by the `postgres` user, hence there will be a warning displayed and upon starting the associated service, it will not be able to copy the PID file associated with the cluster from the `/tmp/` directory to the default PID file location.



## 3. Starting the database cluster server

1. To check the status and details of all clusters on the system, you can use `pg_lsclusters` (also an Ubuntu/Debian-specific command).

1. Use `systemctl` to interact with the previously created service specific to the cluster:

   ```shell
   sudo systemctl <action; e.g. start, stop, restart, status> postgresql@<major version>-main.service
   ```

   There is also the option to control the cluster directly with the Ubuntu/Debian-specific command `pg_ctlcluster`:

   ```shell
   pg_ctlcluster <major version> <cluster name> <action; e.g. start, stop, restart, status>
   ```
   
   This is discouraged, however, as running the cluster as a service brings several advantages.



## 4. Creating a new database within the cluster

1. Until a role in the database cluster for the current user is created later on, we need to interface with it using the `postgres` user:

   ```shell
   sudo su postgres
   ```

2. Create the actual database in the cluster, e.g. named `websitebot_db`, using the command `createdb`:

   ```shell
   createdb <database name; e.g. websitebot_db>
   ```



## 5. Connecting to the database

### General setup for remote servers

Connecting to a cluster on a remote location (i.e. not `localhost`) via SSH is only possible if a password for the database user is set, as peer authentication will not work. A password will be created for the `websitebot` user in `db_setup.ipynb`, but if use of the `postgres` user is required (such as during the setup process), set a password for it in the `psql` shell directly on the remote location using:

```postgresql
ALTER USER postgres WITH PASSWORD '<password>';
```

Note: The two single quote marks around the new password may not be omitted.

1. **CAUTION**: Be advised that the following steps make the database public-facing to the general internet, so proceed carefully and be conscious of security risks.

2. In the file `/etc/postgresql/<major version>/<cluster name>/postgresql.conf`, uncomment the line starting with "`listen_addresses`" and set it to `'*'` (the single quote marks may not be omitted). This allows PostgreSQL to listen to non-local connections.

3. Add the following lines to the file `/etc/postgresql/<major version>/<cluster name>/pg_hba.conf`:

   ```
   # TYPE  DATABASE        USER            ADDRESS                 METHOD
   host    all             <psql user>     0.0.0.0/0               md5
   host    all             <psql user>     ::/0                    md5
   ```

   This specifies the IP mask for allowed connections; in this case it allows any incoming connection.

   Note: `<psql user>` can specify a specific user, e.g. `websitebot` or `postgres`, or alternatively `all`. During first setup it needs to be set to `all` or `postgres`, as there exist no other users of the database yet, but at the end of the setup procedure this should be changed to the specific psql username (e.g. `websitebot`) so as to not allow root/owner access to the database from remote connections.

   Note: Method "`md5`" specifies that the authentication is password-based and hashed with md5. Other options - among others - are `peer` (only available on local system) or `trust` (meaning no authentication at all).

   Note: If the server is in your own subnet, the whitelist entry can be made more strict, e.g.:

   ```
   # TYPE  DATABASE        USER            ADDRESS                 METHOD
   host    all             <psql user>     192.168.1.1/24          md5
   ```

4. Allow incoming connections on the database's port, e.g. `5432` (the PostgreSQL default), in the Linux firewall:

   ```shell
   sudo ufw allow <port>
   ```

5. Restart the `postgresql` service for the changes to take effect:

   ```shell
   sudo systemctl restart postgresql
   ```

### Azure Data Studio

Connect to the database using the Connections menu. Be sure to fill out the field "active database" with `<database name>`.

### `psql` shell

As before, until a role in the database cluster for the current user is created later on, we need to interface with it using the `postgres` user:

```shell
sudo su postgres
```

Before other users are added, you have to login with the short-form command (without the `-U` flag), later on you can use it as well:

```shell
psql <database name> [-U <username>]
```

Or you can use the long-form command:

```shell
psql "postgresql://<username>[:<password>]@<database server location>[:<port>]/<database name>"
```

If the login does not work (cannot `su` or `-U` to user that owns the database, no prompt for password appears, connection fails due to unsuccessful peer authentication, login to a remote server, etc.) use the long-form command, which should mitigate any issues.

Note: `<database name>` is not the `<path to cluster folder/cluster name>` but the name of the database created in the last section, e.g. `websitebot_db`.

Note: `<database server location>` is not the `<path to cluster folder/cluster name>` but the actual network location where PostgreSQL listens for connections, e.g. `localhost`.

Note:  `<password>` may be omitted depending on whether a password is set for the user on the database.

Note: `<port>` may be omitted unless the port for the database was manually specified.

##### Useful commands in the `psql` shell:

| command | description |
| --- | --- |
| `\d (\d+) {tablename}` | list all columns and their data types in the given table (`+` = more info) |
| `\dt (\dt+)` | list all relations (i.e. tables) (`+` = more info) |
| `\du (\du+)` | list all users (`+` = more info) |
| `\l (\l+)` | list all databases in the current logged in cluster (`+` = more info) |
| `\t` | toggle display of column headers in outputs |
| `\pset format wrapped` | set the columns to a fixed display width (text wraps around within column width) |
| `\pset null (null)` | set the display style of `NULL` values from invisible to `(null)` |
| `\conninfo` | display information (db, user, port) about current database connection |
| `\q` | exit shell |



## 6. Building the structure of the database

Refer to the `db_setup.ipynb` Jupyter notebook for the commands which are to be executed. If applicable, be sure to fill in placeholders (i.e. secrets which are stored somewhere else) temporarily before executing and remember to restore the placeholders afterwards.

### Azure Data Studio

Simply attach the notebook to the PostgreSQL connection and execute each cell one after the other. As noted at the end of the notebook once more: Remember to "Clear Results" after finishing for a clean notebook file.

### `psql` shell

Copy and execute each command (i.e. until the next semicolon; line-breaks within one command should be copied as well) one after the other, regardless of cells.



## 7. Stopping the database cluster server

Interact with the `systemctl` service to stop the cluster (see above) or use `pg_ctlcluster` to do so, depending on how the cluster was started.



## 8. Deleting the database / database cluster

To delete the database in the cluster, log in to a `psql` shell as the cluster/database owner (user `postgres`) and execute:

```postgresql
DROP DATABASE <database name>;
```

In case you need to take the nuclear option and start over completely by deleting the cluster, first ensure that the server is stopped correctly before attempting any changes. Then, uninstall all `postgresql` packages using `apt` and delete the files/folders specified at the beginning of this guide (and the custom database folder if the discouraged option was chosen). Finally, reinstall `postgresql` again using `apt` (which will create a default "`main`" cluster again).



## Remarks on Raspberry Pi setups

### SSH connections

1. Make sure that the SSH client used to interact with the RPI does not set conflicting environment variables (especially locale, as these settings are read by PostgreSQL when creating a new cluster). To do this, comment out the relevant lines in `/etc/ssh/ssh_config`.
2. To be sure, set system-wide locale again using `raspi-config`.
3. Reboot the RPI and restart the SSH connection.