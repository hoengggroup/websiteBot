# Server Setup



## 0. Preliminaries

This setup guide assumes a (fresh) Ubuntu Linux installation on your personal device or remote host/VPS. Other Linux distributions will probably work similarly; on macOS some more work may be needed to adapt the steps. The process on a Windows machine will very likely be substantially different and will not be covered here.



## 1. Basic setup

1. Login as the `root` user.

2. Create a user account for the project, e.g. `websitebot`.

   ```shell
   sudo adduser <username>
   ```

   Follow the prompts to set a password and the name of the user (other details being asked are e.g. phone number; this is a holdover from the Unix days and can be skipped by pressing enter).

3. Give the newly created user `sudo` privileges.

   ```shell
   sudo usermod -aG sudo <username>
   ```

   Check if the groups are set correctly using:

   ```shell
   groups <username>
   ```

4. Open the editor for the `sudoers` file:

   ```shell
   sudo visudo
   ```

   Add the following line at the end of the file:

   ```
   <username> ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/bin/rm, /usr/bin/wget, /usr/bin/unzip, /usr/bin/pkill, /usr/sbin/ip, /usr/sbin/openvpn
   ```

   This allows for a non-sudo execution of the startup script, which uses these commands.

5. Install software packages (some needed for operation of the project, some for QoL):

   ```shell
   sudo apt install <package>
   ```

   ```
   jq
   nnn
   openvpn
   postgresql
   ```



## 2. DNS setup (optional)

If you want to use a different DNS provider, follow the following steps:

1. Optional: Check which DNS provider is the fastest for your server by running the shell script below:

   ```shell
   #!/bin/bash
   
   # adapted from https://unix.stackexchange.com/a/680430
   
   DOMAIN=wikipedia.org;
   
   echo "Tests common resolvers and calculates average response times by testing each resolver 3 times."
   echo "************************"
   echo "Cloudflare: 1.1.1.1"
   echo "Level 3: 4.2.2.2"
   echo "OpenDNS: 208.67.220.220"
   echo "Google: 8.8.8.8"
   echo "ANTEL: 200.40.30.245"
   echo "Dyn: 216.146.35.35"
   echo "Neustar: 156.154.70.1"
   echo "puntCAT: 109.69.8.51"
   echo "UncensoredDNS: 91.239.100.100"
   echo "Hurricane Electric: 74.82.42.42"
   echo "Private Vultr DNS: 108.61.10.10"
   echo "************************\n\n"
   
   for resolver in 1.1.1.1 4.2.2.2 208.67.220.220 8.8.8.8 200.40.30.245 216.146.35.35 156.154.71.1 109.69.8.51 91.239.100.100 74.82.42.42 108.61.10.10
   do
     echo $resolver
     for reps in {1..3}
     do
       dig $DOMAIN @$resolver | awk '/time/ {print $4 " ms"}'
       sleep 3
     done | awk '/ms/ {sum+=$1} END {print "Avg time: ",sum/3, " ms"}'
     echo
   done
   ```

2. Check the currently established network links for future reference.

   ```shell
   networkctl list
   networkctl status <link>
   ip addr
   ```

3. Install the `resolvconf` package:

   ```shell
   sudo apt install resolvconf
   ```

4. Add a line for each DNS server address (up to 3 lines allowed) as follows to the end of `/etc/resolvconf/resolv.conf.d/head` (ignore the comments at the top of that file)

   ```
   nameserver <address>
   ```

   For the change to take effect, regenerate the file `/etc/resolv.conf` (the comment block mentioned above is for guarding this generated file) with:

   ```shell
   sudo resolvconf -u
   ```

5. Verify that the changes took effect by examining the output of `dig`:

   ```shell
   dig <example domain>
   ```

   For general testing purposes, you can also specify a DNS server to be queried to `dig` directly:

   ```shell
   dig <example domain> @<DNS server address>
   ```

6. Alternatively - or additionally - you can specify DNS resolution options managed through `systemd` by uncommenting lines and filling in the details in the file `/etc/systemd/resolved.conf`. Then restart the service:

   ```shell
   sudo systemctl restart systemd-resolved.service
   ```



## 3. Database setup

Switch to the user who will run the bot, either by logging out of the ssh session and logging back in with the other username, or just run `su <username>`.

See `setup_db_linux.md` for further instructions.



## 4. Running `websiteBot`

1. Copy/clone the project files to the server via your preferred method, e.g. `git clone` or `scp` (for the latter, see below).

2. Copy the setup script (`websitebot.sh` in this case) to a folder outside the project folder, and run any bootstrapping routines available in the script (e.g. sync with GitHub again or install config files). Always keep that copy updated.

3. Copy to/create in the project tree any untracked files/folders needed; in the case of `websiteBot` for example:

   ```shell
   ${REPO_HOME}/secrets/nordvpn_auth.txt (copy from remote)
   ${REPO_HOME}/secrets/pg_string.txt (copy from remote)
   ${REPO_HOME}/.websitebot_assert_vpn (create empty file)
   ${REPO_HOME}/.websitebot_deployed (create empty file)
   ```

4. Install the Python packages required by the project:

   ```shell
   pip3 install --user
   ```

   ```
   html2text
   psycopg
   python-telegram-bot
   requests
   sdnotify
   unidecode
   ```

5. Create a `systemd` service by creating a file in `/etc/systemd/system/`, e.g. named `websitebot.service`, with the following contents:

   ```
   [Unit]
   Description=websiteBot
   After=network-online.target
   
   [Service]
   Type=simple
   User=<executing user, e.g. websitebot>
   ExecStart=<path to startup script, e.g. websitebot.sh> <options for startup script, e.g. -v ch>
   WatchdogSec=300s
   StartLimitBurst=3
   StartLimitInterval=10min
   NotifyAccess=all
   Restart=always
   RemainAfterExit=no
   
   [Install]
   WantedBy=multi-user.target
   ```

6. Reload the available services using:

   ```shell
   sudo systemctl daemon-reload
   ```

   They can be listed with:

   ```shell
   systemctl list-units --type=service
   ```

7. Use `systemctl` to interact with the previously created service:

   ```shell
   sudo systemctl <action; e.g. start, stop, restart, status> <service name>.service
   ```

8. To edit the service file contents, run:

   ```shell
   sudo systemctl edit --full <service name>.service
   ```

9. In case the service failed too many times in short succession, e.g. due to an error that was introduced with an update, the system will block a start/restart even if the error was fixed in the meantime. In that case, the failed-state counter has to be reset first:

   ```shell
   sudo systemctl reset-failed <service name>.service
   ```

10. To see a live output of the service's log entries to the terminal, run:

   ```shell
   journalctl -f -u <service name>.service
   ```



## 5. Keeping the server maintained

### Updating project files

1. Ensure that the newest version of the startup script is copied outside the project folder.

2. Run its updating mechanism; for `websitebot.sh`:

   ```shell
   websitebot.sh -r -n -g
   ```

### Updating system packages

Be careful about whether your code needs to be updated to work with new package versions.

1. Gather and list new updates:

   ```shell
   apt list --upgradable
   ```

2. Upgrade the packages:

   ```shell
   sudo apt upgrade
   ```

### Updating Python packages

Be careful about whether your code needs to be updated to work with new package versions.

1. Gather and list new updates:

   ```shell
   pip3 list --outdated
   ```

2. Upgrade the packages:

   ```shell
   pip3 install --upgrade --user
   ```

### Downloading files from the server

Use `scp` (short for "secure copy") on the machine to download to:

```shell
scp <username>@<server location, i.e. IP address>:<path to file to be copied> <path to local target folder>
```

### Uploading files to the server

Use `scp` (short for "secure copy") on the machine to upload from:

```shell
scp <path to file to be copied> <username>@<server location, i.e. IP address>:<path to remote target folder>
```

### Updating server SSH keys on the remote devices

In case the server gets a new SSH key, e.g. after the server is wiped and reinstalled, its keys must be removed from the SSH keychains on the remote devices:

```shell
ssh-keygen -R <server location, i.e. IP address>
```

The next time a connection via SSH is established, the new server SSH key can be added to the remote's known_hosts file. If the previous step is skipped, only a warning without a prompt to update the key is displayed.

**CAUTION**: The mentioned warning is not without merit; be extremely careful unless the reason for the SSH key update is known (like e.g. a recent server reinstall).
