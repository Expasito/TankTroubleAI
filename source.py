#! /usr/bin/python
from __future__ import print_function
import pygame
from pygame import *

import os
import neat
import visualize
import random
import matplotlib.pyplot as plt




"""
Goals:
top-down map with obstacles
players can shoot missiles at each other
multiple players? Teams?

"""
WIN_WIDTH = 21*32
WIN_HEIGHT = 21*32
HALF_WIDTH = int(WIN_WIDTH / 2)
HALF_HEIGHT = int(WIN_HEIGHT / 2)

DISPLAY = (WIN_WIDTH, WIN_HEIGHT)
DEPTH = 32
FLAGS = 0
CAMERA_SLACK = 30
global cameraX, cameraY
run=True
pygame.init()
screen = pygame.display.set_mode(DISPLAY, FLAGS, DEPTH)
pygame.display.set_caption("Use arrows to move!")
timer = pygame.time.Clock()

up = down = left = right = running = False
bg = Surface((32,32))
bg.convert()
bg.fill(Color("#000000"))

def main(genomes,config):
    font = pygame.font.Font(pygame.font.get_default_font(), 12)
    for genome_id,genome in genomes:
        genome.fitness=0
    run=True
    entities = pygame.sprite.Group()
    
    # list of all tanks on the map
    tanks=[]
    bullets=[]

    platforms = []
    for i in range(21):
        p = Platform(i*32,0)
        platforms.append(p)
        entities.add(p)

        p = Platform(0,i*32)
        platforms.append(p)
        entities.add(p)

        p = Platform(20*32,i*32)
        platforms.append(p)
        entities.add(p)

        p = Platform(i*32,20*32)
        platforms.append(p)
        entities.add(p)

    tanks.append(Tank(256,256,None,None,None))
    bullets.append(Bullet(33,33,4,4))
    # bullets.append(Bullet(128,128,1,1))


    total_level_width=1000*6*32
    total_level_height=20*32
    camera = Camera(complex_camera, total_level_width, total_level_height)

    tim=0
    while run:
        tim+=1
        timer.tick(60)

        for e in pygame.event.get():
            if e.type == QUIT:run=False
            

        # draw background
        for y in range(32):
            for x in range(32):
                screen.blit(bg, (x * 32, y * 32))


        # update player, draw everything else



        # print(player1.xvel,player1.nomovecounter)
        for e in entities:
            screen.blit(e.image, camera.apply(e))
        for t in tanks:
            t.update(False,True,False,True,False,platforms,bullets)
            screen.blit(t.image,camera.apply(t))
        
        print(bullets)
        for t in tanks:
            print(t.health)

        for b in bullets:
            b.update(platforms)
            screen.blit(b.image,camera.apply(b))

        for b in bullets:
            if b.alive==False:
                bullets.remove(b)


        pygame.display.update()
        

        if tim>3000:
            run=False

       
    return




class Camera(object):
    def __init__(self, camera_func, width, height):
        self.camera_func = camera_func
        self.state = Rect(0, 0, width, height)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

    def update(self, target):
        self.state = self.camera_func(self.state, target.rect)

def simple_camera(camera, target_rect):
    l, t, _, _ = target_rect
    _, _, w, h = camera
    return Rect(-l+HALF_WIDTH, -t+HALF_HEIGHT, w, h)

def complex_camera(camera, target_rect):
    l, t, _, _ = target_rect
    _, _, w, h = camera
    l, t, _, _ = -l+HALF_WIDTH, -t+HALF_HEIGHT, w, h

    l = min(0, l)                           # stop scrolling at the left edge
    l = max(-(camera.width-WIN_WIDTH), l)   # stop scrolling at the right edge
    t = max(-(camera.height-WIN_HEIGHT), t) # stop scrolling at the bottom
    t = min(0, t)                           # stop scrolling at the top
    return Rect(l, t, w, h)

class Entity(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

class Bullet(Entity):
    def __init__(self, xpos, ypos, xvel, yvel):
        Entity.__init__(self)
        self.xvel=xvel
        self.yvel=yvel

        self.image = Surface((4,4))
        self.image.fill(Color("#0000FF"))
        self.image.convert()
        self.rect = Rect(xpos, ypos, 4, 4)
        self.alive=True
    def update(self, platforms):

        self.rect.left += self.xvel
        self.collide(self.xvel, 0, platforms)
        self.rect.top += self.yvel
        self.collide(0, self.yvel, platforms)

    def collide(self, xvel, yvel, platforms):
        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                if xvel > 0:
                    self.rect.right = p.rect.left
                    self.xvel=0
                    self.alive=False
                if xvel < 0:
                    self.rect.left = p.rect.right
                    self.xvel=0
                    self.alive=False
                if yvel > 0:
                    self.rect.bottom = p.rect.top
                    self.yvel = 0
                    self.alive=False
                if yvel < 0:
                    self.rect.top = p.rect.bottom
                    self.yvel+=3
                    self.alive=False

class Tank(Entity):
    def __init__(self, x, y,genome, genomeid, net):
        Entity.__init__(self)
        self.genome=genome
        self.genomeid=genomeid
        self.net=net
        self.xvel = 0
        self.yvel = 0
        self.health=100

        self.died=False
        self.win=False

        self.acc=.3

        self.image = Surface((32,32))
        self.image.fill(Color("#0000FF"))
        self.image.convert()
        self.rect = Rect(x, y, 32, 32)

    def update(self, up, down, left, right, running, platforms,bullets):
        
        if up:
            self.yvel -=self.acc
        if down:
            self.yvel += self.acc
        if left:
            self.xvel -=self.acc
        if right:
            self.xvel +=self.acc
        if not(left or right):
            if self.xvel>0:
                self.xvel-=self.xacc
            if self.xvel<0:
                self.xvel+=self.xacc
        else:
            if self.xvel>8:
                self.xvel=8
            if self.xvel<-8:
                self.xvel=-8
        if not(up or down):
            if self.yvel>0:
                self.yvel-=self.acc
            if self.yvel<0:
                self.yvel+=self.acc
        else:
            if self.yvel>8:
                self.yvel=8
            if self.yvel<-8:
                self.yvel=-8
        # increment in x direction
        self.rect.left += self.xvel
        # do x-axis collisions
        self.collide(self.xvel, 0, platforms,bullets)
        # increment in y direction
        self.rect.top += self.yvel
        # do y-axis collisions
        self.collide(0, self.yvel, platforms,bullets)


            

    def collide(self, xvel, yvel, platforms, bullets):
        for p in platforms:
            if pygame.sprite.collide_rect(self, p):
                if isinstance(p, ExitBlock):
                    pygame.event.post(pygame.event.Event(QUIT))
                if xvel > 0:
                    self.rect.right = p.rect.left
                    self.xvel=0
                if xvel < 0:
                    self.rect.left = p.rect.right
                    self.xvel=0
                if yvel > 0:
                    self.rect.bottom = p.rect.top
                    self.yvel = 0
                if yvel < 0:
                    self.rect.top = p.rect.bottom
                    self.yvel+=3
        for b in bullets:
            if pygame.sprite.collide_rect(self,b):
                self.health-=10
                bullets.remove(b)


class Platform(Entity):
    def __init__(self, x, y):
        Entity.__init__(self)
        self.image = Surface((32, 32))
        self.image.convert()
        self.image.fill(Color("#DDDDDD"))
        self.rect = Rect(x, y, 32, 32)

    def update(self):
        pass

class ExitBlock(Platform):
    def __init__(self, x, y):
        Platform.__init__(self, x, y)
        self.image.fill(Color("#0033FF"))



def run(config_file):
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)
    # p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-997')

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.add_reporter(neat.Checkpointer(10))

    # Run for up to 300 generations.
    winner = p.run(main, 4000)
    pygame.quit()

    # Display the winning genome.
    print('\nBest genome:\n{!s}'.format(winner))

    # # Show output of the most fit genome against training data.
    # print('\nOutput:')
    # winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    
    # for xi, xo in zip(xor_inputs, xor_outputs):
    #     output = winner_net.activate(xi)
    #     iout=[]
    #     # print(output)
    #     for i in output:
    #         iout.append(int(i))
    #         # print(i)
    #     output=iout
    #     print("input {!r}, expected output {!r}, got {!r}".format(xi, xo, output))

    # node_names = {-1:'Left', -2: 'Right', 0:'up',1:'left',2:"right"}
    visualize.draw_net(config, winner, True)
    visualize.plot_stats(stats, ylog=False, view=True)
    visualize.plot_species(stats, view=True)

    # p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-4')
    # p.run(eval_genomes, 10)


if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward2')
    run(config_path)
