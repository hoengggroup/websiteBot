# Database Setup (macOS / Windows)



## 0. Preliminaries

Assumptions of this guide:

- You have `sudo` access on your system and are willing to use it should some commands require it.
- A version of PostgreSQL is already installed on the system by whatever method.
- The main target of this guide is a macOS system, but Windows will most likely work similarly.
- The system will only be used as a local development and testing environment.
- General note about Windows systems: You may need to `cd` to the parent folder of your cluster folder first and specify the folder name instead of the folder path. You may also need to provide the full path to the different binaries that are called.




## 1. Preparation

- Usually, an install method creates a default database, which may then already be linked to a service one can enable. In the case of an install via `homebrew` for example, the default database is located at `/usr/local/var/postgres@<major version>`. It can be manually started/stopped with the same `pg_ctl` command  used for manually created clusters (see below) and be interacted with using `psql` when running.
- It is not recommended to run more than one database cluster at a time. Inspect whether a server process is already running using `ps -ef | grep postgres`.
- This guide will concentrate on creating a new cluster for testing and development.



## 2. Creating a new database cluster

1. Create a folder in the project directory with a git-ignored name (`websiteBot/postgresql_database/`, `websiteBot/db/`, `websiteBot/db_data/`) or a folder with any name outside the project file structure.

2. Use the command `initdb`:

   ```shell
   initdb -D <path to cluster folder>
   ```

   This will create a new cluster with the user and owner being the currently logged in user issuing the command.



## 3. Starting the database cluster server

1. Use the command `pg_ctl` (with optional logging):

   ```shell
   pg_ctl -D <path to cluster folder> [-l <path to logfile>] start
   ```

   Note: To bind to a specific IP, supply the option `-o "-i -h <address>"`.

   Note: To bind to a specific port, supply the option `-o "-F -p <port number>"`.



## 4. Creating a new database within the cluster

1. Create the actual database in the cluster, e.g. named `websitebot_db`, using the command `createdb`:

   ```shell
   createdb <database name>
   ```



## 5. Connecting to the database

### Azure Data Studio

Connect to the database using the Connections menu. Be sure to fill out the field "active database" with `<database name>`.

### `psql` shell

You can login with the short-form command:

```shell
psql <database name> [-U <username>]
```

Or with the long-form command:

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

Copy and execute each command (i.e. until the next semicolon; linebreaks within one command should be copied as well) one after the other, regardless of cells.



## 7. Stopping the database cluster server

Use the command `pg_ctl` again:

```shell
pg_ctl -D <path to cluster folder> stop
```



## 8. Deleting the database / database cluster

To delete the database in the cluster, log in to a `psql` shell as the cluster/database owner (user `postgres`) and execute:

```postgresql
DROP DATABASE <database name>;
```

In case you need to take the nuclear option and start over completely by deleting the cluster, first ensure that the server is stopped correctly before attempting any changes. Then, just delete the `<path to cluster folder>` directory.

