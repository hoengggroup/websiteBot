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



## 5. Setting up the database for remote connections

**CAUTION**: The following steps will enable secure remote connections via SSL/TLS to the database, but be advised that this means it is still public-facing to the general internet, so proceed carefully and be conscious of security risks.

### 1. Setting/Resetting user passwords

Connecting to a cluster on a remote location (i.e. not `localhost`) is only possible if a password for the database user is set, as peer authentication will obviously not work. A password will be created for the `websitebot` user in `db_setup.ipynb`, but if use of the `postgres` user is required (such as during the setup process), set a password for it in the `psql` shell directly on the remote location using:

```postgresql
ALTER USER postgres WITH PASSWORD '<password>';
```

Note: The two single quote marks around the new password may not be omitted.

Note: Apparently, when switching from `md5` to `scram-sha-256` as the password encryption method (see later steps), passwords set before altering the setting may not be accepted anymore. In this case, log in to the `psql` shell and reset the password (it can still be the same one as before).

### 2. Generating a root CA and server/client certificates

The following steps are based on the [official PostgreSQL documentation](https://www.postgresql.org/docs/current/ssl-tcp.html) and [this tutorial](https://www.crunchydata.com/blog/ssl-certificate-authentication-postgresql-docker-containers). We will generate certificates and private/public keys to facilitate SSL/TLS-encrypted connections.

1. Ensure you are connected to the server as the root user.

2. Create a new folder to store the files generated in the next steps, e.g. `/root/ssl/`, and `cd` to it.

3. Root CA: Generate a certificate signing request (CSR) and corresponding key, with the `CN` value corresponding to your root hostname, e.g. `root.hoengggroup-host`.

   ```shell
   openssl req -new -nodes -text -out root.csr -keyout root.key -subj "/CN=<root hostname>"
   ```

4. Root CA: Sign CSR with key to create the root CA, valid for 3650 days:

   ```shell
   openssl x509 -req -in root.csr -text -days 3650 -extfile /etc/ssl/openssl.cnf -extensions v3_ca -signkey root.key -out root.crt
   ```

   The CSR is not needed anymore:

   ```shell
   rm root.csr
   ```

5. Server certificate: Generate a CSR and corresponding key, with the `CN` value corresponding to your server hostname, e.g. `websitebot.hoengggroup-host`.

   ```shell
   openssl req -new -nodes -text -out server.csr -keyout server.key -subj "/CN=<server hostname>"
   ```

6. Server certificate: Sign CSR with root key and root CA to create server certificate, valid for 365 days:

   ```shell
   openssl x509 -req -in server.csr -text -days 365 -CA root.crt -CAkey root.key -CAcreateserial -out server.crt
   ```

   The CSR is not needed anymore:

   ```shell
   rm server.csr
   ```

7. Client certificate: Generate a CSR and corresponding key, with the `CN` value corresponding to your database username, e.g. `websitebot`.

   ```shell
   openssl req -new -nodes -text -out client.csr -keyout client.key -subj "/CN=<username for database>"
   ```

8. Client certificate: Sign CSR with root key and root CA to create client certificate, valid for 365 days:

   ```shell
   openssl x509 -req -in client.csr -text -days 365 -CA root.crt -CAkey root.key -CAcreateserial -out client.crt
   ```

   The CSR is not needed anymore:

   ```shell
   rm client.csr
   ```

### 3. Distributing the certificate and key files

The following files should be present in the previously created folder:

```
client.crt
client.key
root.crt
root.key
server.crt
server.key
```

In order to be able to use these files, some must be placed in the correct folders on the server and others must be downloaded to the client.

1. Copy the root CA, server certificate, and server key to the correct folder (sub-folders of `/etc/ssl/`) and set the correct file permissions and ownership:

   ```shell
   cp <folder name>/root.crt /etc/ssl/certs/postgresql_root.crt
   chown root:root /etc/ssl/certs/postgresql_root.crt
   chmod 644 /etc/ssl/certs/postgresql_root.crt
   ```

   ```shell
   cp <folder name>/server.crt /etc/ssl/certs/postgresql_server.crt
   chown root:root /etc/ssl/certs/postgresql_server.crt
   chmod 644 /etc/ssl/certs/postgresql_server.crt
   ```

   ```shell
   cp <folder name>/server.key /etc/ssl/private/postgresql_server.key
   chown root:ssl-cert /etc/ssl/private/postgresql_server.key
   chmod 640 /etc/ssl/private/postgresql_server.key
   ```

   Note: The destination file names were chosen for the files to be more distiguishable, but you can name them differently (you have to adapt the next steps accordingly of course).

2. As `server.key` is the only one of these files that has to have `640` instead of `644` permissions, make sure the `postgres` user is a member of the group `ssl-cert` (see `chown` command in the line before) in order to have read access:

   ```shell
   groups postgres
   ```

   The postgres user should be a member by default, but add it to this group in case it is not:

   ```shell
   sudo usermod -aG ssl-cert postgres
   ```

3. Download the files needed to authenticate with the server - the root CA, client certificate, and client key - to the clients using `scp` on the client devices:

   ```shell
   scp root@<server IP>:<path to folder>/root.crt <path to destination folder>/root.crt
   scp root@<server IP>:<path to folder>/client.crt <path to destination folder>/client.crt
   scp root@<server IP>:<path to folder>/client.key <path to destination folder>/client.key
   ```

4. Lock down the files in the original folder and the folder itself on the server:

   ```shell
   chmod og-rwx <folder name>/*
   chmod og-rwx <folder name>
   ```

   Note: This command means that for 'o'thers and 'g'roup '-' (remove) 'r'ead, 'w'rite, and e'x'ecute permissions; i.e. everyone except the owner (root) has no permissions.

### 4. Editing PostgreSQL config files

1. Make the follwing edits in the file `/etc/postgresql/<major version>/<cluster name>/postgresql.conf` (uncomment lines and replace or fill in values as needed):

   ```
   listen_addresses = 'localhost,<server IP>'
   max_connections = <maximum simultaneous connections allowed, e.g. 30>
   superuser_reserved_connections = <simultaneous connections reserved for superuser access, e.g. 5; this value lowers max_connections for normal users>
   
   password_encryption = 'scram-sha-256'
   
   ssl = on
   ssl_ca_file = '/etc/ssl/certs/postgresql_root.crt'
   ssl_cert_file = '/etc/ssl/certs/postgresql_server.crt'
   ssl_key_file = '/etc/ssl/private/postgresql_server.key'
   ```

2. Add the following lines to the file `/etc/postgresql/<major version>/<cluster name>/pg_hba.conf` ("hba" stands for host-based authentication):

   ```
   # TYPE  DATABASE        USER            ADDRESS                 METHOD
   hostssl all             <psql user>     0.0.0.0/0               scram-sha-256 clientcert=verify-full
   hostssl all             <psql user>     ::/0                    scram-sha-256 clientcert=verify-full
   ```

   This specifies the details for incoming connections to be allowed; in this case the connection can come from anywhere (indicated by `0.0.0.0/0` and `::/0`) and must connect via SSL/TLS.

   Note: `pg_hba.conf`'s rules are not "pass-through", so the order of lines matters. This is not relevant here, but is important for other examples - e.g. when the `postgres` user is set to be `reject`ed on any incoming `hostssl` connection (sometimes done as good practice), adding the above lines after that rule with `<psql user> = all` (see next note) will still not allow the `postgres` user to log in remotely, as the `reject` rule already produced a match and the rest of the file will not get parsed for that connection.

   Note: `<psql user>` can specify a specific user, e.g. `websitebot` or `postgres`, or alternatively `all`. During first setup it needs to be set to `all` or `postgres`, as there exist no other users of the database yet, but at the end of the setup procedure this should be changed to the specific psql username (e.g. `websitebot`) so as to not allow root/owner access to the database from remote connections.

   Note: Method "`scram-sha-256 clientcert=verify-full`" specifies that for successful authentication, a password - which is hashed with scram-sha-256 - and a client certificate must be provided. Other options - among others - are `peer` (only available on local system for Unix socket connections) or `trust` (meaning no authentication at all).

   Note: If the server is in your own subnet, the whitelist entry can be made more strict by narrowing the addresses for the rule, e.g. `192.168.1.1/24`.

### 5. Firewall and server configuration

1. Allow incoming connections on the database's port, e.g. `5432` (the PostgreSQL default), in the Linux firewall:

   ```shell
   sudo ufw allow <port>
   ```

2. Make sure the firewall settings at your hosting provider allows the port as well.

### 6. Finishing up

1. Restart the `postgresql` service for the changes to take effect:

   ```shell
   sudo systemctl restart postgresql
   sudo systemctl restart postgresql@<major version>-main.service
   ```



## 6. Connecting to the database

### Azure Data Studio

Connect to the database using the "Connections" menu and the "Advanced..." sub-menu by filling out the relevant fields:

```
Connection type: PostgreSQL
Server name: <server hostname specified in server certificate>
Authentication type: Password
User name: <psql user>
Password: <psql user password>
Database name: <database name; e.g. websitebot_db>

Host IP address: <server IP>
Port: <port; e.g. 5432>
SSL mode: Verify-Full
Use SSL compression: False
SSL certificate filename: <path to destination folder>/client.crt
SSL key filename: <path to destination folder>/client.key
SSL root certificate filename: <path to destination folder>/root.crt
```

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
psql "postgresql://<username>[:<password>]@<database server hostname>[:<port>]/<database name>[?<paramspec>&<paramspec>&...]"
```

If the login does not work (cannot `su` or `-U` to user that owns the database, no prompt for password appears, connection fails due to unsuccessful peer authentication, login to a remote server, etc.) use the long-form command, which should mitigate any issues.

Explanation of the keywords:

```
<username>: <psql user>
<password>: <password;
             may be omitted depending on whether a password is set for the user on the database;
             if the password contains special characters, escape them using the % syntax for URLs>
<database server hostname>: <hostname of the server where PostgreSQL listens for connections, e.g. 'localhost' or the server hostname specified in server certificate;
                             not the path to cluster folder/cluster name>
<port>: <port; e.g. 5432; may be omitted unless set to non-default value>
<database name>: <name of the database created in a previous section, e.g. 'websitebot_db';
                  not the path to cluster folder/cluster name>
<paramspec>: <additional key=value pairs; for example the ones needed for SSL/TLS connections are:
              hostaddr=<server IP>
              sslmode=verify-full
              sslrootcert=<path to destination folder>/root.crt
              sslcert=<path to destination folder>/client.crt
              sslkey=<path to destination folder>/client.key
              sslcompression=0>
```

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



## 7. Check connection status/details:

This section is based on [this tutorial](https://www.percona.com/blog/enabling-and-enforcing-ssl-tls-for-postgresql-connections/).

In addition to the command `\conninfo` in the `psql` shell, you can check the security of your active connections with the following SQL queries:

```postgresql
SHOW password_encryption;
SELECT pg_ssl.pid, pg_ssl.ssl, pg_ssl.version, pg_sa.backend_type, pg_sa.usename, pg_sa.client_addr FROM pg_stat_ssl pg_ssl JOIN pg_stat_activity pg_sa ON pg_ssl.pid = pg_sa.pid;
```

The former will return the encryption method used for passwords (md5 or scram-sha-256), and the latter will return a table of all active connections (PIDs) and their SSL/TLS details.



## 8. Building the structure of the database

Refer to the `db_setup.ipynb` Jupyter notebook for the commands which are to be executed. If applicable, be sure to fill in placeholders (i.e. secrets which are stored somewhere else) temporarily before executing and remember to restore the placeholders afterwards.

### Azure Data Studio

Simply attach the notebook to the PostgreSQL connection and execute each cell one after the other. As noted at the end of the notebook once more: Remember to "Clear Results" after finishing for a clean notebook file.

### `psql` shell

Copy and execute each command (i.e. until the next semicolon; line-breaks within one command should be copied as well) one after the other, regardless of cells.



## 9. Stopping the database cluster server

Interact with the `systemctl` service to stop the cluster (see above) or use `pg_ctlcluster` to do so, depending on how the cluster was started.



## 10. Deleting the database / database cluster

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