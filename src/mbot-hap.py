from lib.mBot import *
import math
import pygame
import sys
import time
import socket
import struct

def findJoystick():
        joystick_count = pygame.joystick.get_count()
        if joystick_count == 0:
                print("No joystick detected :-(")
                print("Connect a joystick or game controller and start again...")
                return None

        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        print( "Yes! I found " + str(joystick_count) + " joystick" + ("" if joystick_count == 1 else "s"))
        print( "I will use this one: '" + joystick.get_name() + "'")
        return joystick

def findMBot():
    try:
        bot = mBot()
        bot.startWithHID()
        return bot
    except Exception as err:
        print(f"Could not initialize mBot {err=}, {type(err)=}")
        print("Insert a 2.4GHz-dongle, turn on the mBot and start again...")
        return None

def scaleImage(image):
    img_width, img_height = image.get_size()
    aspect_ratio = img_width / img_height
    new_width = int(screen_height * aspect_ratio)
    new_height = screen_height
    return pygame.transform.scale(image, (new_width, new_height))

def loadAvatarImages():
    image_paths = [
        "resources/dragon_800x800.jpg",
        "resources/panda_800x800.jpg",
        "resources/turtle_800x800.jpg",
        "resources/unicorn_800x800.jpg"]
    return [pygame.image.load(path) for path in image_paths]
    
def openSocket():
     # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Set the time-to-live for messages to 1 so they don't go past the local network segment
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', 1))
    sock.setblocking(0)

    # Bind to the server address
    sock.bind(('', MCAST_PORT))

    # Tell the operating system to add the socket to the multicast group on all interfaces
    group = socket.inet_aton(MCAST_GRP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    return sock

# Credits to https://www.instructables.com/Joystick-to-Differential-Drive-Python/
def joystickToDiff(x, y, minJoystick, maxJoystick, minSpeed, maxSpeed):
    # If x and y are 0, then there is not much to calculate...
	if x == 0 and y == 0:
		return (0, 0)
    
	# First Compute the angle in deg
	# First hypotenuse
	z = math.sqrt(x * x + y * y)

	# angle in radians
	rad = math.acos(math.fabs(x) / z)

	# and in degrees
	angle = rad * 180 / math.pi

	# Now angle indicates the measure of turn
	# Along a straight line, with an angle o, the turn co-efficient is same
	# this applies for angles between 0-90, with angle 0 the coeff is -1
	# with angle 45, the co-efficient is 0 and with angle 90, it is 1

	tcoeff = -1 + (angle / 90) * 2
	turn = tcoeff * math.fabs(math.fabs(y) - math.fabs(x))
	turn = round(turn * 100, 0) / 100

	# And max of y or x is the movement
	mov = max(math.fabs(y), math.fabs(x))

	# First and third quadrant
	if (x >= 0 and y >= 0) or (x < 0 and y < 0):
		rawLeft = mov
		rawRight = turn
	else:
		rawRight = mov
		rawLeft = turn

	# Reverse polarity
	if y < 0:
		rawLeft = 0 - rawLeft
		rawRight = 0 - rawRight

	# minJoystick, maxJoystick, minSpeed, maxSpeed
	# Map the values onto the defined rang
	rightOut = map(rawRight, minJoystick, maxJoystick, minSpeed, maxSpeed)
	leftOut = map(rawLeft, minJoystick, maxJoystick, minSpeed, maxSpeed)

	return (rightOut, leftOut)

def map(v, in_min, in_max, out_min, out_max):
	# Check that the value is at least in_min
	if v < in_min:
		v = in_min
	# Check that the value is at most in_max
	if v > in_max:
		v = in_max
	return (v - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

# Constants for the usb game controller
AXIS_GAMEPAD_JOYLEFT_UPDOWN = 1
AXIS_GAMEPAD_JOYLEFT_LEFTRIGHT = 0
BUTTON_GAMEPAD_RIGHT_THUMB_1 = 0

# Networking / multicating
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

# Game state
game_start_time = 0
game_getready_time = 3
game_play_time = 100
game_max_time = 300
game_min_time = 20
game_controls_allowed = False # True if it's ok to control the mBot
game_button_released = False # True if the button was released (to detect edges)
game_avatar_index = 0

if __name__ == '__main__':

    # Load the avatar images into a list
    avatar_images = loadAvatarImages()

    # Create a UDP socket
    sock = openSocket()

    # Initialize PyGame & joystick
    pygame.init()
    pygame.joystick.init()
    joystick = findJoystick()

    axis_throttle = AXIS_GAMEPAD_JOYLEFT_UPDOWN
    axis_turn = AXIS_GAMEPAD_JOYLEFT_LEFTRIGHT
    button_sound = BUTTON_GAMEPAD_RIGHT_THUMB_1
    sound_paths = ["resources/dragon.wav", "resources/panda.wav", "resources/turtle.wav", "resources/unicorn.wav"]

    # Set up the screen to be fullscreen
    #screen = pygame.display.set_mode((1200, 600))
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    screen_height = screen_info.current_h
    screen_right_mid = screen_height + (screen_width - screen_height) // 2

    # Scale all the images
    scaled_images = [scaleImage(image) for image in avatar_images]

    # Create fonts
    pygame.font.init()
    font_controls = pygame.font.SysFont("Consolas", 20)
    font_time = pygame.font.SysFont("Consolas", 76)

    # Load sounds
    sound_attention = pygame.mixer.Sound("resources/attention.wav")
    sound_plingplong = pygame.mixer.Sound("resources/plingplong.wav")
    sound_gameover = pygame.mixer.Sound("resources/gameover.wav")
    last_sound = ""

    # Connect with the mBot
    bot = findMBot()

    # Main loop
    while True:

        time_elapsed = time.time() - game_start_time
        game_controls_allowed = (time_elapsed > game_getready_time) and (time_elapsed < (game_getready_time + game_play_time))
        sound_toet = pygame.mixer.Sound(sound_paths[game_avatar_index])

        # Process PyGame events
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.KEYDOWN:
            
                # ESC => Quit game
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            
                # A => Next avatar
                elif event.key == pygame.K_a:
                    game_avatar_index = (game_avatar_index + 1) % len(scaled_images)
                    sound_toet = pygame.mixer.Sound(sound_paths[game_avatar_index])
                    pygame.mixer.Sound.play(sound_toet)
            
                # T => Add 10 seconds to game time & broadcast new game time
                elif event.key == pygame.K_t:
                    game_play_time += 10
                    if game_play_time > game_max_time:
                        game_play_time = game_min_time
                    message = ('TIME' + str(game_play_time)).encode('ascii')
                    sock.sendto(message, (MCAST_GRP, MCAST_PORT))
            
                # S => Start the game & broadcast start event
                elif event.key == pygame.K_s:
                    message = 'START'.encode('ascii')
                    sock.sendto(message, (MCAST_GRP, MCAST_PORT))
        
        # Process incoming network messages (if any)
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Received {data} from {addr}")
            message = data.decode('ascii')
            if message.startswith('TIME'):
                game_play_time = int(message[4:])
            elif message == 'START':
                game_start_time = time.time()
        # This exception will be raised if no data is available
        except BlockingIOError:
            pass

        # Clear the screen
        screen.fill((0, 0, 0))

        # Render the instructions
        text_controls = font_controls.render("ESC: Quit | S:Start | A: Avatar | T: Time+10 (" + str(game_play_time) + "s)", True, (200, 200, 200)) 
        screen.blit(text_controls, (screen_right_mid - text_controls.get_width() // 2, screen.get_height() - text_controls.get_height() - 60))

        # Render the game text & progress bar
        
        game_controls_allowed = False
        if time_elapsed < game_getready_time:
            if last_sound != "READY":
                last_sound = "READY"
                sound_plingplong.play()
            text_time_text = 'Get ready...'
        elif time_elapsed < (game_getready_time + game_play_time):
            if last_sound != "GO":
                last_sound = "GO"
                sound_attention.play()
            game_controls_allowed = True
            text_time_text = 'GO!'
            percent_played = (time_elapsed - game_getready_time) / game_play_time
            start_angle = math.pi/2 - percent_played * 2 * math.pi
            end_angle = math.pi/2
            arc_r = 200
            arc_w = 50
            arc_rect = (screen_right_mid - arc_r, screen.get_height() * 0.39 - arc_r, 2*arc_r, 2*arc_r)
            pygame.draw.arc(screen, (64, 64, 64), arc_rect, 0, 2 * math.pi, arc_w)
            pygame.draw.arc(screen, (255, 128, 0), arc_rect, start_angle, end_angle, arc_w)
        else:
            if last_sound != "GAMEOVER":
                last_sound = "GAMEOVER"
                sound_gameover.play()
            text_time_text = 'Game Over!'
        text_time = font_time.render(text_time_text, True, (128, 255, 0))
        screen.blit(text_time, (screen_right_mid - text_time.get_width() // 2, screen.get_height() * 0.39 - text_time.get_height()/2 ))

        # Render the avater image
        current_img_width = scaled_images[game_avatar_index].get_width()
        x_offset = max((current_img_width - screen_width) // 2, 0)
        screen.blit(scaled_images[game_avatar_index], (-x_offset, 0))

        # Update the screen
        pygame.display.flip()
       
        motor_out = (0, 0) 
        if (joystick is not None) and game_controls_allowed:

            # Button not pushed? Remember it! Than you're allowed to play a sound once the button is pushed
            if( joystick.get_button(button_sound) == 0 ):
                    game_button_released = True
            else:
                    # The button is pushed => Only play a new sound if it was not yet pushed before
                    if( game_button_released ):
                            pygame.mixer.Sound.play(sound_toet)
                    game_button_released = False

            # Calculate the sped of each wheel
            throttle = -joystick.get_axis(axis_throttle)
            turn = -joystick.get_axis(axis_turn)
            motor_out = joystickToDiff(turn, throttle, -1.0, 1.0, -255, 255)

            print( "throttle: " + str(throttle) + " -- turn: " + str(turn) + " => left: " + str(motor_out[0]) + " -- right: " + str(motor_out[1]))

        if (bot is not None):
             # Send the speeds to the mBot / mBoot
            bot.doMove( (int)(motor_out[0]), (int)(motor_out[1]))  
           