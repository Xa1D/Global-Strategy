import pygame

class Button():
    def __init__(self, text, position, font, base_colour, hover_colour,function=None, base_bg=(50,50,50), hover_bg=(0,100,200),padding=(10,10), image=None):
        self.font = font
        self.text_input = text
        self.base_colour = base_colour
        self.hover_colour = hover_colour
        self.function = function
        self.base_bg = base_bg
        self.hover_bg = hover_bg
        self.padding = padding

        self.text_base = self.font.render(self.text_input, True, self.base_colour)
        self.text_hover = self.font.render(self.text_input, True, self.hover_colour)
        self.text = self.text_base
        self.text_width = self.text.get_width() + 2*self.padding[0]
        self.text_height = self.text.get_height() + 2*self.padding[1]
        
        if image:
            self.using_image = True
            self.surface = image
        else:
            self.surface = pygame.Surface((self.text_width, self.text_height))
            self.surface.fill(self.base_bg)
            self.using_image = False
        self.rect = self.surface.get_rect(center=position)
        self.text_rect = self.text.get_rect(center=self.rect.center)

    def update(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(self.surface, self.rect)
        screen.blit(self.text, self.text_rect)
        self.change_hover_colour(mouse_pos)

    def change_hover_colour(self, pos):
        if self.rect.collidepoint(pos):
            self.text = self.text_hover
            if not self.using_image: 
                self.surface.fill(self.hover_bg)
        else:
            self.text = self.text_base
            if not self.using_image:
                self.surface.fill(self.base_bg)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.function:
                self.function()

class Sidebar:
    def __init__(self, pos, width, height, font, bg_colour=(30,30,30), padding=10):
        self.pos = pos
        self.width = width
        self.height = height
        self.font = font
        self.bg_colour = bg_colour
        self.padding = padding
        self.buttons = []
        self.labels = []

    def add_text(self, text, position):
        self.labels.append((text, position))

    def add_button(self, text, position, function):
        button = Button(text=text, position=position, font=self.font, base_colour=(255,255,255), hover_colour=(255,255,0), function=function)
        self.buttons.append(button)

    def handle_event(self, event):
        for i in self.buttons:
            i.handle_event(event)

    def draw_labels(self, screen):
        for text, position in self.labels:
            text_surface = self.font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, position)
            

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_colour, (self.pos[0], self.pos[1], self.width, self.height))
        self.draw_labels(screen)
        for button in self.buttons:
            button.update(screen)

class Camera:
    def __init__(self):
        self.speed = 8
        self.pos = pygame.Vector2(3500,450)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.pos.x -= self.speed
        if keys[pygame.K_d]:
            self.pos.x += self.speed
        if keys[pygame.K_w]:
            self.pos.y -= self.speed
        if keys[pygame.K_s]:
            self.pos.y += self.speed