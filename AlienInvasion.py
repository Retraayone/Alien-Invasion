import sys
from time import sleep

import pygame
import random
from settings import Settings
from game_stats import GameStats
from button import Button
from scoreboard import Scoreboard
from ship import Ship
from bullet import Bullet
from alien import Alien
from star import Star  # Import the Star class

class AlienInvasion:
    """Overall class to manage game assets and behaviour."""

    def __init__(self):
        """Initializing the game and create game resources"""
        pygame.init()
        
        self.game_active = False  # Start the game in an inactive state
        self.paused = False  # Add a paused state
        self.clock = pygame.time.Clock()
        self.settings = Settings()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height
        pygame.display.set_caption("Alien Invasion")

        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.stars = pygame.sprite.Group()  # Create a group to hold stars

        self._create_fleet()
        self._create_stars()  # Create stars
        # Create an instance to store game statistics
        self.stats = GameStats(self)
        # Make the play button
        self.play_button = Button(self, "Play")
        # Create an instance to store the scoreboard
        self.sb = Scoreboard(self)

        # Initialize the mixer
        pygame.mixer.init()

        # Load sounds
        self.background_music = pygame.mixer.Sound('assets/sounds/background_music.mp3')
        self.laser_shot_sound = pygame.mixer.Sound('assets/sounds/laser_shot.wav')
        self.enemy_hit_sound = pygame.mixer.Sound('assets/sounds/enemy_hit.wav')
        self.game_over_sound = pygame.mixer.Sound('assets/sounds/game_over.wav')

        # Set volume for background music
        self.background_music.set_volume(0.1)  # Set volume to 20%

        # Play background music in a loop
        self.background_music.play(loops=-1)

    def run_game(self):
        """Start the main loop for the game"""
        while True:
            self._check_events()
            if self.game_active and not self.paused:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()  # Update aliens' positions
            self.update_screen()
            self.clock.tick(144)  # Limit frame rate to 60 FPS

    def _check_events(self):
        """Respond to keypresses and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_keydown_events(self, event):
        """Respond to keypresses."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit()
        elif event.key == pygame.K_SPACE:
            self._fire_bullets()
        elif event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
            self._toggle_pause()  # Toggle pause state

    def _toggle_pause(self):
        """Toggle the game's paused state."""
        self.paused = not self.paused
        if self.paused:
            pygame.mixer.pause()  # Pause all sounds
        else:
            pygame.mixer.unpause()  # Unpause all sounds

    def _check_keyup_events(self, event):
        """Respond to key releases."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False

    def _check_play_button(self, mouse_pos):
        """Start a new game when the player clicks Play."""
        if self.play_button.rect.collidepoint(mouse_pos) and not self.game_active:
            # Reset the game settings.
            self.settings.initialize_dynamic_settings()
            # Reset the game statistics.
            self.stats.reset_stats()
            self.game_active = True
            # Hide the mouse cursor.
            pygame.mouse.set_visible(False)

            # Get rid of any remaining bullets and aliens.
            self.bullets.empty()
            self.aliens.empty()

            # Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()

            # Reset the scoreboard images.
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

    def _fire_bullets(self):
        """Create a new bullet and add it to the bullets group."""
        if len(self.bullets) < self.settings.bullets_allowed:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)
            self.laser_shot_sound.play()  # Play laser shot sound

    def _update_bullets(self):
        """Update position of bullets and get rid of old bullets."""
        # Update bullet positions.
        self.bullets.update()

        # Get rid of bullets that have disappeared.
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)
        
        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Respond to bullet-alien collisions."""
        # Remove any bullets and aliens that have collided.
        collisions = pygame.sprite.groupcollide(
            self.bullets, self.aliens, True, True)
        
        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
                self.enemy_hit_sound.play()  # Play enemy hit sound

            self.sb.prep_score()
            self._check_high_score()

        if not self.aliens:
            # Destroy existing bullets and create new fleet.
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()

            # Increase level.
            self.stats.level += 1
            self.sb.prep_level()

    def _check_high_score(self):
        """Check to see if there's a new high score."""
        if self.stats.score > self.stats.high_score:
            self.stats.high_score = self.stats.score
            self.sb.prep_high_score()

    def _create_fleet(self):
        """Create a fleet of aliens"""
        # Make an Alien.
        # Spacing between aliens is one alien width and one alien height.
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        current_x, current_y = alien_width, alien_height
        max_rows = (self.settings.screen_height - 3 * alien_height) // (2 * alien_height) - 5  # Adjust to remove one more row
        while current_y < (max_rows * 2 * alien_height):
            while current_x < (self.settings.screen_width - 2 * alien_width):
                self._create_alien(current_x, current_y)
                current_x += 2 * alien_width
            # Finished a row; reset x value, and increment y value.
            current_x = alien_width
            current_y += 2 * alien_height

    def _create_alien(self, x_position, y_position):
        """Create an alien and place it in the fleet"""
        new_alien = Alien(self)
        new_alien.x = x_position
        new_alien.rect.x = x_position
        new_alien.rect.y = y_position
        self.aliens.add(new_alien)

    def _update_aliens(self):
        """Check if the fleet is at an edge, then update positions."""
        self._check_fleet_edges()
        self.aliens.update()
        # Look for alien-ship collisions.
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()
            print("ship hit!!!")

        # Look for aliens hitting the bottom of the screen.
        self._check_aliens_bottom()
            

    def _check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Drop the entire fleet and change the fleet's direction."""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _check_aliens_bottom(self):
        """Check if any aliens have reached the bottom of the screen."""
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= self.screen.get_rect().bottom:
                # Treat this as if the ship got hit.
                self._ship_hit()
                break

    def _create_stars(self):
        """Create a group of stars to scatter in the background."""
        for _ in range(10):  # Adjust the number of stars as needed
            star = Star(self)
            star.rect.x = random.randint(0, self.settings.screen_width)  # Scatter stars across the entire width
            star.rect.y = random.randint(0, self.settings.screen_height)
            self.stars.add(star)

    def _ship_hit(self):
        """Respond to the ship being hit by an alien"""
        if self.stats.ships_left > 0:
            # Decrement ships left.
            self.stats.ships_left -= 1
            # Get rid of any remaining bullets and aliens.
            self.bullets.empty()
            self.aliens.empty()
            # Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()
            # Pause.
            sleep(0.5)
            # Update scoreboard.
            self.sb.prep_ships()
        else:
            self.game_active = False
            pygame.mouse.set_visible(True)
            self.game_over_sound.play()  # Play game over sound

    def update_screen(self):
        """Update images and flip to the new screen."""
        self.screen.fill(self.settings.bg_color)
        self.stars.draw(self.screen)  # Draw the stars
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        self.ship.blitme()
        self.aliens.draw(self.screen)
        # Draw the play button if the game is inactive.
        if not self.game_active:
            self.play_button.draw_button()
        # Draw the score information.
        self.sb.show_score()
        # Display pause message if the game is paused.
        if self.paused:
            self._show_pause_message()
        pygame.display.flip()

    def _show_pause_message(self):
        """Display a pause message on the screen."""
        font = pygame.font.SysFont(None, 74)
        pause_message = font.render("Paused", True, (255, 255, 255))
        pause_rect = pause_message.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(pause_message, pause_rect)

if __name__ == '__main__':
    # Make an instance and run the game
    ai = AlienInvasion()
    ai.run_game()