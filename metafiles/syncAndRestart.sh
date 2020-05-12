echo "stopping service..."
sudo systemctl stop websitebot.service 
echo "service stopped."
echo "clonging git now"
git clone git@github.com:niklasbogensperger/websiteBot.git temp
rsync -av temp/ oldShatterhand/oldShatterhand/
rm -rf temp/
echo "synced."

echo "Current IP is:"
curl https://ipinfo.io/ip

echo -n "Should I restart websitebot.service(y/n)? "
read answer
if [ "$answer" != "${answer#[Yy]}" ] ;then
	echo "Restarting now... please wait for status"
	sudo systemctl start websitebot.service
	sleep 2
	systemctl status websitebot.service 
fi

