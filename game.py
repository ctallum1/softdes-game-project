import sys
import pygame
from pygame.locals import *

class Game:
    # game meta functions
    def __init__(self):
        # create external pygame window
        WINDOW_SIZE = (640, 480)
        self.screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("Magma Boy and Hydro Girl")

        # create internal pygame window
        CHUNK_SIZE = 16
        DISPLAY_SIZE = (34 * CHUNK_SIZE, 25 * CHUNK_SIZE)
        self.display = pygame.Surface(DISPLAY_SIZE)

    def draw_level_screen(self, level_select, controller):
        self.display.blit(level_select.screen, (0, 0))

        for level in range(5):
            image = level_select.titles[level+1]
            self.display.blit(image, ((self.display.get_width() - image.get_width())/2, 50*level + 100))

        
        self.display.blit(level_select.left_player, (50, 150))
        self.display.blit(level_select.right_player, (430, 150))    

    def user_select_level(self, level_select, controller):
        level_index = 0
        while True:
            events = pygame.event.get()
            if controller.press_key(events, K_DOWN):
                level_index += 1
                if level_index == 5:
                    level_index = 0
            if controller.press_key(events, K_UP):
                level_index -= 1
                if level_index == -1:
                    level_index = 4
            self.draw_level_screen(level_select, controller)
            self.draw_level_select_indicator(level_select, level_index)
            level_dict = {
                0: "level1",
                1: "level2",
                2: "level3",
                3: "level1",
                4: "level1"
            }
            if controller.press_key(events, K_RETURN):
                return level_dict[level_index]
            
    def draw_level_select_indicator(self, level_select, level_index):
        location_x = (self.display.get_width() - level_select.indicator_image.get_width())/2
        location_y = level_index*50 + 96
        indicator_location = (location_x, location_y)
        self.display.blit(level_select.indicator_image, indicator_location)
        self.refresh_window()

    def reset_game(self, players):
        """
        Moves all of the playes to the begining location.
        """
        for player in players:
            player.reset_character()

    def refresh_window(self):
        """
        Refresh and draw the game screen
        """
        new_window_size, center_cords = self.adjust_scale()
        # scale internal display to match window)
        game_disp = pygame.transform.scale(self.display, new_window_size)
        self.screen.blit(game_disp, center_cords)
        pygame.display.update()

    def adjust_scale(self):
        """
        Adjust internal screen for window scaling

        If the window size is changed, scale the game to the maximum amount
        while keeping the same aspect ratio. Also keep the game centered in the
        window.

        Returns:
            display_size::tuple (height, width)
                The updated height and width of the internal game display
            cords::tuple (x_cord, y_cord)
                The cordinates of the upper left corner of the internal game
                display so that when it is blit onto window, it is centered.
        """
        window_size = self.screen.get_size()

        # if window is longer than aspect ratio
        if window_size[0] / window_size[1] >= 1.5:
            display_size = (int(1.5 * window_size[1]), window_size[1])
        # if window is taller than aspect ratio
        else:
            display_size = (window_size[0], int(.75 * window_size[0]))
        # find cords so that display is centered
        cords = ((window_size[0] - display_size[0]) / 2,
                 (window_size[1] - display_size[1]) / 2)

        return display_size, cords

    # game mechanics

    def draw_level_background(self, board):
        """
        Draw the background of the level.

        Args:
            board::board class object
                board class object that contains information on chunk images
                and thier locations
        """
        self.display.blit(board.get_background(), (0, 0))       

    def draw_board(self, board):
        """
        Draw the board.

        Args:
            board::board class object
                board class object that contains information on chunk images
                and thier locations
        """
        # draw the full background
        board_textures = board.get_board_textures()
        # draw the solid blocks and liquids
        for y, row in enumerate(board.get_game_map()):
            for x, tile in enumerate(row):
                if tile != "0":
                    self.display.blit(
                        board_textures[f"{tile}"], (x * 16, y * 16)
                    )

    def draw_gates(self, gates):
        """
        Draw gates and buttons.
        """
        for gate in gates:
            self.display.blit(gate.gate_image, gate.gate_location)

            for location in gate.plate_locations:
                self.display.blit(gate.plate_image, location)

    def draw_doors(self, doors):
        for door in doors:
            self.display.blit(door.door_background, door.background_location)
            self.display.blit(door.door_image, door.door_location)
            self.display.blit(door.frame_image, door.frame_location)

    def draw_player(self, players):
        """
        Draw the player.

        If the player is moving right or left, draw the player as facing that
        direction.

        Args:
            player::[player object, player object]
                a list of player objects that contains movement data as well as
                different images, one for each direction it can face.
        """
        for player in players:
            if player.moving_right:
                player_image = player.side_image
            elif player.moving_left:
                player_image = pygame.transform.flip(player.side_image, True, False)
            else:
                player_image = player.image
            player_image.set_colorkey((255, 0, 255))
            self.display.blit(player_image, (player.rect.x, player.rect.y))

    def move_player(self, board, gates, players):
        for player in players:
            
            player.calc_movement()
            movement = player.get_movement()
            collision_types = {
                'top': False,
                'bottom': False,
                'right': False,
                'left': False}
            player.rect.x += movement[0]
            collide_blocks = board.get_solid_blocks()
            for gate in gates:
                collide_blocks += gate.get_solid_blocks()
            hit_list = self.collision_test(player.rect, collide_blocks)
            for tile in hit_list:
                if movement[0] > 0:
                    player.rect.right = tile.left
                    collision_types['right'] = True
                elif movement[0] < 0:
                    player.rect.left = tile.right
                    collision_types['left'] = True
            player.rect.y += movement[1]
            hit_list = self.collision_test(player.rect, collide_blocks)
            for tile in hit_list:
                if movement[1] > 0:
                    player.rect.bottom = tile.top
                    collision_types['bottom'] = True
                elif movement[1] < 0:
                    player.rect.top = tile.bottom
                    collision_types['top'] = True

            if collision_types['bottom']:
                player.y_velocity = 0
                player.air_timer = 0
            else:
                player.air_timer += 1

            if collision_types['top']:
                player.y_velocity = 0

    def check_for_death(self, board, players):
        """
        Check to see if player has falen in pool that kills them or if they are
        crushed by a gate.

        If a magma type player collides with a water pool, they die. Likewise,
        if a water type player collides with a lava pool, they die. If either
        type of player collides with a goo pool, they die.
        Args:
            board::board class object
                class object with information on board layout
            gates::gate class object
                class object with information on gate location and state
            players::[player object, player object]
                A list of player class objects.
        """
        for player in players:
            if player.get_type() == "water":
                is_killed = self.collision_test(player.rect, board.get_lava_pools())
            if player.get_type() == "magma":
                is_killed = self.collision_test(player.rect, board.get_water_pools())
            is_killed += self.collision_test(player.rect, board.get_goo_pools())

            if is_killed:
                player.kill_player()

    def check_for_gate_press(self, gates, players):
        """
        Check to see if either player is touching one of the gate buttons.
        """
        for gate in gates:
            plate_collisions = []
            for player in players:
                plate_collisions += self.collision_test(player.rect, gate.get_plates())
            if plate_collisions:
                gate.plate_is_pressed = True
            else:
                gate.plate_is_pressed = False
            gate.try_open_gate()

    def check_for_door_open(self, door, player):
        door_collision = self.collision_test(player.rect, [door.get_door()])
        if door_collision:
            door.player_at_door = True
        else:
            door.player_at_door = False
        door.try_raise_door()

    @staticmethod
    def level_is_done(doors):
        is_win = True
        for door in doors:
            if not door.is_door_open():
                is_win = False
        return is_win

    @staticmethod
    def collision_test(rect, tiles):
        """
        Create a list of tiles a pygame rect is colliding with.

        Args:
            rect::pygame.rect
                A pygame rect that may be colliding with other rects.
            tiles::[rect, rect, rect]
                A list of pygame rects. The function checks to see if the
                arguement "rect" colides with any of these "tiles".
        Returns:
            hit_list::list
                A list of all "tiles" that the argument rect is colliding with.
                If an empty list is returned, the rect is not colliding with
                any tile.
        """
        hit_list = []
        for tile in tiles:
            if rect.colliderect(tile):
                hit_list.append(tile)
        return hit_list