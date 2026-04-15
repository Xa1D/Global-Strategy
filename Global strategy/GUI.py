import pygame

class Button():
    def __init__(self, text, position, font, base_color, hover_color,callback=None, base_bg=(50,50,50), hover_bg=(0,100,200),padding=(10,5), image=None):
        self.font = font
        self.text_input = text
        self.base_color = base_color
        self.hover_color = hover_color
        self.callback = callback
        self.base_bg = base_bg
        self.hover_bg = hover_bg
        self.padding = padding
        self.text_base = self.font.render(self.text_input, True, self.base_color)
        self.text_hover = self.font.render(self.text_input, True, self.hover_color)
        self.text = self.text_base
        width = self.text.get_width() + 2*self.padding[0]
        height = self.text.get_height() + 2*self.padding[1]
        if image:
            self.image = image
            self.using_image = True
        else:
            self.image = pygame.Surface((width, height))
            self.image.fill(self.base_bg)
            self.using_image = False
        self.rect = self.image.get_rect(center=position)
        self.text_rect = self.text.get_rect(center=self.rect.center)

    def update(self, screen):
        self.text_rect.center = self.rect.center
        screen.blit(self.image, self.rect)
        screen.blit(self.text, self.text_rect)

    def hover_colour(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.text = self.text_hover
            if not self.using_image: 
                self.image.fill(self.hover_bg)
        else:
            self.text = self.text_base
            if not self.using_image:
                self.image.fill(self.base_bg)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.callback:
                self.callback()

class Sidebar:
    def __init__(self, pos, width, height, font, bg_color=(30,30,30), padding=10, button_spacing=60):
        self.pos = pos
        self.width = width
        self.height = height
        self.font = font
        self.bg_color = bg_color
        self.padding = padding
        self.button_spacing = button_spacing
        self.buttons = []

    def add_button(self, text, callback):
        pos_y = self.pos[1] + 100 
        pos_y += len(self.buttons) * self.button_spacing
        button_pos = (self.pos[0] + self.width // 2, pos_y)
        button = Button(text=text, position=button_pos, font=self.font, base_color=(255,255,255), hover_color=(255,255,0), callback=callback)
        self.buttons.append(button)

    def handle_event(self, event):
        for i in self.buttons:
            i.handle_event(event)

    def draw(self, screen, country):
        pygame.draw.rect(screen, self.bg_color, (self.pos[0], self.pos[1], self.width, self.height))
        if country is None:
             name_text = self.font.render("Stats", True, (255,255,255))
             screen.blit(name_text, (self.pos[0]+self.padding, self.pos[1]+self.padding))
        else:
            name_text = self.font.render(country.name, True, (255,255,255))
            units_text = self.font.render(f"Units: {country.units}", True, (255,255,255))
            screen.blit(name_text, (self.pos[0]+self.padding, self.pos[1]+self.padding))
            screen.blit(units_text, (self.pos[0]+self.padding, self.pos[1]+40))
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.hover_colour(mouse_pos)
            button.update(screen)