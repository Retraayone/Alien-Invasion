import pygame
from pygame.sprite import Sprite
import random

class Star(Sprite):
    """A class to represent a single star in the background."""

    # Load the star image once and use it for all instances
    image = None

    def __init__(self, ai_game):
        """Initialize the star and set its starting position."""
        super().__init__()
        self.screen = ai_game.screen
        self.settings = ai_game.settings

        # Load the star image if it hasn't been loaded yet
        if Star.image is None:
            Star.image = pygame.image.load('assets/star.bmp')

        self.image = Star.image
        self.rect = self.image.get_rect()

        # Start each new star at a random position.
        self.rect.x = random.randint(0, self.settings.screen_width)
        self.rect.y = random.randint(0, self.settings.screen_height)