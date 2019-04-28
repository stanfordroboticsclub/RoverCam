args=("$@")

if [ "$#" -ne 1 ]; then
    echo "Need exactly one parameter: camera mDNS name"
    exit 2
fi


rgx_ip="inet (10\.0\.0\.[0-9]+)"
rgx_ip_any="([0-9]+\.[0-9]+\.[0-9]+\.([0-9]+))"

# port="500${args[0]}"
# ip_pi="10.0.0.2${args[0]}"

cam_launch_hi="gst-launch-1.0 rpicamsrc preview=false bitrate=2000000 sensor-mode=5 \
! 'video/x-h264,width=1280,height=720,framerate=45/1,profile=high' "

cam_launch_med="gst-launch-1.0 rpicamsrc preview=false bitrate=1000000 sensor-mode=6 \
! 'video/x-h264,width=640,height=480,framerate=45/1,profile=high' "


function finish {
  pkill -P $$
  echo "finish"
}

trap finish EXIT


echo "using port ${port}..."

cmd_ip=$(ifconfig)

if [[ $cmd_ip =~ $rgx_ip ]]
    then
        ip_viewer="${BASH_REMATCH[1]}"
        echo "detected viewer machine IP address: ${ip_viewer}"    # concatenate strings
    else
        echo "failed to retrieve viewer IP address"
        exit 1
fi

cmd_resolve=$(avahi-resolve --name ${args[0]})
if [[ $cmd_resolve =~ $rgx_ip_any ]]
    then
        ip_pi="${BASH_REMATCH[1]}"
        port="${BASH_REMATCH[2]}"
        echo "detected pi camera IP address: ${ip_pi}"    # concatenate strings
    else
        echo "failed to resolve pi's IP address"
        exit 1
fi


gst-launch-1.0 udpsrc port=${port} ! gdpdepay ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink sync=false &


cam_launch_suffix=" ! h264parse ! queue ! rtph264pay pt=96 ! gdppay ! udpsink host=${ip_viewer} port=$port"

cam_launch="${cam_launch_med}${cam_launch_suffix}"

ssh -t pi@${ip_pi} ${cam_launch}