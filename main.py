import pygame,sys,os
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

text1 = pygame.font.SysFont("Ariel",30,0,0)
text2 = pygame.font.SysFont("Ariel",60,1,0)
tilesize = 20
tiledim = (worlddim[0]//tilesize,worlddim[1]//tilesize)
COLOR = [(20,20,230),(20,230,20),(230,20,20),(20,230,230),(230,230,20),(230,230,230),(20,20,20)]
hitboxes = []
dynamic_objects = []

class Player:
    def __init__(self,pos,hitbox):
        self.vel = [0,0]
        self.grounded = True
        self.moving = False
        self.facing = 1
        self.hitbox = pygame.Rect(pos[0],pos[1],hitbox[0],hitbox[1])
        self.curtile = (self.hitbox.centerx//tilesize,self.hitbox.bottom//tilesize)
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

    def stop_moving(self):
        if self.moving:
            self.moving = False
            if player.grounded:
                self.changeanim("stopping","standing")
            else:
                self.changeanim("standing","standing")
            self.vel[0] = 0

    def resolve(self):
        
        self.vel[1] += 0.2
        if self.vel[1] > 10:
            self.vel[1] = 10

        if self.moving:
            self.vel[0] += self.facing*0.5
            if self.facing == 1 and self.vel[0] > 3:
                self.vel[0] = 3
            if self.facing == -1 and self.vel[0] < -3:
                self.vel[0] = -3
        else:
            if self.vel[0] > 0.2:
                self.vel[0] -= 0.2
            elif self.vel[0] < -0.2:
                self.vel[0] += 0.2
            else:
                self.vel[0] = 0

        self.curtile = (self.hitbox.centerx//tilesize,self.hitbox.bottom//tilesize)
        
        move(self) 

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

# Utility Functions

laying_tool = 1
laying_action = None

def openworld(path):
    global start,world,end,doors,switches,player
    with open(path,'r')as file1:
        filecontent =  json.load(file1)
        world = filecontent[0]
        start = filecontent[1]
        end = filecontent[2]
        doors_raw = filecontent[3]
        switches_raw = filecontent[4]

    doors = {}
    for door in doors_raw:
        x,y = door%tiledim[0],door//tiledim[0]
        doors[door] = [True,pygame.Rect(x*tilesize,y*tilesize,tilesize,4*tilesize)]

    switches = {}
    for switch in switches_raw:
        x,y = switch[0]%tiledim[0],switch[0]//tiledim[0]
        switches[(x,y)] = switch[1]

    player = Player(start,(32,56))
    player.hitbox.centerx = start[0]*tilesize + tilesize//2
    player.hitbox.bottom = start[1]*tilesize

def move(entity):
    entity.hitbox.x += entity.vel[0]
    hits = []
    for box in hitboxes:
        if box.colliderect(entity.hitbox):
            hits.append(box)
    for door in doors.values():
        if door[0] and door[1].colliderect(entity.hitbox):
            hits.append(door[1])
    
    for box in hits: 
        
        if entity.vel[0] >= 0 and entity.hitbox.right > box.left:
            entity.hitbox.right = box.left
            entity.stop_moving()
            continue
        elif entity.vel[0] < 0 and entity.hitbox.left < box.right:
            entity.hitbox.left = box.right
            entity.stop_moving()
            continue

    entity.hitbox.y += entity.vel[1]
    hits = []
    for box in hitboxes:
        if box.colliderect(entity.hitbox):
            hits.append(box)
    for door in doors.values():
        if door[0] and door[1].colliderect(entity.hitbox):
            hits.append(door[1])
    for box in hits:
        if entity.vel[1] >= 0 and entity.hitbox.bottom > box.top:
            entity.hitbox.bottom = box.top
            entity.ground()
            continue
        elif entity.vel[1] < 0 and entity.hitbox.top < box.bottom:
            entity.hitbox.top = box.bottom
            entity.vel[1] = 0
            continue
    if entity.hitbox.left < 0:
        entity.hitbox.left = 0
        entity.stop_moving()
    elif entity.hitbox.right > worlddim[0]:
        entity.hitbox.right = worlddim[0]
        entity.stop_moving()
    if entity.hitbox.top < 0:
        entity.hitbox.top = 0
        entity.vel[1] = 0
    elif entity.hitbox.bottom > worlddim[1]:
        entity.hitbox.bottom = worlddim[1]
        entity.ground()

def saveworld():
    doors_raw = list(doors.keys())
    switches_raw = []
    for switch in switches:
        switches_raw.append([switch[0]+switch[1]*tiledim[0],switches[switch]])
    filecontent = [world,start,end,doors_raw,switches_raw]
    with open("data\levels\level2.json","w")as file1:
        json.dump(filecontent,file1)

def reset():
    player.curtile = (start[0]+1,start[1]+3)
    player.hitbox.bottom = (start[1]+3)*tilesize
    player.hitbox.centerx = (start[0]+1)*tilesize + tilesize//2
    player.stop_moving()
    for door in doors:
        doors[door][0] = True

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

    reset()

# Run Functions
runsegments = {
    "mainmenu" : 1,
    "levelselect" : 0,
    "gameplay" : 0,
    "worldedit" : 0,
    "won":0,
    "paused" : 0
}
levels = []
    

def levelselectrun(events):
    global curlevel
    for event in events:
        if event.type == KEYDOWN:
            if event.key == K_UP:
                curlevel -= 1
            elif event.key == K_DOWN:
                curlevel += 1
            elif event.key == K_RETURN:
                if runsegments["gameplay"]:
                    openworld("data/levels/"+levels[curlevel])
                    optimize_level()
                    runsegments["levelselect"] = 0
            if curlevel < 0:
                curlevel = no_of_levels - 1
            elif curlevel >= no_of_levels:
                curlevel = 0

    win.fill(COLOR[6])

    for i in range(0,no_of_levels):
        if i == curlevel:
            text = text1.render(levels[i][:-5].upper(),0,COLOR[0])
        else:
            text = text1.render(levels[i][:-5].upper(),0,COLOR[5])
        win.blit(text,(70,70+i*30))


    if fullscreen:
        Win.blit(pygame.transform.scale(win,monitor),(0,0))
    else:
        Win.blit(pygame.transform.scale(win,resolution),(0,0))
    pygame.display.update()

def mainmenurun(events):

    for event in events:
        if event.type == KEYDOWN:
            if event.key ==  K_1:
                runsegments["gameplay"] = runsegments["levelselect"] = 1
                runsegments["mainmenu"] = 0
            elif event.key == K_2:
                runsegments["worldedit"] = runsegments["levelselect"] = 1
                runsegments["mainmenu"] = 0
            elif event.key == K_3:
                print("Coming Soon")
            elif event.key == K_4:
                print("Coming Soon")
            elif event.key == K_5:
                pygame.quit()
                sys.exit()
    
    win.fill(COLOR[6])

    texts = (
        text2.render("1.PLAY",0,COLOR[5]),
        text2.render("2.WORLD EDIT",0,COLOR[5]),
        text2.render("3.SCORES",0,COLOR[5]),
        text2.render("4.SETTINGS",0,COLOR[5]),
        text2.render("5.QUIT",0,COLOR[5])
    )
    for i in range(0,5):
        win.blit(texts[i],(200,200 + i*75))

    if fullscreen:
        Win.blit(pygame.transform.scale(win,monitor),(0,0))
    else:
        Win.blit(pygame.transform.scale(win,resolution),(0,0))
    pygame.display.update()

def gameplayrun(events): 

    global cycle
    cycle += 1

    for event in events:

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
                if event.key == K_DOWN:
                    if (player.curtile[0],player.curtile[1]-1) in switches:
                        for door in switches[(player.curtile[0],player.curtile[1]-1)]:
                            if door in doors:
                                doors[door][0] = not doors[door][0]
                            else:
                                switches[(player.curtile[0],player.curtile[1]-1)].remove(door)
                                 

        elif event.type == KEYUP:
            
            if event.key == K_LEFT or event.key == K_RIGHT:
                if player.moving:
                    player.stop_moving()

    if player.curtile == (end[0]+1,end[1]+3):
        runsegments["won"] = 1
        print("win")

    for door in doors:
        d = doors[door]
        if d[0]  and d[1].height < tilesize*4:
            d[1].height += tilesize//4
        elif not d[0] and d[1].height > 0:
            d[1].height -= tilesize//4

    win.fill((30,30,30))

    for door in doors:
        pygame.draw.rect(win,(0,230,230),doors[door][1])

    for y in range(tiledim[1]):
        for x in range(tiledim[0]):
            if world[y][x] == 1:
                pygame.draw.rect(win,(0,0,240),(x*tilesize,y*tilesize,tilesize,tilesize))
    pygame.draw.rect(win,(0,230,0),(start[0]*tilesize,start[1]*tilesize,tilesize*3,tilesize*3),3)
    pygame.draw.rect(win,(230,0,0),(end[0]*tilesize,end[1]*tilesize,tilesize*3,tilesize*3),3)

    for switch in switches:
        pygame.draw.rect(win,(230,230,0),(switch[0]*tilesize,switch[1]*tilesize,tilesize,tilesize))

    player.resolve()

    player.draw(win)

    if fullscreen:
        Win.blit(pygame.transform.scale(win,monitor),(0,0))
    else:
        Win.blit(pygame.transform.scale(win,resolution),(0,0))

    pygame.display.update()

def worldeditrun(events):

    global start,end,laying_tool,laying_action

    if laying_tool == 1:
        if mouse[0]:
            world[mtile[1]][mtile[0]] = 1
        elif mouse[2]:
            world[mtile[1]][mtile[0]] = 0
    
    for event in events:
        if event.type == KEYDOWN:
            if event.key == K_1:
                laying_tool = 1
            elif event.key == K_2:
                laying_tool = 2
            elif event.key == K_3:
                laying_tool = 3
            elif event.key == K_4:
                laying_tool = 4
            elif event.key == K_5:
                laying_tool = 5
            elif event.key == K_6:
                laying_tool = 6
                laying_action = None
            
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                tile_id = mtile[1]*tiledim[0] + mtile[0]
                if laying_tool == 2:
                    start = mtile
                elif laying_tool == 3:
                    end = mtile 
                elif laying_tool == 4:                    
                    if tile_id not in doors:
                        doors[tile_id] = [True,pygame.Rect(mtile[0]*tilesize,mtile[1]*tilesize,tilesize,tilesize*4)]
                elif laying_tool == 5:
                    if mtile not in switches:
                        switches[mtile] = []
                elif laying_tool == 6:
                    if laying_action == None:
                        if mtile in switches:
                            laying_action = mtile  
                    else:
                        for door in doors:
                            if (tile_id in range(door,door+tiledim[0]*4,tiledim[0])):
                                
                                if door in switches[laying_action]:
                                    switches[laying_action].remove(door)
                                else:
                                    switches[laying_action].append(door)
                                
                                break
                        laying_action = None

            
            elif event.button == 3:
                if laying_tool == 4:
                    tile_id = mtile[1]*tiledim[0] + mtile[0]
                    if tile_id in doors:
                        del doors[tile_id]
                elif laying_tool == 5:
                    if mtile in switches:
                        del switches[mtile]

def wonrun(events):

    for event in events:
        
        if event.type == KEYDOWN:
            if event.key == K_1:
                pass
            elif event.key == K_2:
                reset()
                runsegments["won"] = 0
            elif event.key == K_3:
                runsegments["won"] = 0
                runsegments["levelselect"] = 1
            elif event.key == K_4:
                runsegments["won"] = runsegments["gameplay"] = 0
                runsegments["mainmenu"] = 1

    texts = (
        text2.render("1.NEXT",0,COLOR[5]),
        text2.render("2.RESET",0,COLOR[5]),
        text2.render("3.LEVELSELECT",0,COLOR[5]),
        text2.render("4.MAINMENU",0,COLOR[5])
    )

    pygame.draw.rect(win,COLOR[5],(200,100,880,520))
    pygame.draw.rect(win,COLOR[6],(210,110,860,500))

    for i in range(0,4):
        win.blit(texts[i],(230,130 + i*75))

    if fullscreen:
        Win.blit(pygame.transform.scale(win,monitor),(0,0))
    else:
        Win.blit(pygame.transform.scale(win,resolution),(0,0))

    pygame.display.update()

def redraw():
    win.fill((30,30,30))

    for door in doors:
        pygame.draw.rect(win,(0,230,230),doors[door][1])

    for y in range(tiledim[1]):
        for x in range(tiledim[0]):
            if world[y][x] == 1:
                pygame.draw.rect(win,(0,0,240),(x*tilesize,y*tilesize,tilesize,tilesize))
    pygame.draw.rect(win,(0,230,0),(start[0]*tilesize,start[1]*tilesize,tilesize*3,tilesize*3),3)
    pygame.draw.rect(win,(230,0,0),(end[0]*tilesize,end[1]*tilesize,tilesize*3,tilesize*3),3)

    for switch in switches:
        pygame.draw.rect(win,(230,230,0),(switch[0]*tilesize,switch[1]*tilesize,tilesize,tilesize))

    if runsegments["worldedit"]:
        mouse_rect = [mtile[0]*tilesize,mtile[1]*tilesize,tilesize,tilesize]
        if laying_tool == 2 or laying_tool == 3:
            mouse_rect[2]=mouse_rect[3]=tilesize*3
        if laying_tool == 4:
            mouse_rect[3] = tilesize*4
        if laying_tool == 6:
            pygame.draw.circle(win,COLOR[5],mpos,5)
            if laying_action:
                pygame.draw.line(win,COLOR[5],(laying_action[0]*tilesize+tilesize//2,laying_action[1]*tilesize+tilesize//2),mpos,3)
                pygame.draw.rect(win,COLOR[5],(laying_action[0]*tilesize,laying_action[1]*tilesize,tilesize,tilesize))
        else:
            pygame.draw.rect(win,COLOR[laying_tool-1],mouse_rect,3)
        
    
    if fullscreen:
        Win.blit(pygame.transform.scale(win,monitor),(0,0))
    else:
        Win.blit(pygame.transform.scale(win,resolution),(0,0))

    pygame.display.update()

levels = os.listdir("./data/levels")
no_of_levels = len(levels)
curlevel = 0

while True:

    clock.tick(FPS)
     
    pygameevent = pygame.event.get()
    mouse = pygame.mouse.get_pressed()
    mpos = pygame.mouse.get_pos()
    keys = pygame.key.get_pressed()
    mtile = (mpos[0]//tilesize,mpos[1]//tilesize)

    for event in pygameevent:
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit("__main__")
            if event.key == K_LCTRL:
                pass               
            
            if event.key == K_f:
                fullscreen = not fullscreen
                if fullscreen:                    
                    Win = pygame.display.set_mode(monitor,FULLSCREEN)
                else:
                    Win = pygame.display.set_mode(resolution)

    if runsegments["mainmenu"]:
        mainmenurun(pygameevent)
    elif runsegments["levelselect"]:
        levelselectrun(pygameevent)
    elif runsegments["gameplay"]:
        if runsegments["won"]:
            wonrun(pygameevent)
        else:
            gameplayrun(pygameevent)
    elif runsegments["worldedit"]:
        worldeditrun(pygameevent)

    