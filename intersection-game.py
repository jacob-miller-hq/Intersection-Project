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

DEBUG = True

def deg2rad(deg):
    return deg / 180 * math.pi

class Car:
    # TODO: this should extend sprite
    def __init__(self):
        self.width = 40
        self.length = 70
        self.center = pygame.math.Vector2(80, 80)
        self.angle = -30
        self.color = (0, 180, 0)
        self.speed = 10
        self.turn = 0
        self.ACC = 0.1
        self.BRAKE = 0.3
        self.TURN_SPEED = 0.05
        self.MAX_TURN = 1
        self.MAX_SPEED = 100
        self.DRAG = 0.98
        self.STRAIGHTENING = 0.95

        self.shape = [
            pygame.math.Vector2(-0.5 * self.width, -0.2 * self.length),
            pygame.math.Vector2(0.5 * self.width, -0.2 * self.length),
            pygame.math.Vector2(0.5 * self.width, 0.8 * self.length),
            pygame.math.Vector2(-0.5 * self.width, 0.8 * self.length)
        ]
    
    def update(self, keys=None):
        self.speed *= self.DRAG
        self.turn *= self.STRAIGHTENING
        if keys != None:
            if pygame.K_DOWN in keys and keys[pygame.K_DOWN]:
                self.speed -= self.BRAKE
                if self.speed < 0:
                    self.speed = 0
            elif pygame.K_UP in keys and keys[pygame.K_UP]:
                self.speed += self.ACC
                if self.speed > self.MAX_SPEED:
                    self.speed = self.MAX_SPEED
            if pygame.K_LEFT in keys and keys[pygame.K_LEFT]:
                self.turn -= self.TURN_SPEED
                if self.turn < -self.MAX_TURN:
                    self.turn = -self.MAX_TURN
            if pygame.K_RIGHT in keys and keys[pygame.K_RIGHT]:
                self.turn += self.TURN_SPEED
                if self.turn > self.MAX_TURN:
                    self.turn = self.MAX_TURN

        self.angle += self.turn * self.speed
        velocity = pygame.math.Vector2(0, self.speed).rotate(self.angle)
        self.center += velocity

        # TODO: collision detection. Might not be done right here though


    def draw(self, surface):
        points = [vertex.rotate(self.angle) + self.center for vertex in self.shape]        
        pygame.draw.polygon(surface, self.color, points)
        if DEBUG:
            direction = pygame.math.Vector2(0, 1).rotate(self.angle)
            velocity = self.speed * direction
            pygame.draw.line(surface, (255, 0, 255), self.center, self.center + 10 * velocity, 1)
            frontCenter = self.center + 0.6 * self.length * direction
            pygame.draw.line(surface, (255, 0, 255), frontCenter, frontCenter + 10 * direction.rotate(self.turn * 20), 3)

class IntersectionGame:
    def __init__(self):
        self.clock = pygame.time.Clock()
        size = (800, 600)
        self.screen = pygame.display.set_mode(size)
        # TODO: this should be a sprite group
        self.cars = [Car()]
        self.keys = {}

    def gameLoop(self, fr=60):
        running = True
        while running:
            # check for exit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.keys[event.key] = True
                elif event.type == pygame.KEYUP:
                    self.keys[event.key] = False
            
            # timing check
            # TODO: add a little more here to ensure consistency
            self.clock.tick(60)
            # game tick
            for car in self.cars:
                car.update(self.keys)

            # draw everything
            self.screen.fill((0, 0, 0))

            for car in self.cars:
                car.draw(self.screen)

            pygame.display.flip()

if __name__ == "__main__":
    pygame.init()

    game = IntersectionGame()
    game.gameLoop()

