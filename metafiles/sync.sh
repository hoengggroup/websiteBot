#!/bin/bash
echo "clonging git now"
git clone git@github.com:niklasbogensperger/websiteBot.git temp
rsync -av temp/ oldShatterhand/oldShatterhand/
rm -rf temp/

echo "Current IP is:"
curl https://ipinfo.io/ip
