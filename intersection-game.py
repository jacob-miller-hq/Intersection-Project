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
import numpy as np
import numpy.linalg as la

DEBUG = True

def rotate(vector, angle):
    angle = angle / 180 * math.pi
    return np.dot(vector, [[math.cos(angle), math.sin(angle)], [-math.sin(angle), math.cos(angle)]])

class Car:
    # TODO: this should extend sprite
    def __init__(self):
        self.width = 40
        self.length = 70
        self.center = np.array([80, 80], dtype='float64')
        self.angle = -60
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

        self.shape = np.array([
            [-0.5, -0.2],
            [0.5, -0.2],
            [0.5, 0.8],
            [-0.5, 0.8]
        ]) * [self.width, self.length]

    def contains(self, point):
        # TODO: potentially redo this to utilize SAT like collision
        point = np.array(point, dtype='float64')
        point -= self.center
        point = rotate(point, -self.angle)
        point += pygame.math.Vector2(0.5 * self.width, 0.2 * self.length)
        return point[0] > 0 and point[0] < self.width and point[1] > 0 and point[1] < self.length

    def getEdges(self):
        points = rotate(self.shape, self.angle) + self.center
        return np.stack([points, np.roll(points, 1, axis=0)], axis=1)

    # implemented the Separating Axis Theorem from here:
    # https://www.metanetsoftware.com/technique/tutorialA.html
    # *Note: Only really works on convex shapes and needs more work to work with non-polygons
    def collides(self, o, surface=None):        
        allEdges = np.concatenate((self.getEdges(), o.getEdges()))
        vecs1 = rotate(self.shape, self.angle)
        vecs2 = rotate(o.shape, o.angle)
        for edge in allEdges:
            vec = edge[1] - edge[0]
            vec /= la.norm(vec)
            orthoVec = np.array([vec[1], -vec[0]])

            projected1 = np.dot(vecs1, vec)
            projected2 = np.dot(vecs2, vec)
            projDist = np.dot(o.center - self.center, vec)

            # display stuff
            if DEBUG and surface != None:
                midCenter = (self.center + o.center) / 2
                axisCenter = midCenter - 200 * orthoVec
                axis1 = axisCenter - projDist / 2 * vec
                axis2 = axisCenter + projDist / 2 * vec
                # print(vec, vec)
                pygame.draw.line(surface, (100, 100, 100), midCenter, axisCenter, 1)
                pygame.draw.line(surface, (100, 100, 100), axis1, axis2, 1)
                pygame.draw.line(surface, (100, 100, 200), axis1 + projected1.min() * vec, axis1 + projected1.max() * vec, 7)
                pygame.draw.line(surface, (100, 0, 100), axis2 + projected2.min() * vec, axis2 + projected2.max() * vec, 3)

            if projDist > projected1.max() - projected2.min() or projDist < projected1.min() - projected2.max():
                return False
        return True
    
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
        velocity = rotate(np.array([0, self.speed]), self.angle)
        self.center += velocity

    def draw(self, surface):
        points = rotate(self.shape, self.angle) + self.center
        pygame.draw.polygon(surface, self.color, points)
        if DEBUG:
            direction = rotate(np.array([0, 1]), self.angle)
            velocity = self.speed * direction
            pygame.draw.line(surface, (255, 0, 255), self.center, self.center + 10 * velocity, 1)
            frontCenter = self.center + 0.6 * self.length * direction
            pygame.draw.line(surface, (255, 0, 255), frontCenter, frontCenter + 10 * rotate(direction, self.turn * 20), 3)

class IntersectionGame:
    def __init__(self):
        self.clock = pygame.time.Clock()
        size = (800, 600)
        self.screen = pygame.display.set_mode(size)
        # TODO: this should be a sprite group
        self.cars = [Car(), Car()]
        self.selectedCar = None
        self.keys = {}
        self.mouse = [(0,0), 0, 0, 0, 0, 0, 0] #[pos, b1,b2,b3,b4,b5,b6]

    def gameLoop(self, fr=60):
        running = True
        while running:
            # check for exit
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # self.mouse[event.button] = True
                    # self.mouse[0] = event.pos
                    self.selectedCar = None
                    for car in self.cars:
                        if car.contains(event.pos):
                            self.selectedCar = car

                # elif event.type == pygame.MOUSEBUTTONUP:
                #     self.mouse[event.button] = False
                #     self.mouse[0] = event.pos
                # elif event.type == pygame.MOUSEMOTION:
                #     self.mouse[0] = event.pos
                elif event.type == pygame.KEYDOWN:
                    self.keys[event.key] = True
                elif event.type == pygame.KEYUP:
                    self.keys[event.key] = False
            
            # timing check
            # TODO: add a little more here to ensure consistency
            self.clock.tick(60)
            # game tick
            for car in self.cars:
                if car == self.selectedCar:
                    car.update(self.keys)
                else:
                    car.update()

            # draw everything
            self.screen.fill((0, 0, 0))

            for car in self.cars:
                car.draw(self.screen)
            
            # TODO move collision before screen clear when finished debugging
            if self.cars[0].collides(self.cars[1], self.screen):
                # print(self.cars[0].center)
                pass

            pygame.display.flip()

if __name__ == "__main__":
    pygame.init()

    game = IntersectionGame()
    game.gameLoop()

