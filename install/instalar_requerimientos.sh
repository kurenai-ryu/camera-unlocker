


sudo apt-get install libopencv-dev python-opencv python-dev 


sudo apt-get install python-psycopg2 -y
sudo pip install flask_restful
#http://www.pyimagesearch.com/2015/12/21/increasing-webcam-fps-with-python-and-opencv/
sudo pip install imutils
sudo pip install requests

#fix a wiring-pi python
sudo apt-get install swig2.0 -y

cd ~
git clone --recursive https://github.com/neuralpi/WiringPi-Python.git
cd WiringPi-Python/WiringPi
sudo ./build
cd ..
swig2.0 -python wiringpi.i
sudo python setup.py install
sudo python3 setup.py install