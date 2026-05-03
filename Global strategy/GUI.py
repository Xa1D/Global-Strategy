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
        mouse_pos = pygame.mouse.get_pos()
        self.text_rect.center = self.rect.center
        screen.blit(self.image, self.rect)
        screen.blit(self.text, self.text_rect)
        self.change_hover_colour(mouse_pos)

    def change_hover_colour(self, pos):
        if self.rect.collidepoint(pos):
            self.text = self.text_hover
            if not self.using_image: 
                self.image.fill(self.hover_bg)
        else:
            self.text = self.text_base
            if not self.using_image:
                self.image.fill(self.base_bg)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            if self.function:
                self.function()

class Sidebar:
    def __init__(self, pos, width, height, font, bg_colour=(30,30,30), padding=10, button_spacing=60):
        self.pos = pos
        self.width = width
        self.height = height
        self.font = font
        self.bg_colour = bg_colour
        self.padding = padding
        self.button_spacing = button_spacing
        self.buttons = []

    def add_button(self, text, function):
        pos_y = self.pos[1] + 100 
        pos_y += len(self.buttons) * self.button_spacing
        button_pos = (self.pos[0] + self.width // 2, pos_y)
        button = Button(text=text, position=button_pos, font=self.font, base_colour=(255,255,255), hover_colour=(255,255,0), function=function)
        self.buttons.append(button)

    def handle_event(self, event):
        for i in self.buttons:
            i.handle_event(event)

    def draw(self, screen, country):
        pygame.draw.rect(screen, self.bg_colour, (self.pos[0], self.pos[1], self.width, self.height))
        if country is None:
             name_text = self.font.render("Stats", True, (255,255,255))
             screen.blit(name_text, (self.pos[0]+self.padding, self.pos[1]+self.padding))
        else:
            name_text = self.font.render(country.name, True, (255,255,255))
            units_text = self.font.render(f"Units: {country.units}", True, (255,255,255))
            screen.blit(name_text, (self.pos[0]+self.padding, self.pos[1]+self.padding))
            screen.blit(units_text, (self.pos[0]+self.padding, self.pos[1]+40))
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