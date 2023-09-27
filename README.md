# Saffron-Pictures

This works best with Linux.
You can take pictures with or without the joystick

## Setup

Create a folder to clone this repository and the depthai python repository
Create a virtual environment before running install_requirement.py, this environment will be important for some settings within the script.
Create a folder called Pictures in your project directory. When starting a dataset you will be prompted for the name of the dataset and it will be saved within your directory in the Pictures folder.
You'll need to clone the depthai repository to use the OAK cameras. 


Within your project directory clone this repository
```
https://github.com/byu-crop-biomechanics-lab/Saffron-Pictures
```
Create your virtual environment within the project directory

Setup depthai within your project directory
```
git clone https://github.com/luxonis/depthai-python
cd depthai-python/utilities
python3 install_requirements.py
```

In your computer's network settings manually change your ethernet IP address to 169.254.1.50. The 50 can be set to anything from 0 to 255, except for 221 and 222 which are the OAK cameras' IP addresses.

### Gantry
1. Plug in the power supply.
2. If using the joystick plug in using the cable that plugs into the interface port on the Blackbox. Connect black to ground, yellow to TX, and green to RX. Plug the microcontroller into a power supply, I use my laptop. There is a wire from the interface cable from the Blackbox that can be used to power 5V devices but the microcontroller doesn't run well off of it.
### OAKs
1. Plug in the PoE switch.
2. Plug the ethernet cable from the PoE switch into your laptop.
3. Make sure the Oaks are plugged in and their ports have a yellow led on the top left and a yellow or green led on the top right. This LED will flash or flicker which is normal.

## Running them
### OAKs 
1. Clone the repository onto a Linux device.
2. Open the test script you plan on using
3. Start the .venv virtual environment using 
`source .venv/bin/activate`
If you have troubles connecting to the OAKs refer to this document - 
4. Click on the black screen. Any key commands you use are through that screen so click on it when you input any commands.
5. Type G to connect to camera 1. If it doesn’t connect the first time then wait 30 seconds and try again. You’ll know its connected if the screen pops up showing live video.
6. Type H to connect to camera 2 only when camera 1 is connected. It may cause a crash if you connect to camera 2 without camera 1 connected.
7. Once both are connected you can adjust any camera settings using the keyboard commands below.
8. Type C to start capturing images. You can choose to take a certain number of pictures or not in the terminal.
9. Name the folder you want your pictures to go in. When you enter your folder name the pictures will start taking. If the folder exists the program will ask you to choose another name. 
### Gantry
1. Get ready to press the start button for the program or get the joystick ready. Once you enter C in the next step the pictures will start taking. I recommend starting the gantry moving right when starting the pictures to avoid duplicate pictures
2. Type C again to stop taking pictures. Once the dataset has been taken all the pictures will be analyzed by the program. For pom poms the center of each one with a bounding box will be saved.



## Keyboard commands for the OAKs
#### Basic Camera Usage ####
* G - connect to camera 1
* H - connect to camera 2
* Q - quit the program
* C - start capturing pictures

#### Camera Settings ####
* I - increase shutter speed
* O - decrease shutter speed
* K - increase ISO
* L - decrease ISO
* A - set camera to Auto adjust mode


