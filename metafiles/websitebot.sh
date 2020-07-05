#!/usr/bin/env bash

restart_flag=false
github_flag=false
vpn_flag=false
directory_flag=false
temp_directory='/home/bot/temp/'
vpn_directory='/etc/openvpn/ovpn_tcp/'
vpn_suffix='.tcp443.ovpn'
bot_directory='/home/bot/websitebot/websiteBot/'
help_text="\
You probably want to clone the source from GitHub and restart the systemctl service:
$(basename "$0") -r -g

Usage: $(basename "$0") [-r] [-g] [-v VPN_PATTERN] [-d BOT_DIRECTORY]
  start the bot using python3.8 (primarily for the systemctl service)

Disallowed combination of options:
  -r with anything except -g

Options:
  -r                  restart the bot's systemctl service instead of starting the bot directly
                      (primarily for manual intervention)
  -g                  clone the bot's code from GitHub before (re-)starting
  -v <VPN_PATTERN>    connect to VPN before starting the bot using a configuration matching VPN_PATTERN
  -d <BOT_DIRECTORY>  start the bot from the specified directory
                      (defaults to '/home/pi/oldShatterhand/oldShatterhand/')
  -h                  display this help text
"

print_usage() {
    printf "$help_text"
}

get_ip() {
    printf "The current IP address is: $(curl --silent https://icanhazip.com/)\n"
}

restart_bot() {
    printf 'Stopping websitebot service...\n'
    sudo systemctl stop websitebot.service
    printf 'websitebot service stopped.\n'
    if [ "$github_flag" = true ]; then
        sync_github
    fi
    printf 'Restarting websitebot service. Wait for output of service status.\n'
    sudo systemctl start websitebot.service
    sleep 2
    systemctl status websitebot.service
}

sync_github() {
    printf 'Cloning from GitHub.\n'
    git clone git@github.com:hoengggroup/websiteBot.git $temp_directory
    rsync -av $temp_directory $bot_directory
    rm -rf $temp_directory
    printf 'Successfully cloned from GitHub.\n'
}

connect_vpn() {
    printf 'Modifying ip tables to allow incoming connections via non-vpn interface.\n'
    sudo ip rule add from $(ip route get 1 | grep -Po '(?<=src )(\S+)') table 128
    sudo ip route add table 128 to $(ip route get 1 | grep -Po '(?<=src )(\S+)')/32 dev $(ip -4 route ls | grep default | grep -Po '(?<=dev )(\S+)')
    sudo ip route add table 128 default via $(ip -4 route ls | grep default | grep -Po '(?<=via )(\S+)')
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
        d) directory_flag=true
           bot_directory="${OPTARG}" ;;
        h) print_usage
           exit 0 ;;
        *) print_usage
           exit 1 ;;
    esac
done

if [ "$restart_flag" = true ]; then
    if [ "$vpn_flag" = true ]; then
        printf 'Warning: Disregarding -v option. Please do not use -v when restarting with -r, as the VPN is handled by the service when it is restarted.\n'
    fi
    if [ "$directory_flag" = true ]; then
        printf 'Warning: Disregarding -d option. Please do not use -d when restarting with -r, as the default directory is always used by the service when it is restarted.\n'
    fi
    restart_bot
    exit 0
else
    if [ "$github_flag" = true ]; then
        sync_github
    fi
    if [ "$vpn_flag" = true ]; then
        sudo pkill openvpn
        connect_vpn
    fi
    printf "Starting bot in directory: ${bot_directory}\n"
    get_ip
    cd ${bot_directory}
    python3.8 main_driver.py
fi
