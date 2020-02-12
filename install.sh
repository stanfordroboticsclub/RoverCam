#!/usr/bin/env sh

FOLDER=$(dirname $(realpath "$0"))
cd $FOLDER

# if you want to use a rpi camera you need to enable it in raspi-config
#. raspi-config nonint
#do_camera 1

python3 setup.py clean --all install

yes | sudo apt-get install \
gstreamer1.0-tools gstreamer1.0-plugins-bad gstreamer1.0-plugins-good libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev

# sudo apt install -y autoconf automake libtool pkg-config
# gst-rpicamsrc-master is no longer needed! (building to from scratch broke often
# wget https://github.com/thaytan/gst-rpicamsrc/archive/master.zip
# unzip master.zip
# cd gst-rpicamsrc-master
# sudo bash ./autogen.sh --prefix=/usr --libdir=/usr/lib/arm-linux-gnueabihf/
# sudo make
# sudo make install
# cd ..

# installs opencv
sudo bash install_cv.sh

for file in *.service; do
    [ -f "$file" ] || break
    sudo ln -s $FOLDER/$file /lib/systemd/system
done

sudo systemctl daemon-reload
