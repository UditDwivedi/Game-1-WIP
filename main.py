import pygame,sys,random,math
import json
from pygame.locals import *
pygame.init()

clock = pygame.time.Clock()
FPS = 60
cycle = 0

worlddim = (1280,720)
resolution = (1280,720)
monitor = (pygame.display.Info().current_w,pygame.display.Info().current_h)
Win = pygame.display.set_mode(resolution)
win = pygame.Surface(worlddim)
pygame.display.set_caption('Title')
fullscreen = False

with open("data\\levels\\level1.json",'r')as file1:
    world =  json.load(file1)
hitboxes = []
tilesize = 20
tiledim = (worlddim[0]//tilesize,worlddim[1]//tilesize)

class Player:
    def __init__(self,pos,hitbox):
        self.vel = [0,0]
        self.grounded = True
        self.moving = False
        self.facing = 1
        self.hitbox = pygame.Rect(pos[0],pos[1],hitbox[0],hitbox[1])
        self.curtile = [self.hitbox.centerx//tilesize,self.hitbox.bottom//tilesize]
        self.battery = 1200

        spritesheet = pygame.image.load("data\\sprites\\bot standing.png")
        self.animations = {
            "moving" : [spritesheet.subsurface(i*64,0,64,64) for i in range(4)] + [10],
            "stopping" : [spritesheet.subsurface(i*64,64,64,64) for i in range(2)] + [20],
            "starting" : [spritesheet.subsurface(i*64,64,64,64) for i in range(2,4)] + [20],
            "standing" : [spritesheet.subsurface(i*64,128,64,64) for i in range(2)] + [30],
            "jumping" : [spritesheet.subsurface(i*64,128,64,64) for i in range(2,4)] + [15],
            "midair" : [spritesheet.subsurface(0,192,64,64)] + [FPS],
            "landing" : [spritesheet.subsurface(64,192,64,64)] + [30],
            "waiting" : [spritesheet.subsurface(128,192,64,64) ] + [FPS]
        }
        self.animtick = 0
        self.curanim = self.animations["standing"]
        self.nextanim = self.animations["standing"]

    def changeanim(self,cur,next):
        self.curanim = self.animations[cur]
        self.nextanim = self.animations[next]
        self.animtick = 0

    def ground(self):
        if not self.grounded:
            if not self.moving:
                self.changeanim("landing","standing")
            elif self.moving:
                self.changeanim("landing","moving")
            self.grounded = True
        self.vel[1] = 0

    def resolve(self):
        
        self.vel[1] += 0.2
        if self.vel[1] > 10:
            self.vel[1] = 10

        if self.moving:
            self.vel[0] += self.facing*0.5
            if self.facing == 1 and self.vel[0] > 4:
                self.vel[0] = 4
            if self.facing == -1 and self.vel[0] < -4:
                self.vel[0] = -4
        else:
            if abs(self.vel[0]) > 0.4:
                self.vel[0] -= 0.2*self.facing
            else:
                self.vel[0] = 0

        self.curtile = [self.hitbox.centerx//tilesize,self.hitbox.bottom//tilesize]
        
        move(self,hitboxes) 
        # if self.battery:
        #     player.battery -= 1            
        # else:
        #     self.changeanim("waiting","waiting")
        #     self.moving = False

        if self.grounded and (self.vel[1] > 1 or self.vel[1] < -1):
            self.grounded = False
            self.changeanim("midair","midair")

    def draw(self,win):
        if cycle%self.curanim[-1] == 0:
            self.animtick += 1
        if self.animtick == len(self.curanim)-1:
            if self.nextanim:
                self.curanim = self.nextanim
                self.animtick = 0
            else:
                self.animtick -= 1

        img = self.curanim[self.animtick]

        if self.facing == -1:
            img = pygame.transform.flip(img,1,0)

        win.blit(img,(self.hitbox.x-16,self.hitbox.y-8))
        pygame.draw.rect(win, (255,0,0), self.hitbox, 1)
        pygame.draw.rect(win, (240,0,240), (self.curtile[0]*tilesize,self.curtile[1]*tilesize,tilesize,tilesize),1)
        pygame.draw.rect(win, (15,240,0),(20,20,self.battery//12,20))
        pygame.draw.rect(win, (240,240,240), (20,20,100,20), 2)
        
def move(entity, hitboxes):
    entity.hitbox.x += entity.vel[0]
    hits = []
    for box in hitboxes:
        if box.colliderect(entity.hitbox):
            hits.append(box)
    
    for box in hits: 
        
        if entity.vel[0] >= 0 and entity.hitbox.right > box.left:
            entity.hitbox.right = box.left
            entity.vel[0] = 0
            entity.moving = False
            continue
        elif entity.vel[0] < 0 and entity.hitbox.left < box.right:
            entity.hitbox.left = box.right
            entity.vel[0] = 0
            entity.moving = False
            continue

    entity.hitbox.y += entity.vel[1]
    hits = []
    for box in hitboxes:
        if box.colliderect(entity.hitbox):
            hits.append(box)
    for box in hits:
        if entity.vel[1] >= 0 and entity.hitbox.bottom > box.top:
            entity.hitbox.bottom = box.top
            entity.ground()
            continue
        elif entity.vel[1] < 0 and entity.hitbox.top < box.bottom:
            entity.hitbox.top = box.bottom
            entity.vel[1] = 0
            continue

def optimize_level():
    global world, hitboxes
    temp = {}  
    hitboxes = []     
    for y in range(tiledim[1]):
        box = 0
        for x in range(tiledim[0]):              
            if world[y][x]:
                box += 1
            elif box:
                if (x-box,box) not in temp:
                    temp[(x-box,box)] = []
                temp[(x-box,box)].append(y)
                box = 0
        if box:
            if (x+1-box,box) not in temp:
                temp[(x+1-box,box)] = []
            temp[(x+1-box,box)].append(y)
    temp2 = {}
    for x in temp:
        temp2[x] = []
        column = []
        count = 0
        for y in temp[x]:
            if y == count:
                column.append(y)
                
            else:
                if column != []:
                    temp2[x].append(column)
                column = [y]
                count = y
            count += 1
        temp2[x].append(column)
    for i in temp2:
        for j in temp2[i]:
            hitboxes.append(pygame.Rect(i[0]*tilesize,j[0]*tilesize,i[1]*tilesize,len(j)*tilesize))

    with open("data\\levels\\level1.json",'w')as file1:
        json.dump(world,file1)

curlevel = 1
spawntile = (10,10)
player = Player(spawntile,(32,56))
player.hitbox.centerx = spawntile[0]*tilesize + tilesize//2
player.hitbox.bottom = spawntile[1]*tilesize 
gameplay = True
worldedit = False
paused = False

def genratebattery():
    temppos = [random.randrange(0,tiledim[0]),random.randrange(0,tiledim[1])]
     
def gameplayrun(): 

    global cycle, gameplay
    cycle += 1

    for event in pygameevent:

        if event.type == KEYDOWN:

            if player.grounded and player.battery:
                if event.key == K_LEFT and not(player.moving):
                    player.facing = -1
                    player.moving = True
                    player.changeanim("starting","moving")
                elif event.key == K_RIGHT and not(player.moving):
                    player.facing = 1
                    player.moving = True
                    player.changeanim("starting","moving")
                if event.key == K_UP:
                    player.changeanim("jumping","midair")
                    player.grounded = False
                    player.vel[1] = -6  
                                 

        elif event.type == KEYUP:
            
            if event.key == K_LEFT or event.key == K_RIGHT:
                if player.grounded and player.moving:
                    player.changeanim("stopping","standing")
                player.moving = False
           
    if len(batteries) < 4 and cycle%300:
        genratebattery()

    player.resolve()
    if world[player.curtile[1]][player.curtile[0]] == 3:
        gameplay = False
        print("win")

def worldeditrun():

    mouse = pygame.mouse.get_pressed()
    mpos = pygame.mouse.get_pos()
    mtile = (mpos[0]//tilesize,mpos[1]//tilesize)
    if mouse[0]:
        world[mtile[1]][mtile[0]] = 1
    elif mouse[2]:
        world[mtile[1]][mtile[0]] = 0
    # for event in pygameevent:

    #     if event.type == MOUSEBUTTONDOWN:
    #         mpos = event.pos
    #         mtile = (mpos[0]//tilesize,mpos[1]//tilesize)
    #         if event.button == 1:
    #             world[mtile[1]][mtile[0]] = 1
    #         elif event.button == 3:
    #             world[mtile[1]][mtile[0]] = 0 

def redraw():
    win.fill((30,30,30))

    for y in range(tiledim[1]):
        for x in range(tiledim[0]):
            if world[y][x] == 1:
                pygame.draw.rect(win,(0,0,240),(x*tilesize,y*tilesize,tilesize,tilesize))
            elif world[y][x] == 2:
                pygame.draw.rect(win,(240,240,0),(x*tilesize,y*tilesize,tilesize,tilesize))
            elif world[y][x] == 3:
                pygame.draw.rect(win,(0,240,0),(x*tilesize,y*tilesize,tilesize,tilesize))
    for i in hitboxes:
        pygame.draw.rect(win,(255,0,0),i,1)
    if worldedit:
        pass
    else:
        player.draw(win)
    if fullscreen:
        Win.blit(pygame.transform.scale(win,monitor),(0,0))
    else:
        Win.blit(pygame.transform.scale(win,resolution),(0,0))

    pygame.display.update()

batteries = []

optimize_level()
while True:

    clock.tick(FPS)
     
    pygameevent = pygame.event.get()

    for event in pygameevent:
        if event.type == QUIT:
            pygame.quit()
            sys.exit("__main__")
        
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit("__main__")
            if event.key == K_LCTRL:
                if worldedit:
                    optimize_level()
                worldedit = not worldedit
                gameplay = not gameplay                
            
            if event.key == K_f:
                fullscreen = not fullscreen
                if fullscreen:                    
                    Win = pygame.display.set_mode(monitor,FULLSCREEN)
                else:
                    Win = pygame.display.set_mode(resolution)

    if gameplay:
        gameplayrun()
    elif worldedit:
        worldeditrun()
    elif paused:
        pass
    else:
        pass

    redraw()
    