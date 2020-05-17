#!/usr/bin/env bash

restart_flag=false
github_flag=false
vpn_flag=false
temp_directory='/home/pi/temp/'
vpn_directory='/etc/openvpn/'
vpn_pattern='ch'
vpn_suffix='.tcp443.ovpn'
bot_directory='/home/pi/oldShatterhand/oldShatterhand/'
help_text="\
Usage: $(basename $0) [-r] [-g] [-v VPN_PATTERN] [-d BOT_DIRECTORY]

Options:
  -r                  restart the bot service
  -g                  clone the bot's code from GitHub
  -v <VPN_PATTERN>    connect to VPN before starting the bot using a configuration matching VPN_PATTERN
                      defaults to configurations containing 'ch'
  -d <BOT_DIRECTORY>  run the bot from the specified directory
                      defaults to '/home/pi/oldShatterhand/oldShatterhand/'
"

print_usage() {
    printf "$help_text"
}

get_ip() {
    printf "The current IP address is: $(curl --silent https://api.ipify.org)\n"
}

restart_bot() {
    printf 'Stopping websitebot service...\n'
    sudo systemctl stop websitebot.service
    printf 'websitebot service stopped.\n'
    if [ "$github_flag" = true ]; then
        sync_github
        github_flag=false
    fi
    if [ "$vpn_flag" = true ]; then
        connect_vpn
        vpn_flag=false
    fi
    printf 'Restarting websitebot service. Wait for output of service status.\n'
    sudo systemctl start websitebot.service
    sleep 2
    systemctl status websitebot.service
}

sync_github() {
    printf 'Cloning from GitHub.\n'
    git clone git@github.com:niklasbogensperger/websiteBot.git $temp_directory
    rsync -av $temp_directory $bot_directory
    rm -rf $temp_directory
    printf 'Successfully cloned from GitHub.\n'
}

connect_vpn() {
    printf 'Connecting to VPN.\n'
    get_ip
    connection_success=false

    for i in $(curl --silent https://api.nordvpn.com/server/stats | jq --slurp --raw-output --arg vpn_pattern "$vpn_pattern" '.[] | to_entries | map(select(.key | contains($vpn_pattern))) | sort_by(.value.percent) | limit(10;.[]) | [.key] | "\(.[0])"'); do
        config="${vpn_directory}${i}${vpn_suffix}"
        if sudo openvpn --config $config --auth-user-pass ${vpn_directory}auth.txt --daemon; then
            printf "Successfully connected to VPN using config file: ${config}\nWaiting for new IP.\n"
            sleep 15
            get_ip
            connection_success=true
            break
        else
            printf "Could not connect to VPN using config file: ${config}\n"
            connection_success=false
        fi
    done
    if [ "$connection_success" = false ]; then
        for i in $(find ${vpn_directory} -name "$vpn_pattern*" | sort); do
            if sudo openvpn --config $i --auth-user-pass ${vpn_directory}auth.txt --daemon; then
                printf "Successfully connected to VPN using config file: ${i}\nWaiting for new IP.\n"
                sleep 15
                get_ip
                connection_success=true
                break
            else
                printf "Could not connect to VPN using config file: ${i}\n"
                connection_success=false
            fi
        done
    fi
    if [ "$connection_success" = false ]; then
        printf 'Could not connect to VPN with any of the config files matching the provided pattern.\n'
    fi
}

while getopts 'rgv:d:h' flag; do
    case "${flag}" in
        r) restart_flag=true ;;
        g) github_flag=true ;;
        v) vpn_flag=true
           vpn_pattern="${OPTARG}" ;;
        d) bot_directory="${OPTARG}" ;;
        *) print_usage  # -h flag does not raise error here because it is also specified as a flag above
        exit 1 ;;
    esac
done

if [ "$restart_flag" = true ]; then
    restart_bot
fi

if [ "$github_flag" = true ]; then
    sync_github
fi

if [ "$vpn_flag" = true ]; then
    connect_vpn
fi

if [ "$restart_flag" = false ]; then
    printf "Starting bot in directory: ${bot_directory}\n"
    get_ip
    python3 ${bot_directory}main_driver.py
    printf 'Started bot. Running python3 processes:\n'
    ps -ef | grep python3
    printf 'End of script.\n'
fi
