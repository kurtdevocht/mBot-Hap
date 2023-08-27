from lib.mBot import *
import math
import pygame
import sys
import time
import socket
import struct

def FindJoystick():
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

def FindMBot():
    try:
        bot = mBot()
        bot.startWithHID()
        return bot
    except Exception as err:
        print(f"Could not initialize mBot {err=}, {type(err)=}")
        print("Insert a 2.4GHz-dongle, turn on the mBot and start again...")
        return None

def ScaleImage(image):
    img_width, img_height = image.get_size()
    aspect_ratio = img_width / img_height
    new_width = int(screen_height * aspect_ratio)
    new_height = screen_height
    return pygame.transform.scale(image, (new_width, new_height))

def LoadAvatarImages():
    image_paths = [
        "resources/dragon_800x800.jpg",
        "resources/panda_800x800.jpg",
        "resources/turtle_800x800.jpg",
        "resources/unicorn_800x800.jpg"]
    return [pygame.image.load(path) for path in image_paths]
    
def OpenSocket():
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
    avatar_images = LoadAvatarImages()

    # Create a UDP socket
    sock = OpenSocket()

    # Initialize PyGame & joystick
    pygame.init()
    pygame.joystick.init()
    joystick = FindJoystick()

    axis_throttle = AXIS_GAMEPAD_JOYLEFT_UPDOWN
    axis_turn = AXIS_GAMEPAD_JOYLEFT_LEFTRIGHT
    button_sound = BUTTON_GAMEPAD_RIGHT_THUMB_1
    sound_paths = ["resources/dragon.wav", "resources/panda.wav", "resources/turtle.wav", "resources/unicorn.wav"]

    # Set up the screen to be fullscreen
    #screen = pygame.display.set_mode((800, 600))
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    screen_info = pygame.display.Info()
    screen_width = screen_info.current_w
    screen_height = screen_info.current_h
    screen_right_mid = screen_height + (screen_width - screen_height) // 2

    # Scale all the images
    scaled_images = [ScaleImage(image) for image in avatar_images]

    # Create fonts
    pygame.font.init()
    font_controls = pygame.font.SysFont("Consolas", 20)
    font_time = pygame.font.SysFont("Consolas", 76)

    # Connect with the mBot
    bot = FindMBot()

    # Main loop
    while True:

        time_elapsed = time.time() - game_start_time
        game_controls_allowed = (time_elapsed > game_getready_time) and (time_elapsed < (game_getready_time + game_play_time))
        toetSound = pygame.mixer.Sound(sound_paths[game_avatar_index])

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
                    toetSound = pygame.mixer.Sound(sound_paths[game_avatar_index])
                    pygame.mixer.Sound.play(toetSound)
            
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
        text_time_text = 'Game Over!'
        if time_elapsed < game_getready_time:
            text_time_text = 'Get ready...'
        elif time_elapsed < (game_getready_time + game_play_time):
            text_time_text = 'GO!'
            percent_played = (time_elapsed - game_getready_time) / game_play_time
            start_angle = math.pi/2 - percent_played * 2 * math.pi
            end_angle = math.pi/2
            arc_r = 200
            arc_w = 50
            arc_rect = (screen_right_mid - arc_r, screen.get_height() * 0.39 - arc_r, 2*arc_r, 2*arc_r)
            pygame.draw.arc(screen, (64, 64, 64), arc_rect, 0, 2 * math.pi, arc_w)
            pygame.draw.arc(screen, (255, 128, 0), arc_rect, start_angle, end_angle, arc_w)
        text_time = font_time.render(text_time_text, True, (128, 255, 0))
        screen.blit(text_time, (screen_right_mid - text_time.get_width() // 2, screen.get_height() * 0.39 - text_time.get_height()/2 ))

        # Render the avater image
        current_img_width = scaled_images[game_avatar_index].get_width()
        x_offset = max((current_img_width - screen_width) // 2, 0)
        screen.blit(scaled_images[game_avatar_index], (-x_offset, 0))

        # Update the screen
        pygame.display.flip()
       
        if (joystick is not None) and (bot is not None):

            # Button not pushed? Remember it! Than you're allowed to play a sound once the button is pushed
            if( joystick.get_button(button_sound) == 0 ):
                    game_button_released = True
            else:
                    # The button is pushed => Only play a new sound if it was not yet pushed before
                    if( game_button_released ):
                            pygame.mixer.Sound.play(toetSound)
                    game_button_released = False

            # Calculate the sped of each wheel
            speed = -joystick.get_axis(axis_throttle)
            turn = joystick.get_axis(axis_turn)

            speedLeft = speed
            if( turn < 0 ):
                    speedLeft += 2 * turn * speed

            speedRight = speed
            if( turn > 0):
                    speedRight -= 2 * turn * speed

            print( "speed: " + str(speed) + " -- turn: " + str(turn) + " => speedLeft: " + str(speedLeft) + " -- speedRight: " + str(speedRight))
            
            # Send the speeds to the mBot / mBoot
            bot.doMove( (int)(speedLeft * 255), (int)(speedRight * 255))
