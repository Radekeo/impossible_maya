#cmds.select(all=True)
#cmds.delete()

STEP_PROPS = (.75,.75, 3.0)
BALL_PROPS = (6, 1, .2)
BLOCKS = 4
CONST = 1


class Scene:
    def __init__(self):
        sx,sy,radius = BALL_PROPS
        self.w, self.d, self.h = STEP_PROPS
        self.staircase = []
        self.group_name = ''
        self.ball = Ball(sx,sy,radius)
        self.building = Building(5, 4, CONST+1.2)
        self.placeObjects()
        
        
    def placeObjects(self):
        # create blocks of stairs
        self.drawBlocks()
        self.ball.drawBall()
        self.building.drawBuilding()

    def createStaircaseGroup(self, i):
        # Create a group for the staircase
        group_name = 'staircase_group' + f'{i}'
        self.group_name = cmds.group(empty=True, name=group_name)
        return self.group_name
        
    def drawBlocks(self):
        stairs = [1,4,5,3]
        moveX = moveY = moveZ = 0
        counter = 0
        axis = ''
        for i in range(BLOCKS):
            self.createStaircaseGroup(i)             
            for s in range(stairs[i]):
                name = 'step' + f'{counter}'
                if i == 0:
                    moveX, moveY, moveZ = self.w, CONST+self.h/2, 0
                    axis = 'X'
                else:
                    if i == 1:
                        moveX = 0
                        moveY = CONST+self.h/2
                        moveZ = self.d * s
                        axis = 'Z'
                    elif i == 2:
                        moveX = self.w * (s+1)
                        moveY = CONST+self.h/2
                        axis = 'X'
                    else:
                        moveY = CONST+self.h/2
                        moveZ = -(self.d *(s-2))
                        axis = 'Z'

                self.staircase.append(Steps(name, self.w, self.d, self.h, axis))
                cmds.move(moveX, moveY, moveZ, name)
                cmds.parent(name, self.group_name)
                counter += 1
                self.h = self.h - 0.125
        return


    def update(self):
        self.ball.update(self.staircase)
        

class Ball:
    def __init__(self, sx, sy, radius):
        self.sx = sx
        self.sy = sy
        self.r = radius
        self.name = 'ball'
        
    def drawBall(self):
        cmds.polySphere(name=self.name, sx=self.sx, sy=self.sy, r=self.r)
        return

    
    def bounce_curve(self, t, start_pos, mid_pos, end_pos):
        # x = ((1 - t) * (1 - t) * p0.X) + (2 * t * (1 - t) * p1.X) + (t * t * p2.X)
        # y = ((1 - t) * (1 - t) * p0.Y) + (2 * t * (1 - t) * p1.Y) + (t * t * p2.Y)

        x = (1-t)**2 * start_pos[0] + 2*t*(1-t)*mid_pos[0] + t**2 * end_pos[0]
        y = (1-t)**2 * start_pos[1] + 2*t*(1-t)*mid_pos[1] + t**2 * end_pos[1]       
        new_pos = (x,y)

        return new_pos

    def deform(self, frame, start_frame, end_frame, squash_factor):
        # Calculate squash factor based on the frame within the bouncing phase
        squash_factor = max(1 - abs(frame - ((start_frame + end_frame) / 2)) / (end_frame - start_frame) * squash_factor, 0.5)

        # Set keyframes for scaling attributes
        cmds.setKeyframe(self.name, attribute='scaleX', time=frame, value=squash_factor)
        cmds.setKeyframe(self.name, attribute='scaleY', time=frame, value=1 / squash_factor)
        cmds.setKeyframe(self.name, attribute='scaleZ', time=frame, value=squash_factor)

    def reform(self, frame, start_frame, end_frame):
        # Set keyframes for scaling attributes to return to original shape
        cmds.setKeyframe(self.name, attribute='scaleX', time=frame, value=1)
        cmds.setKeyframe(self.name, attribute='scaleY', time=frame, value=1)
        cmds.setKeyframe(self.name, attribute='scaleZ', time=frame, value=1)

    def rotate(self, rotation):
        # rotation *= (frame - start_frame) / (end_frame - start_frame)

        # Set keyframe for rotation attribute
        cmds.setKeyframe(self.name, attribute='rotateY', value=rotation)
        cmds.setKeyframe(self.name, attribute='rotateX', value=rotation)

        return


    def update(self, lst):
        KF = 15
        squash = 0.4
        rotation = 0
        bounce_height = 2.0
        for i in range(len(lst)):
            start_frame = i * KF + 1
            end_frame = (i + 1) * KF

            # Calculate bouncing motion between steps

            

            start_y = cmds.getAttr(f'{lst[i].name}.ty') + CONST + self.r
            start_x, start_z = cmds.getAttr(f'{lst[i].name}.tx'), cmds.getAttr(f'{lst[i].name}.tz')
            if i == len(lst)-1:
                end_x, end_z = cmds.getAttr(f'{lst[0].name}.tx'), cmds.getAttr(f'{lst[0].name}.tz')
                end_y = cmds.getAttr(f'{lst[0].name}.ty') + CONST + self.r
            else:
                end_x, end_z = cmds.getAttr(f'{lst[i+1].name}.tx'), cmds.getAttr(f'{lst[i+1].name}.tz')
                end_y = cmds.getAttr(f'{lst[0].name}.ty') + CONST  + self.r

            x_dist, z_dist = end_x - start_x, end_z - start_z

            # start_pos = (start_x, start_y, start_z)
            mid_pos = (start_x+ x_dist/2, start_y + bounce_height + self.r, start_z + z_dist/2)
            # end_pos = (end_x, end_y, end_z)

            ##################start_pos_2D###########
            if i == len(lst)-1:
                start_pos_2D = (start_z, start_y)
                mid_pos_2D = (mid_pos[2], mid_pos[1])
                end_pos_2D = (end_z, end_y)
            
            elif i < len(lst)-1:
                if i==0 or lst[i+1].axis == 'Z':
                    start_pos_2D = (start_z, start_y)
                    mid_pos_2D = (mid_pos[2], mid_pos[1])
                    end_pos_2D = (end_z, end_y)
                else:
                    start_pos_2D = (start_x, start_y)
                    mid_pos_2D = (mid_pos[0], mid_pos[1])
                    end_pos_2D = (end_x, end_y)

            

            for frame in range(start_frame, end_frame+1):
                step_time = ((frame-1) % KF)/ KF
                rot = 360/13/KF
                rotation = rotation + rot

                # bounce
                bounce_pos = self.bounce_curve(step_time, start_pos_2D, mid_pos_2D, end_pos_2D)
                if i == len(lst)-1:
                    new_x = cmds.getAttr(f'{lst[i].name}.tx') + ((x_dist/KF) * ((frame-1)%KF))
                    new_z = bounce_pos[0]

                elif i<len(lst)-1:
                    if i == 0 or lst[i+1].axis == 'Z' or i==len(lst)-1:
                        new_x = cmds.getAttr(f'{lst[i].name}.tx') + ((x_dist/KF) * ((frame-1)%KF))
                        new_z = bounce_pos[0]
                    else:
                        new_x = bounce_pos[0]
                        new_z = cmds.getAttr(f'{lst[i].name}.tz') + ((z_dist/KF) * ((frame-1)%KF))
                new_y = bounce_pos[1]
                

                # Translation
                cmds.setKeyframe(self.name, attribute='translateX', time=frame, value=new_x)
                cmds.setKeyframe(self.name, attribute='translateY', time=frame, value=new_y)
                cmds.setKeyframe(self.name, attribute='translateZ', time=frame, value=new_z)

                # Squash and Stretch
                if start_frame <= frame <= end_frame:
                    self.deform(frame, start_frame, end_frame, squash)
                else:
                    self.reform(frame, start_frame, end_frame)

                # Rotation
                self.rotate(rotation)

                
                
                print(f'Keyframe {frame} out of {end_frame}:')
                print(f'Ball at {new_x},{new_y},{new_z}')

            
        return
        
    
class Steps:
    def __init__(self, name, width, depth, height, axis):
        self.w = width
        self.d = depth
        self.h = height
        self.axis = axis
        self.name = name
        self.drawStep()

    def drawStep(self):
        cmds.polyCube(w=self.w, d=self.d, h=self.h, name=self.name)
        return

class Building:
    def __init__(self, width, depth, height):
        self.w = width
        self.d = depth
        self.h = height
        self.group_name = cmds.group(empty=True, name='building')
  

    def drawBuilding(self):
        moveX,moveY,moveZ = 1.75, self.h/2, 1
        cmds.polyCube(w=self.w, d=self.d, h=self.h, name='block1')
        cmds.move(moveX, moveY, moveZ, 'block1')
        cmds.parent('block1', self.group_name)
        return

beachBallScene = Scene()
beachBallScene.update()
