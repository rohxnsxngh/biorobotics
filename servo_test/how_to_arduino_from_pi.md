This markdown file details the process of controlling a servo using an Arduino controlled by a Raspberry Pi

# install necessary packages (pi)
```bash
sudo apt update
sudo apt install python3-serial
sudo apt update
sudo apt install vim

```

# install arduino-cli
```bash
wget https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_ARM64.tar.gz
tar -xvf arduino-cli_latest_Linux_ARM64.tar.gz
sudo mv arduino-cli /usr/local/bin/

# check correct installation by running
arduino-cli version
```

# setting up arduino sketch
created servo_test.ino
```bash
# install necessary libraries
arduino-cli lib install "Servo"
```

```bash
# how to compile
arduino-cli compile --fqbn arduino:avr:uno .
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno
```

# checking connected boards (optional)
```bash
 arduino-cli board list
```


# sendiung test angle from pi
```bash
python3 control_servo.py
```







