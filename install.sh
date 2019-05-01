#!/usr/bin/env sh

FOLDER=$(dirname $(realpath "$0"))
cd $FOLDER

. raspi-config nonint
do_camera 1


yes | sudo apt-get install \
autoconf automake libtool pkg-config gstreamer1.0-tools gstreamer1.0-plugins-bad gstreamer1.0-plugins-good libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev

wget https://github.com/thaytan/gst-rpicamsrc/archive/master.zip
unzip master.zip
cd gst-rpicamsrc-master
./autogen.sh --prefix=/usr --libdir=/usr/lib/arm-linux-gnueabihf/
make
sudo make install


for file in *.service; do
    [ -f "$file" ] || break
    sudo ln -s $FOLDER/$file /lib/systemd/system
done

sudo systemctl daemon-reload
