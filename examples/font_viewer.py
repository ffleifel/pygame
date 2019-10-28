#!/usr/bin/env python
""" pygame.examples.font_viewer
Scroll through your system fonts from a list of surfaces or one huge buffer.

This example exhibits:
* iterate over available fonts using font.get_fonts and font.SysFont()
* scroll using virtual mouse input
* save a surface to disk
* work with a very large surface
* simple mouse and keyboard scroll speed acceleration

By default this example uses the fonts returned by pygame.font.get_fonts()
and opens them using pygame.font.SysFont().
Alternatively, you may pass a path to the command line. The TTF files found
in that directory will be used instead.

Mouse Controls:
* Click in the window to toggle scrolling. The cursor will vanish and pygame
  will enter virtual mouse mode until you click again.

Keyboard Controls:
* Press up or down to scroll 
* Press escape to exit
"""
import pygame as pg
import sys, os

use_big_surface = False  # draw into large buffer and save png file


class fontviewer:
    """
    This example is encapsulated by the fontviewer class
    It initializes the pygame window, handles input, and draws itself
    to the screen.
    """
    KEY_SCROLL_SPEED = 10

    def __init__(self, **dparams):
        pg.init()
        self.font_dir = dparams.get("folder", None)

        # create a window that uses 80 percent of the screen
        info = pg.display.Info()
        w = info.current_w
        h = info.current_h
        pg.display.set_mode((int(w * 0.8), int(h * 0.8)))
        self.font_size = h // 20

        self.clock = pg.time.Clock()
        self.y_offset = 0
        self.grabbed = False
        self.render_fonts("&N abcDEF789")

        if use_big_surface or "big" in sys.argv:
            self.render_surface()
            self.display_surface()
            self.save_png()
        else:
            self.display_fonts()

    def get_font_list(self):
        """
        Generate a font list using font.get_fonts() for system fonts or
        from a path from the command line.
        """
        path = ""
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            path = os.path.join(sys.argv[1], "")
        fonts = []
        if os.path.exists(path):
            # this list comprehension could replace the following loop
            # fonts = [f in os.listdir(path) if f.endswith('.ttf')]
            for font in os.listdir(path):
                if font.endswith(".ttf"):
                    fonts.append(font)
        return fonts or pg.font.get_fonts(), path

    def render_fonts(self, text="A display of font &N", **dparams):
        """
        Build a list that includes a surface and the running total of their
        height for each font in the font list. Store the largest width and
        other variables for later use.
        """
        font_size = dparams.get("size", 0) or self.font_size
        color = dparams.get("color", (255, 255, 255))
        self.back_color = dparams.get("back_color", (0, 0, 0))

        fonts, path = self.get_font_list()
        font_surfaces = []
        total_height = 0
        max_width = 0

        load_font = pg.font.Font if path else pg.font.SysFont

        # display instructions at the top of the display
        font = pg.font.SysFont(pg.font.get_default_font(), font_size)
        lines = (
            "Click in this window to enter scroll mode",
            "The mouse will be grabbed and hidden until you click again",
            "Foreign fonts might render incorrectly",
            "Here are your {} fonts".format(len(fonts)),
            ""  )
        for line in lines:
            surf = font.render(line, 1, color, self.back_color)
            font_surfaces.append((surf, total_height))
            total_height += surf.get_height()
            max_width = max(max_width, surf.get_width())

        # render all the fonts and store them with the total height
        for name in sorted(fonts):
            font = load_font(path + name, font_size)
            line = text.replace("&N", name)
            print(name, line, surf.get_height())
            try:
                surf = font.render(line, 1, color, self.back_color)
            except pygame.error as e:
                print(e)
                break

            max_width = max(max_width, surf.get_width())
            font_surfaces.append((surf, total_height))
            total_height += surf.get_height()

        # store variables for later usage
        self.total_height = total_height
        self.max_width = max_width
        self.font_surfaces = font_surfaces
        self.max_y = total_height - pg.display.get_surface().get_height()

    def display_fonts(self):
        """
        Display the visible fonts based on the y_offset value(updated in
        handle_events) and the height of the pygame window.
        """
        display = pg.display.get_surface()
        clock = pg.time.Clock()
        center = display.get_width() // 2

        while True:
            # draw visible surfaces
            display.fill(self.back_color)
            for surface, top in self.font_surfaces:
                if top >= self.y_offset:
                    x = center - surface.get_width() // 2
                    display.blit(surface, (x, top - self.y_offset))

            # get input and update the screen
            if not self.handle_events():
                break
            pg.display.flip()
            clock.tick(30)

    def render_surface(self):
        """
        Note: this method uses twice the memory and is only called if
        big_surface is set to true or big is added to the command line.

        Optionally generates one large buffer to draw all the font surfaces
        into. This is necessary to save the display to a png file and may
        be useful for testing large surfaces.
        """

        large_surface = pg.surface.Surface(
            (self.max_width, self.total_height)).convert()
        large_surface.fill(self.back_color)
        print("scrolling surface created")

        # display the surface size and memory usage
        byte_size = large_surface.get_bytesize()
        total_size = byte_size * (self.max_width * self.total_height)
        print("Surface Size = {}x{} @ {}bpp: {:,.3f}mb".format(
                self.max_width, self.total_height,
                byte_size, total_size / 1000000.0))

        y = 0
        center = int(self.max_width / 2)
        for surface, top in self.font_surfaces:
            w = surface.get_width()
            x = center - int(w / 2)
            large_surface.blit(surface, (x, y))
            y += surface.get_height()
        self.max_y = (large_surface.get_height() - 
                pg.display.get_surface().get_height() )
        self.surface = large_surface

    def display_surface(self, time=10):
        """
        Display the large surface created by the render_surface method. Scrolls
        based on the y_offset value(set in handle_events) and the height of the
        pygame window.
        """
        screen = pg.display.get_surface()

        # Create a rect equal to the size of the screen. Then we can just change
        # its top attribute to draw the desired part of the rendered font surface
        # to the display surface
        rect = pg.rect.Rect(
            0,
            0,
            self.surface.get_width(),
            min(self.surface.get_height(), screen.get_height()) )
        x = int((screen.get_width() - self.surface.get_width()) / 2)

        while True:
            if not self.handle_events():
                break
            screen.fill(self.back_color)
            rect.top = self.y_offset
            screen.blit(self.surface, (x, 0), rect)
            pg.display.flip()
            self.clock.tick(20)

    def save_png(self, name="font_viewer.png"):
        pg.image.save(self.surface, name)
        file_size = os.path.getsize(name) // 1024
        print("font surface saved to {}\nsize: {:,}Kb".format(name, file_size))

    def handle_events(self):
        """
        This method handles user input. It returns False when it receives
        a pygame.QUIT event or the user presses escape. The y_offset is
        changed based on mouse and keyboard input. display_fonts() and
        display_surface() use the y_offset to scroll display.
        """
        events = pg.event.get()
        for e in events:
            if e.type == pg.QUIT:
                return False
            elif e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    return False
            elif e.type == pg.MOUSEBUTTONDOWN:
                # enter or exit virtual mouse mode for scrolling
                self.grabbed = not self.grabbed
                pg.event.set_grab(self.grabbed)
                pg.mouse.set_visible(not self.grabbed)

        # allow simple accelerated scrolling with the keyboard
        keys = pg.key.get_pressed()
        if keys[pg.K_UP]:
            self.key_held += 1
            self.y_offset -= self.KEY_SCROLL_SPEED * (self.key_held / 10)
        elif keys[pg.K_DOWN]:
            self.key_held += 1
            self.y_offset += self.KEY_SCROLL_SPEED * (self.key_held / 10)
        else:
            self.key_held = 20

        # set the y_offset for scrolling and keep it between 0 and max_y
        y = pg.mouse.get_rel()[1]
        if y and self.grabbed:
            self.y_offset += (y / 2) ** 2 * (y / abs(y))
            self.y_offset = min((max(self.y_offset, 0), self.max_y))
        return True


viewer = fontviewer()
