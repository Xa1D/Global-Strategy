import pygame
pygame.init()
class Button():
    def __init__(self, text, position, font, base_colour, hover_colour,function=None, image=None):
        self.font = font
        self.text_input = text
        self.base_colour = base_colour
        self.hover_colour = hover_colour
        self.function = function
        self.base_bg = (50,50,50)
        self.hover_bg = (0,100,200)
        self.padding = (10,10)

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

class Panel:
    def __init__(self, pos, width, height, font):
        self.pos = pos
        self.width = width
        self.height = height
        self.font = font
        self.bg_colour = (30,30,30)
        self.padding = 10
        self.buttons = []
        self.labels = []
        self.dividers = []

    def add_text(self, text, position):
        self.labels.append((text, position))

    def add_button(self, text, position, function):
        button = Button(text=text, position=position, font=self.font, base_colour=(255,255,255), hover_colour=(255,255,0), function=function)
        self.buttons.append(button)

    def add_divider(self,x_start,y_start,x_end,y_end):
        self.dividers.append((x_start, y_start, x_end,y_end))

    def handle_event(self, event):
        for i in self.buttons:
            i.handle_event(event)

    def draw_labels(self, screen):
        for text, position in self.labels:
            text_surface = self.font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, position)

    def draw_dividers(self, screen):
        for x_start, y_start, x_end,y_end in self.dividers:
            pygame.draw.line(screen, (100, 100, 100), (x_start, y_start), (x_end, y_end), width=2)

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_colour, (self.pos[0], self.pos[1], self.width, self.height))
        self.draw_labels(screen)
        self.draw_dividers(screen)
        for button in self.buttons:
            button.update(screen)

class Camera:
    def __init__(self,pos):
        self.speed = 8
        self.pos = [pos[0],pos[1]]
        self.zoom = 1
        self.zoom_range = [0.5,2]
        self.zoom_speed = 0.05

    def handle_scroll(self,events):
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                original_zoom = self.zoom
                if event.y > 0:
                    self.zoom = min(self.zoom + self.zoom_speed, self.zoom_range[1])
                if event.y < 0:
                    self.zoom = max(self.zoom - self.zoom_speed, self.zoom_range[0])

                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.pos[0] = self.pos[0] + mouse_x / original_zoom - mouse_x / self.zoom
                self.pos[1] = self.pos[1] + mouse_y / original_zoom - mouse_y / self.zoom
                   
    def update(self,events):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.pos[0] -= self.speed
        if keys[pygame.K_d]:
            self.pos[0] += self.speed
        if keys[pygame.K_w]:
            self.pos[1] -= self.speed
        if keys[pygame.K_s]:
            self.pos[1] += self.speed
        self.handle_scroll(events)