"""Resizable-window and fullscreen support for The Cosmic Clinic."""

import pygame

from gui_theme import WINDOW_SIZE


MIN_WINDOW_SIZE = (770, 455)
MAX_INITIAL_SCALE = 1.5


class DisplayMixin:
    """Scale the fixed game canvas into a resizable, letterboxed window."""

    def setup_display(self):
        """Create a large window while preserving the game's logical canvas."""

        self.fullscreen = False
        self.windowed_size = self.get_initial_window_size()
        self.window = pygame.display.set_mode(
            self.windowed_size,
            pygame.RESIZABLE,
        )
        self.screen = pygame.Surface(WINDOW_SIZE).convert()
        self.display_viewport = pygame.Rect((0, 0), WINDOW_SIZE)
        self.update_display_viewport()

    def get_initial_window_size(self):
        """Return a large window that still fits comfortably on the desktop."""

        desktop_sizes = pygame.display.get_desktop_sizes()
        desktop_width, desktop_height = (
            desktop_sizes[0] if desktop_sizes else WINDOW_SIZE
        )
        usable_width = desktop_width * 0.9
        usable_height = desktop_height * 0.86
        scale = min(
            MAX_INITIAL_SCALE,
            usable_width / WINDOW_SIZE[0],
            usable_height / WINDOW_SIZE[1],
        )
        scale = max(0.5, scale)
        return (
            round(WINDOW_SIZE[0] * scale),
            round(WINDOW_SIZE[1] * scale),
        )

    def resize_display(self, size):
        """Apply a user-requested window size with a practical minimum."""

        if self.fullscreen:
            return
        width = max(MIN_WINDOW_SIZE[0], size[0])
        height = max(MIN_WINDOW_SIZE[1], size[1])
        self.windowed_size = (width, height)
        self.window = pygame.display.set_mode(
            self.windowed_size,
            pygame.RESIZABLE,
        )
        self.update_display_viewport()

    def toggle_fullscreen(self):
        """Toggle borderless desktop fullscreen with F11."""

        previous_size = self.windowed_size
        try:
            if self.fullscreen:
                self.window = pygame.display.set_mode(
                    previous_size,
                    pygame.RESIZABLE,
                )
                self.fullscreen = False
            else:
                self.windowed_size = self.window.get_size()
                self.window = pygame.display.set_mode(
                    (0, 0),
                    pygame.FULLSCREEN,
                )
                self.fullscreen = True
        except pygame.error:
            self.window = pygame.display.set_mode(
                previous_size,
                pygame.RESIZABLE,
            )
            self.windowed_size = previous_size
            self.fullscreen = False
        self.update_display_viewport()

    def update_display_viewport(self):
        """Center the original aspect ratio inside the current window."""

        window_width, window_height = self.window.get_size()
        scale = min(
            window_width / WINDOW_SIZE[0],
            window_height / WINDOW_SIZE[1],
        )
        render_width = max(1, round(WINDOW_SIZE[0] * scale))
        render_height = max(1, round(WINDOW_SIZE[1] * scale))
        self.display_viewport = pygame.Rect(
            (window_width - render_width) // 2,
            (window_height - render_height) // 2,
            render_width,
            render_height,
        )

    def present_frame(self):
        """Scale and display the finished logical frame with letterboxing."""

        self.window.fill((3, 7, 12))
        if self.display_viewport.size == WINDOW_SIZE:
            scaled_frame = self.screen
        else:
            scaled_frame = pygame.transform.smoothscale(
                self.screen,
                self.display_viewport.size,
            )
        self.window.blit(scaled_frame, self.display_viewport.topleft)
        pygame.display.flip()

    def window_to_game_position(self, position):
        """Translate a physical-window position into logical game coordinates."""

        if not self.display_viewport.collidepoint(position):
            return (-10000, -10000)
        logical_x = (
            (position[0] - self.display_viewport.x)
            * WINDOW_SIZE[0]
            / self.display_viewport.width
        )
        logical_y = (
            (position[1] - self.display_viewport.y)
            * WINDOW_SIZE[1]
            / self.display_viewport.height
        )
        return (int(logical_x), int(logical_y))

    def game_to_window_position(self, position):
        """Translate logical coordinates for tests and display integrations."""

        window_x = self.display_viewport.x + (
            position[0] * self.display_viewport.width / WINDOW_SIZE[0]
        )
        window_y = self.display_viewport.y + (
            position[1] * self.display_viewport.height / WINDOW_SIZE[1]
        )
        return (round(window_x), round(window_y))

    def get_mouse_position(self):
        """Return the mouse in logical coordinates for hover effects."""

        return self.window_to_game_position(pygame.mouse.get_pos())

    def get_fullscreen_hint(self):
        """Return the appropriate F11 action for the footer."""

        return "F11 windowed" if self.fullscreen else "F11 fullscreen"
