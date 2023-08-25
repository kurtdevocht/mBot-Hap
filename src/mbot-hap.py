import math
import pygame
import sys
import time
import socket
import struct

# Game state
game_start_time = 0
game_getready_time = 3
game_play_time = 100
game_max_time = 300
game_min_time = 20
game_controls_allowed = False


# Multicast group IP and port
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

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

# Initialize pygame
pygame.init()

# Load the avatar images into a list
image_paths = ["resources/dragon_800x800.jpg", "resources/panda_800x800.jpg", "resources/turtle_800x800.jpg", "resources/unicorn_800x800.jpg"]
images = [pygame.image.load(path) for path in image_paths]

# Get screen dimensions
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h
screen_right_mid = screen_height + (screen_width - screen_height) // 2

# Create a function to scale the image
def scale_image(image):
    img_width, img_height = image.get_size()
    aspect_ratio = img_width / img_height
    new_width = int(screen_height * aspect_ratio)
    new_height = screen_height
    return pygame.transform.scale(image, (new_width, new_height))

# Scale all the images
scaled_images = [scale_image(image) for image in images]

# Set up the screen to be fullscreen
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

# Load and set up your font
pygame.font.init()
font_controls = pygame.font.SysFont("Consolas", 20)
font_time = pygame.font.SysFont("Consolas", 76)

# Keep track of the current image index
current_image_index = 0

# Main loop
while True:

    time_elapsed = time.time() - game_start_time
    game_controls_allowed = (time_elapsed > game_getready_time) and (time_elapsed < (game_getready_time + game_play_time))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:  # Pressing the esc key will quit the program
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_a:  # Change the image when 'a' is pressed
                current_image_index = (current_image_index + 1) % len(scaled_images)
            elif event.key == pygame.K_t:
                game_play_time += 10
                if game_play_time > game_max_time:
                    game_play_time = game_min_time
                message = ('TIME' + str(game_play_time)).encode('ascii')
                sock.sendto(message, (MCAST_GRP, MCAST_PORT))
            elif event.key == pygame.K_s:
                message = 'START'.encode('ascii')
                sock.sendto(message, (MCAST_GRP, MCAST_PORT))


    try:
        data, addr = sock.recvfrom(1024)
        print(f"Received {data} from {addr}")
        message = data.decode('ascii')
        if message.startswith('TIME'):
            game_play_time = int(message[4:])
        elif message == 'START':
            game_start_time = time.time()
    except BlockingIOError:
        # This exception will be raised if no data is available
        # You can continue doing other tasks here
        pass

    screen.fill((0, 0, 0))
    text_controls = font_controls.render("ESC: Quit\nS:Start\nA: Avatar\nT: Time+10 (" + str(game_play_time) + ")", True, (200, 200, 200)) 
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

    # Get the current image's width to calculate x_offset
    current_img_width = scaled_images[current_image_index].get_width()
    x_offset = max((current_img_width - screen_width) // 2, 0)

    # Draw the current scaled image
    screen.blit(scaled_images[current_image_index], (-x_offset, 0))

    # Draw the text
    # You can change the position to wherever you want the text to appear on the screen
    screen.blit(text_controls, (screen_right_mid - text_controls.get_width() // 2, screen.get_height() - text_controls.get_height() - 60))
    screen.blit(text_time, (screen_right_mid - text_time.get_width() // 2, screen.get_height() * 0.39 - text_time.get_height()/2 ))

    pygame.display.flip()
