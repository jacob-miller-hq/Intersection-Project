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

DEBUG = False

def rotate(vector, angle):
    angle = angle / 180 * math.pi
    return np.dot(vector, [[math.cos(angle), math.sin(angle)], [-math.sin(angle), math.cos(angle)]])

class Polygon:
    # TODO: this should extend sprite?
    def __init__(self, center=None, angle=0, color=(255, 255, 255)):
        self.center = np.array(center, dtype='float64') if not center is None else np.array([80, 80], dtype='float64')
        self.angle = angle
        self.color = color

        self.shape = np.array([
            [-20, 10],
            [-10, 20],
            [10, 20],
            [20, 10],
            [20, -10],
            [10, -20],
            [-10, -20],
            [-20, -10]
        ])

    def getPoints(self):
        return rotate(self.shape, self.angle) + self.center

    def getEdges(self):
        points = self.getPoints()
        return np.stack([points, np.roll(points, 1, axis=0)], axis=1)

    def containsPoint(self, point):       
        edges = self.getEdges()
        vecs1 = rotate(self.shape, self.angle)
        for edge in edges:
            vec = edge[1] - edge[0]
            vec /= la.norm(vec)

            projected1 = np.dot(vecs1, vec)
            projDist = np.dot(point - self.center, vec)

            if projDist > projected1.max() or projDist < projected1.min():
                return False
        return True

    # *Note: works only with convex polygons
    def contains(self, o):
        for point in o.getPoints():
            if not self.containsPoint(point):
                return False
        return True

    # implemented the Separating Axis Theorem from here:
    # https://www.metanetsoftware.com/technique/tutorialA.html
    # *Note: Only really works on convex shapes and needs more effort to work with non-polygons
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

    def draw(self, surface):
        points = self.getPoints()
        pygame.draw.polygon(surface, self.color, points, 2)

class Car(Polygon):
    def __init__(self, center=None, angle=0, color=(0, 200, 0), speed=5):
        Polygon.__init__(self, center, angle, color)
        self.width = 40
        self.length = 70
        self.speed = speed
        self.turn = 0
        self.selected = False

        self.ACC = 0.1
        self.BRAKE = 0.3
        self.TURN_SPEED = 0.05
        self.MAX_TURN = 1
        self.MAX_SPEED = 100
        self.DRAG = 0.98
        self.STRAIGHTENING = 0.95

        self.shape = np.array([
            [0.75, -0.5],
            [0.8, -0.4],
            [0.8, 0.4],
            [0.75, 0.5],
            [-0.2, 0.5],
            [-0.2, -0.5]
        ]) * [self.length, self.width]

    def getEdges(self):
        points = rotate(self.shape, self.angle) + self.center
        return np.stack([points, np.roll(points, 1, axis=0)], axis=1)
    
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
        velocity = rotate(np.array([self.speed, 0]), self.angle)
        self.center += velocity

    def draw(self, surface):
        points = self.getPoints()
        pygame.draw.polygon(surface, self.color, points)
        if self.selected:
            pygame.draw.polygon(surface, (255, 255, 255), points, 2)
        if DEBUG:
            direction = rotate(np.array([1, 0]), self.angle)
            velocity = self.speed * direction
            pygame.draw.line(surface, (255, 0, 255), self.center, self.center + 10 * velocity, 1)
            frontCenter = self.center + 0.6 * self.length * direction
            pygame.draw.line(surface, (255, 0, 255), frontCenter, frontCenter + 10 * rotate(direction, self.turn * 20), 3)

class FromRoad(Polygon):
    def __init__(self, carList, color=(0, 0, 200)):
        Polygon.__init__(self, np.array([500, 300], dtype='float64'), 10, color)
        self.carList = carList
        self.length = 300
        self.speed = 7
        self.color = color
        self.spawnMin = 200
        self.spawnMax = 300
        self.spawnTick = np.random.randint(self.spawnMin, self.spawnMax+1)
        self.tickCount = 0
        self.spawnPoint = self.center + rotate(np.array([-self.length, 0]), self.angle)
        self.shape = np.array([[0, -30], [0, 30], [-self.length, 30], [-self.length, -30]])

    def update(self):
        self.tickCount += 1
        if self.tickCount > self.spawnTick:
            self.spawn()
            self.tickCount = 0
            self.spawnTick = np.random.randint(self.spawnMin, self.spawnMax+1)
        return 0
    
    def spawn(self):
        # TODO: fix spawning/pushing bug?
        self.carList.append(Car(self.spawnPoint.copy(), self.angle, self.color, self.speed))

class ToRoad(Polygon):
    def __init__(self, carList, color=(0, 0, 200)):
        Polygon.__init__(self, np.array([500, 500], dtype='float64'), -10, color)
        self.carList = carList
        self.length = 300
        self.speed = 7
        self.shape = np.array([[0, -30], [0, 30], [-self.length, 30], [-self.length, -30]])

    def update(self):
        total = 0
        for car in self.carList:
            if self.contains(car):
                self.carList.remove(car)
                total += 1
        return total

class IntersectionGame:
    def __init__(self):
        self.clock = pygame.time.Clock()
        size = (800, 600)
        self.screen = pygame.display.set_mode(size)
        # TODO: these should be sprite groups
        self.cars = [Car(angle=80), Car(angle=100)]
        self.roads = [FromRoad(self.cars, (0, 0, 200)), ToRoad(self.cars, (0, 200, 0))]
        self.selectedCar = None
        self.keys = {}
        self.mouse = [(0,0), 0, 0, 0, 0, 0, 0] #[pos, b1,b2,b3,b4,b5,b6]
        self.score = 0

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
                    if not self.selectedCar is None:
                        self.selectedCar.selected = False
                        self.selectedCar = None
                    for car in reversed(self.cars):
                        if car.containsPoint(event.pos):
                            self.selectedCar = car
                            self.selectedCar.selected = True
                            break

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
            
            for road in self.roads:
                self.score += road.update()

            for i in range(len(self.cars)):
                for j in range(i+1, len(self.cars)):
                    if (self.cars[i].collides(self.cars[j])):
                        self.cars[i].color = (200, 0, 0)
                        self.cars[j].color = (200, 0, 0)

            # draw everything
            self.screen.fill((0, 0, 0))

            for car in self.cars:
                car.draw(self.screen)
            for road in self.roads:
                road.draw(self.screen)

            font = pygame.font.Font(None, 40)
            textSurface = font.render("Score: {}".format(self.score), True, (255, 255, 255))
            self.screen.blit(textSurface, (12, 12))

            pygame.display.flip()
        

if __name__ == "__main__":
    pygame.init()

    game = IntersectionGame()
    game.gameLoop()

