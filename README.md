# mBot-Hap
## About
With **mBot-Hap** you can steer an [mBot robot](https://www.makeblock.com/pages/mbot-robot-kit) with a gamepad for a specified amount of time. This allows you to set up games where the robot needs to do some tasks while the clock is ticking ⏳.

If you're rich, you can set up up to 4 laptops (each connected to an mBot and game controller) in the same network, so you can play together! The clock and game time will automatically be synchronised.
## What you need
- A computer. It's not tested on non-Windows computers, but it might work... 
- An mBot with a 2.4GHz-dongle (or coding skills to make this code work with a bluetooth version, or with another type of robot)
- A usb game controller like [this one](https://www.kabelshop.nl/Gembird-Controller-pc-Gembird-2-controllers-USB-Vibratie-D-pad-10-knoppen-2-joysticks-JPD-UDV2-01-i24279-t1437173.html) (or coding skills to make it work with other controllers)
## Get it running
- Download this repository as a zip file, **unblock** the zip file and extract it
- Install [Python 3.11](https://www.python.org/)
- Install the following Python libraries:
```
pip install cython
pip install pyserial
pip install hidapi
pip install pygame 
```
- **NOTE** - @2023-11-07 installing the *hidapi* library failed when using Python 3.12. On Python 3.11 it works...
- **NOTE** - On Windows, pip.exe is usually installed in *C:\Users\YourUserName\AppData\Local\Programs\Python\Python311\Scripts\pip.exe* (change *YourUserName* and Python version) and might be added to the path. If pip is not recognized, add its folder to your PATH environment variable, or adapt and run the helper script **install_libs.bat**
- Connect the game controller and the mBot 2.4GHz dongle
- Run **mbot-hap.py**:
```
python mbot-hap.py
```
- **NOTE** - On Windows, python.exe is usually installed in *C:\Users\YourUserName\AppData\Local\Programs\Python\Python312\python.exe* (change *YourUserName* and Python version) and might be added to the path. If python is not recognized, add its folder to your PATH environment variable, or adapt and run the helper script **run.bat**

## Create a network
If you want to play together, a seperate computer is needed for each mBot. On each laptop the installation procedure needs to be repeated.

UDP multicasting is used to synchronise the computers. Fot this, the computers need to be on the same network. This does not work on all networks, so a dedicated router or hotspot might be needed. An internet connection is not necessary.

**Nerd-tip:** I'ts quite easy to hack the game by intercepting the broadcasted UDP messages 🤓
## Controlling the game
Keyboard keys:
- **ESC** - Didn't you like the game?
- **A** - Selects the game avatar. The leds on the mBot will get a corresponding color
- **T** - Set the game time
- **S** - Start the game

Only while the clock is running, the mBot can be moved with the game controller.

Game controller:
- **Button '1'** - Play the avatar sound
- **Button 'Select'** - Switch steering mode
- **Joysticks** - Drive the mBot (depending on the steering mode)

**MEGA-TIP** - Turn on the **Analog**-mode of the usb controller for smoother steering.