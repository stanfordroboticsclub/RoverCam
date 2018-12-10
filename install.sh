#!/usr/bin/env sh

FOLDER=$(dirname $(realpath "$0"))
cd $FOLDER

yes | sudo apt-get install nodejs

git clone https://github.com/131/h264-live-player.git player
cd player
yes | npm install

cd $FOLDER

for file in *.service; do
    [ -f "$file" ] || break
    sudo ln -s $FOLDER/$file /lib/systemd/system
done

sudo systemctl daemon-reload
