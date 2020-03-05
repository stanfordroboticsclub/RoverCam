sudo apt-get install -y libhdf5-dev libhdf5-serial-dev
sudo apt-get install -y libqtwebkit4 libqt4-test
sudo apt-get install -y libatlas-base-dev libjasper-dev libqtgui4 python3-pyqt5

#might also need libavformat58 libswscale5

# second has more modules
# yes | sudo pip3 install opencv-python
# yes | sudo pip3 install opencv-contrib-python #needs to force version as newest version has issues
yes | pip install opencv-contrib-python==4.1.0.25
yes | sudo pip3 install imutils
