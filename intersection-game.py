"""
Engine of the intersection 'game'
"""

### Mechanics Ideas: ###
"""
Each car will be its own game object with limitations on speed and accelleration
Each entry and exit road will also be its own object with speed, length, and traffic density defined
The intersection itself will be a single polygon
The user/ai may select 1 car at a time to control its speed/direction (or acceleration/turning radius?)
Only cars in the intersection can turn independantly
cars exiting the intersection must be within 10? degrees of the target direction of the outgoing road
"""

import sys, math, pygame

def deg2rad(deg):
    return deg / 180 * math.pi

class Car:
    # TODO: this should extend sprite
    def __init__(self):
        self.width = 40
        self.length = 70
        self.center = pygame.math.Vector2(80, 80)
        self.angle = 60
        self.color = (0, 180, 0)

        h_width = self.width / 2
        h_length = self.length / 2
        self.shape = [
            pygame.math.Vector2(-h_width, -h_length),
            pygame.math.Vector2(h_width, -h_length),
            pygame.math.Vector2(h_width, h_length),
            pygame.math.Vector2(-h_width, h_length)
        ]
    
    def draw(self, surface):
        points = [vertex.rotate(self.angle) + self.center for vertex in self.shape]        
        pygame.draw.polygon(surface, self.color, points)

class IntersectionGame:
    def __init__(self):
        self.clock = pygame.time.Clock()
        size = (800, 600)
        self.screen = pygame.display.set_mode(size)
        # TODO: this should be a sprite group
        self.cars = [Car()]

    def gameLoop(self, fr=60):
        running = True
        while running:
            # check for exit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            
            # timing check
            # TODO: add a little more here to ensure consistency
            self.clock.tick(60)
            # game tick
            for car in self.cars:
                car.angle += 2

            # draw everything
            self.screen.fill((0, 0, 0))

            rect = pygame.Rect(30, 30, 40, 70)
            pygame.draw.rect(self.screen, (255, 0, 0), rect)

            for car in self.cars:
                car.draw(self.screen)

            pygame.display.flip()

if __name__ == "__main__":
    pygame.init()

    game = IntersectionGame()
    game.gameLoop()

