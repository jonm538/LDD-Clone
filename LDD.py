from panda3d.core import CollisionHandlerPusher
from panda3d.core import Plane, PlaneNode, Vec3, Point3
from direct.showbase.ShowBase import ShowBase
from panda3d.core import CardMaker
from direct.gui.DirectGui import DirectFrame, DirectButton
from direct.gui.DirectGui import DGG
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import CollisionTraverser, CollisionHandlerQueue, CollisionNode, CollisionRay, BitMask32
from panda3d.core import TextureStage
from panda3d.core import Texture, TransparencyAttrib, TextureStage
from math import sin, cos, radians
from panda3d.core import NodePath
from direct.gui.DirectGui import DirectScrolledFrame
import os
from panda3d.core import GraphicsOutput, Texture
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import LColor
from panda3d.core import RenderState
from panda3d.core import BitMask32
from panda3d.core import LPoint2f
import xml.etree.ElementTree as ET
import math
from panda3d.core import WindowProperties
import collections
from panda3d.core import PointLight, PerspectiveLens
from panda3d.core import TexturePool
from panda3d.core import load_prc_file_data
from panda3d.core import DirectionalLight
from panda3d.core import AmbientLight, DirectionalLight, Point3








def hex_to_rgb(hex):
    r = int(hex[1:3], 16)
    g = int(hex[3:5], 16)
    b = int(hex[5:7], 16)
    return r/255, g/255, b/255, 1 # Normalize to 0-1 range and return as RGBA
class MyApp(ShowBase):


    
    def __init__(self):
        ShowBase.__init__(self)
        self.brick_geom_folder_path = '/Users/jonathan/Documents/Resources/brick_geometry'  # Replace with the actual folder path


        

        self.brick_files = [
            os.path.join(self.brick_geom_folder_path, file)
            for file in os.listdir(self.brick_geom_folder_path)
            if os.path.isfile(os.path.join(self.brick_geom_folder_path, file)) and file != '.DS_Store'
        ]
        
        self.brick_files = sorted(self.brick_files)

        self.brick_types = {}
        for i, brick_file in enumerate(self.brick_files, start=1):
            self.brick_types[f'brick{i}'] = brick_file


        self.selectMove = False

        self.accept('mouse1', self.on_left_click)  # Left click
        self.hover_text = None
        self.hover_text_frame = None
        self.taskMgr.add(self.update_model_position, "update_model_position")
        self.taskMgr.add(self.check_mouse, "check_mouse")
        self.mousewatch = False
        self.picked_obj = None
        self.accept('b', self.toggle_color_selection_window)
        self.create_color_selection_window()
        self.taskMgr.add(self.check_mouse_position, 'check_mouse_position')
        self.current_tool = None

        self.accept('mouse3', self.start_orbit_drag)
        self.accept('mouse3-up', self.stop_orbit_drag)
        self.accept('shift-mouse3', self.start_drag)
        self.accept('shift-mouse3-up', self.stop_drag)
        self.taskMgr.add(self.pan_task, 'pan_task')
        self.taskMgr.add(self.orbit_task, 'orbit_task')
        self.is_dragging = False
        self.last_mouse_pos = None
        self.delta = None
        self.selected_color = None
        self.last_mouse_pos = None
        self.curr_mouse_pos = None
        self.dx = None
        self.dy = None
        self.taskMgr.add(self.update, 'update')
        self.taskMgr.add(self.orbit_update, 'orbit_update')
        self.dragged = False
        self.is_orbit_dragging = False
        self.shown_buttons_count = {}
        self.category_buttons = {}

        
        # Initialize button dictionaries
        self.brick_buttons = {}
        self.cat_buttons = {}

        # Initialize slot positions
        self.category_slot = 1
        self.brick_slot = {}
        self.brick_slot = 1
        self.create_gui()
        self.create_navigation_buttons()
        self.mouse_on_frame = False
        self.mode = None


        # Load an image as a texture
        #self.loading_image = TexturePool.loadTexture('/Users/jonathan/Documents/Resources/LDD Splash Screen.png')

        # Create a card to display the texture
        #card_maker = CardMaker('loading_screen')
        #card_maker.set_frame(-1, 1, -1, 1)  # cover the entire screen
        #card = self.render2d.attach_new_node(card_maker.generate())
        #card.setTexture(self.loading_image)
        
        # Set camera position and orientation
        self.camera.setPos(764, -650, 890)
        self.camera.setHpr(30, -30, 0)

        # Reset trackball position
        self.disableMouse() 

        
        plight = PointLight("plight")
        plight.setColor((1,1,1,1))
        self.plnp = self.render.attachNewNode(plight)
        self.render.setLight(self.plnp)
        self.plnp.setPos (764, -650, 890)



        # Create a plane at z=0
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
        planeNode = PlaneNode('plane')
        planeNode.setPlane(self.plane)
        self.render.attachNewNode(planeNode)

        cm = CardMaker("ground")
        cm.setFrame(0, 800, 0, 800)  # adjust as necessary
        ground = self.render.attachNewNode(cm.generate())
        ground.setPos(0, 0, 0)  # adjust as necessary
        ground.setP(-90)
        ground.setTwoSided(True)
        self.center = Point3(800 / 2, 800 / 2, 0)
        self.camera.lookAt(self.center)



        texture = self.loader.loadTexture('/Users/jonathan/Documents/Resources/TileFloor.png')
        texture.setWrapU(texture.WM_repeat)
        texture.setWrapV(texture.WM_repeat)
        
        # Load the alpha texture
        alphaTex = self.loader.loadTexture("/Users/jonathan/Documents/Resources/TileFloorAlpha.png")
        
        # Create the TextureStage
        ts = TextureStage('ts')
        ts.setMode(TextureStage.MModulate)
        
        # Set the texture
        ground.setTexture(ts, texture)
        
        # Set the alpha texture
        tsAlpha = TextureStage('tsAlpha')
        ground.setTexture(tsAlpha, alphaTex)
        
        # Set transparency
        ground.setTransparency(TransparencyAttrib.MDual, 1)
        ground.setTexScale(tsAlpha, 16, 16)

        # Set texture scale
        ground.setTexScale(ts, 16, 16)

        self.selected = False
        self.hovered_brick = None

        self.setBackgroundColor(0.9, 0.9, 0.9, 1)
        self.create_toolbar_options()
        self.current_brick_type = None
        self.model = None
        self.locked = False
        self.create_toolbar()
        
        self.placed_bricks = []  # keep track of all bricks placed

        self.hoveringOver = False
        self.placing_brick = False
        self.moveSelect = False
        
        self.picker = CollisionTraverser()
        self.pq = CollisionHandlerQueue()
        self.accept('c', self.clone_selected)
        self.accept('wheel_up', self.zoom_in)
        self.accept('wheel_down', self.zoom_out)
        
        

        self.accept('arrow_left', self.move_camera, [-30, 0, 0])
        self.accept('arrow_right', self.move_camera, [30, 0, 0])
        self.accept('arrow_up', self.move_camera, [0, 0, 30])
        self.accept('arrow_down', self.move_camera, [0, 0, -30])

        # Create a collision node for the picker ray
        picker_node = CollisionNode('pickerNode')
        # Only collide with models (which should be in the mask 0x1)
        picker_node.setFromCollideMask(BitMask32.bit(1))
        # Don't actually produce collisions with the models
        picker_node.setIntoCollideMask(BitMask32.allOff())
        # Attach the picker_node to a CollisionRay
        picker_ray = CollisionRay()
        picker_node.addSolid(picker_ray)
        # Attach the collision node to camera
        self.picker_node_path = self.camera.attachNewNode(picker_node)
        # Add the picker_node_path to the CollisionTraverser
        self.picker.addCollider(self.picker_node_path, self.pq)

       # self.mode = 'PLACE'  # Set default mode to 'PLACE'


    def render_obj_to_texture(self, obj_path, card):
        # Load the model
        model = loader.loadModel(obj_path)
        print(model)    
        model.setColorScale(0.5, 0, 0.5, 1)
        
        min_point, max_point = model.get_tight_bounds()
        center_point = (min_point + max_point) / 2

        # Create an offscreen buffer
        buffer = self.win.make_texture_buffer('renderBuffer', 512, 512)
        buffer.set_sort(-100)  # This buffer should be rendered before the main window

        # Set up a display region and a camera for the buffer
        display_region = buffer.make_display_region()
        offscreen_camera = self.make_camera(buffer)
        offscreen_camera.node().get_lens().set_near_far(1, (max_point - min_point).length() * 2)

        # Add a point light to the offscreen camera
        light = PointLight('pointLight')
        light_node = offscreen_camera.attach_new_node(light)
        light_node.set_pos(center_point + Point3(0, 0, 10))  # Adjust light position as necessary
        model.set_light(light_node)



        # Clear the buffer's display region before rendering
        display_region.set_clear_color_active(True)
        display_region.set_clear_depth_active(True)
        display_region.set_clear_color((1, 1, 1, 1))  # Clear to white

        # Reparent the model to the render, not to the camera
        model.reparent_to(self.render)
        #offscreen_camera.setHpr(30, -30, 0)


        # Move the offscreen camera back a bit so that it can see the model
        dy = max_point.y - min_point.y
        offscreen_camera.set_pos(center_point + Point3(0, -2 * dy, 0))  # Adjust this factor as needed
        offscreen_camera.look_at(center_point+ Point3(0,0,-.5))
        model.setHpr(30, 90, -60)  # Rotate 180 degrees on the Z-axis and 90 degrees on the X-axis


        # Render the scene and grab the image to the texture
        self.graphicsEngine.render_frame()
        buffer.save_screenshot('debug.png')

        # Set the buffer's texture to the Card
        card.setTexture(buffer.get_texture())

        # Clean up
        model.remove_node()
        self.graphicsEngine.remove_window(buffer)

    def clear_load_screen(self, card):
        card.remove_node()

    def on_mouse_enter_frame(self, event):
        self.mouse_on_frame = True

    def on_mouse_exit_frame(self, event):
        self.mouse_on_frame = False
        
    def reset_view(self):
        self.camera.setPos(764, -650, 890)
        self.camera.lookAt(self.center)
        
    def start_drag(self):
        if self.mouseWatcherNode.hasMouse():
            self.last_mouse_pos = self.mouseWatcherNode.getMouse()  # this is where you start dragging
            self.is_dragging = True
            self.dragged = False

    def stop_drag(self):
        self.is_dragging = False
        self.dragged = True
        if self.mouseWatcherNode.hasMouse(): 
            self.curr_mouse_pos = self.mouseWatcherNode.getMouse()  # this is where you stop dragging

    def pan_task(self, task):
        if self.is_dragging:
            if self.mouseWatcherNode.hasMouse():
                new_mouse_pos = LPoint2f(self.mouseWatcherNode.getMouse())  # get the new position of the mouse
                if new_mouse_pos is not None and self.last_mouse_pos is not None: 
                    self.dx = new_mouse_pos.getX() - self.last_mouse_pos.getX()
                    self.dy = new_mouse_pos.getY() - self.last_mouse_pos.getY()
                    self.last_mouse_pos = LPoint2f(new_mouse_pos)  # update last_mouse_pos for next cycle
                else:
                    return task.cont
        return task.cont



    def update(self, task):
        if not self.dragged and self.is_dragging:
            self.camera.setPos(self.camera.getX() - (70*self.dx), self.camera.getY(), self.camera.getZ() - (70*self.dy))
            self.delta = None
        return task.cont


    def start_orbit_drag(self):
        if self.mouseWatcherNode.hasMouse():
            self.last_mouse_pos = self.mouseWatcherNode.getMouse()  # this is where you start dragging
            self.is_orbit_dragging = True
            self.dragged = False

    def stop_orbit_drag(self):
        self.is_orbit_dragging = False
        self.dragged = True
        if self.mouseWatcherNode.hasMouse(): 
            self.curr_mouse_pos = self.mouseWatcherNode.getMouse()  # this is where you stop dragging

    def orbit_task(self, task):
        if self.is_orbit_dragging:
            if self.mouseWatcherNode.hasMouse():
                new_mouse_pos = LPoint2f(self.mouseWatcherNode.getMouse())  # get the new position of the mouse
                if new_mouse_pos is not None and self.last_mouse_pos is not None: 
                    self.dx = new_mouse_pos.getX() - self.last_mouse_pos.getX()
                    self.dy = new_mouse_pos.getY() - self.last_mouse_pos.getY()
                    self.last_mouse_pos = LPoint2f(new_mouse_pos)  # update last_mouse_pos for next cycle
                else:
                    return task.cont
        return task.cont


    def orbit_update(self, task):
        if self.is_orbit_dragging and not self.dragged:
            # Get the current position of the camera
            x, y, z = self.camera.getPos() - self.center  # Adjusted position

            # Calculate the distance from the point of interest (center of ground plane)
            r = ((x ** 2) + (y ** 2) + (z ** 2)) ** 0.5

            # Calculate the polar angle (theta) and azimuthal angle (phi)
            theta = math.atan2(y, x)  # Angle with the x-axis in the xy-plane
            phi = math.acos(z / r)    # Angle with the z-axis

            # Adjust theta and phi based on the mouse's movement
            theta -= 3*self.dx
            phi += 3*self.dy

            # Ensure phi is within bounds (prevents flipping over at zenith)
            phi = max(0.1, min(math.pi, phi))

            # Calculate the new position of the camera
            x = r * math.sin(phi) * math.cos(theta)
            y = r * math.sin(phi) * math.sin(theta)
            z = r * math.cos(phi)

            # Update the camera's position (add the center back)
            self.camera.setPos(x + self.center[0], y + self.center[1], z + self.center[2])

            # Keep the camera focused on the center of the ground plane
            self.camera.lookAt(self.center)

        return task.cont

        
    def move_camera(self, dx, dy, dz):
        # Move the camera by the specified amount
        self.camera.setPos(self.camera.getPos() + Vec3(dx, dy, dz))
        cameraloc = self.camera.getPos()
        #print(cameraloc)


    def create_navigation_buttons(self):
        self.zoom_in_button = DirectButton(
            text="Zoom In",
            pos=(0, 0, -0.95),
            scale=.05,
            pressEffect=False,
            command=self.zoom_in, 
            relief=DGG.FLAT,
            text_fg=(1,1,1,1),
            frameColor=(0,0,1,1),
            rolloverSound=None,
            clickSound=None)

        self.zoom_out_button = DirectButton(
            text="Zoom Out",
            pos=(0, 0, -0.85),
            scale=.05,
            pressEffect=False,
            command=self.zoom_out, 
            relief=DGG.FLAT,
            text_fg=(1,1,1,1),
            frameColor=(0,0,1,1),
            rolloverSound=None,
            clickSound=None)

        self.reset_view_button = DirectButton(
            text="Reset View",
            pos=(-.25, 0, -0.95),
            scale=.05,
            pressEffect=False,
            command=self.reset_view, 
            relief=DGG.FLAT,
            text_fg=(1,1,1,1),
            frameColor=(0,0,1,1),
            rolloverSound=None,
            clickSound=None)
                                 
                                 
                                       
        #self.zoomButton.bind(DGG.B1RELEASE, stop_zoom)
    def zoom_in(self):
        """This function is called when the mouse wheel is scrolled up."""
        direction = self.center - self.camera.getPos()  # Get the direction vector
        direction.normalize()  # Normalize the vector to have a length of 1
        self.camera.setPos(self.camera.getPos() + direction * 25)  # Move 5 units closer

    def zoom_out(self):
        """This function is called when the mouse wheel is scrolled down."""
        direction = self.center - self.camera.getPos()  # Get the direction vector
        direction.normalize()  # Normalize the vector to have a length of 1
        self.camera.setPos(self.camera.getPos() - direction * 25)  # Move 5 units farther

    def check_mouse_position(self, task):
        if base.mouseWatcherNode.hasMouse():
            # Get the current mouse position in 2D GUI coordinates
            mpos = base.mouseWatcherNode.getMouse()
            
            # Get the frame size of the color selection window
            left, right, bottom, top = self.color_selection_window['frameSize']
            
            # If the mouse is not within the boundaries, hide the window
            if not (left < mpos.getX() < right and bottom < mpos.getY() < top):
                self.color_selection_window.hide()

        return task.cont


    def create_color_selection_window(self):
        self.color_selection_window = DirectFrame(
                parent = self.aspect2d,  # parent to attach the frame to
                frameSize = (-.5, .5, -.2, 1),  # size of the frame
                frameColor = (1, 1, 1, 1),  # color of the frame (red, green, blue, alpha)
                pos = (.3, 0, -.2)  # position of the frame

            )  
        self.color_selection_window.hide()

        colors = [
            (1,0.5,0.7,1),#white
            hex_to_rgb("#05131D"), #black
            hex_to_rgb("#6C6E68"), #dark stone gray
            hex_to_rgb("#A0A5A9"), #medium stone gray
            hex_to_rgb("#FFFFFF"), #white
            hex_to_rgb("#720E0F"), #new dark red
            hex_to_rgb("#C91A09"), #bright red
            hex_to_rgb("#352100"), #dark brown
            hex_to_rgb("#582A12"), #reddish brown
            hex_to_rgb("#A0BCAC"), #sand green
            hex_to_rgb("#9B9A5A"), #olive green
            hex_to_rgb("#E4CD9E"), #tan
            hex_to_rgb("#A95500"), #dark orange
            hex_to_rgb("#B3D7D1"),  # Aqua
            hex_to_rgb("#4B9F4A"),  # Bright Green
            hex_to_rgb("#0055BF"),  # Bright Blue
            hex_to_rgb("#F8BB3D"),  # Flame Yellowish Orange
            hex_to_rgb("#CD6298"),  # Bright Reddish Lilac
            ]
        num_columns = 8
        for i, color in enumerate(colors):
            column = i % num_columns  # Calculate the column number based on the index
            row = i // num_columns  # Calculate the row number based on the index

            # Calculate position based on column and row
            x_pos = -.425 + column * 0.12  # Adjust as necessary
            y_pos = 0.8 - row * 0.25  # Adjust as necessary
            color_button_pos = (x_pos, 0, y_pos)

            button = DirectButton(
                parent=self.color_selection_window,
                frameColor=color,
                pos =color_button_pos,
                command=self.set_color(color),
                extraArgs=[color],
                #relief=DGG.FLAT,
                scale = 0.5,  # Make the button a little square
                #stateColors=[(color + (1,))]*4
                # additional configuration...
            )
            button.setBin('gui-popup', 0)

            
            def on_enter(self, event, button=button, color=color):
                button_pos = button.getPos()
                flat_pos = (button_pos[0], button_pos[2])
                button.tooltip = self.create_color_tooltip(color, flat_pos)


            def on_exit(button=button):
                if hasattr(button, 'tooltip'):
                    button.tooltip.destroy()
                    del button.tooltip

                button.bind(DGG.ENTER, self.on_enter)
            #button.bind(DGG.ENTER, lambda _: on_enter())
                button.bind(DGG.EXIT, lambda _: on_exit())


    def create_color_tooltip(color, pos):
        text = f"R:{color[0]:.2f}, G:{color[1]:.2f}, B:{color[2]:.2f}"
        return DirectLabel(
            parent=button,
            text=text,
            pos=(pos[0] + 0.1, pos[1], pos[2] + 0.1),  # Adjust the offset as necessary
            scale=.05,
            frameColor=(1, 1, 1, 1),
        )
    def set_color(self, color):
        ###print("set color")
        self.selected_color = color
        #print(self.selected_color)

    def toggle_color_selection_window(self):
        print("making colors")
        if self.color_selection_window.is_hidden():
            self.color_selection_window.show()
        else:
            self.color_selection_window.hide()

    def clone_selected(self):
        if self.selected and self.hovered_brick is not None:  # Check if a brick is selected
            # Create a new copy of the hovered_brick
            #print(self.hovered_brick.getPos())
            cloned_brick = self.hovered_brick.copyTo(self.render)

            cloned_brick.setPos(self.hovered_brick.getPos() + Vec3(0, 0, 2))


            cloned_brick.setScale(40, 40, 40)  # adjust this as necessary

            # Add the cloned brick to the placed bricks list
            self.placed_bricks.append(cloned_brick)

            cloned_brick.setP(90)
            cloned_brick.setPos(self.hovered_brick.getPos())



            # Show a pop-up message
            self.show_clone_message()

    




    def show_clone_message(self):
        self.clone_text = OnscreenText(text='Cloned', pos=(0, 0), scale=0.07, fg=(1, 0, 0, 1), bg=(1, 1, 1, 0.7))

        # remove the text after 2 seconds
        taskMgr.doMethodLater(2, self.remove_clone_message, 'remove_clone_message')

    def remove_clone_message(self, task):
        if self.clone_text:
            self.clone_text.destroy()
            self.clone_text = None


    def set_brick_type(self, brick_type):
        print("Selected brick type:", brick_type)
        self.current_brick_type = brick_type
        self.model = None
        self.mode = 'PLACE'
        self.placing_brick = True  # Set placing_brick to True when a brick type is selected

    def moveSelect(self):
         print("okay now we're getting somewhere")

    def mouse_watch(self, task):
        self.mouseWatcherNode.hasMouse()
        mousewatch = self.mouseWatcherNode.hasMouse()
        #print("test")
        return task.cont

    def check_mouse(self, task):
       # print(self.selected)
       # print(self.hovered_brick, self.picked_obj, self.mode, self.locked)
        if self.mouseWatcherNode.hasMouse():
            mousewatch = True
            pass
        else:
            mousewatch = False
            self.picked_obj = None
            self.hovered_brick = None
        return task.cont
    
    def update_model_position(self, task):
        new_pos = Vec3()  # initialize new_pos
        if not self.locked and self.mouseWatcherNode.hasMouse():
            mouse_pos = self.mouseWatcherNode.getMouse()
            near_point = Point3()
            far_point = Point3()
            self.camLens.extrude(mouse_pos, near_point, far_point)
            near_world = self.render.getRelativePoint(self.cam, near_point)
            far_world = self.render.getRelativePoint(self.cam, far_point)
            pos3d = Point3()
            if self.plane.intersectsLine(pos3d, near_world, far_world):
                # If a brick is selected, update its position
                #if not self.locked and self.selected and self.hovered_brick is not None and not self.selectMove: #if a brick is NOT locked but IS selected
                 #   return
                    # the new position will be pos3d + Vec3(0, 0, 1)
                    #new_pos = pos3d + Vec3(0, 0, 1)
                    #new_pos.x = round(new_pos.x / 5) * 5
                    #new_pos.y = round(new_pos.y / 5) * 5
                    #new_pos.z = round(new_pos.z / 5) * 5
                    #clamped_pos = self.clamp_position(new_pos)

                    # calculate how much to move the brick in each direction
                   # delta_x = clamped_pos.x - self.hovered_brick.getX()
                    #delta_y = clamped_pos.y - self.hovered_brick.getY()
                    #delta_z = clamped_pos.z - self.hovered_brick.getZ()

                    # move the brick
                    #self.hovered_brick.setX(self.hovered_brick.getX() + delta_x)
                    #self.hovered_brick.setY(self.hovered_brick.getY() + delta_y)
                    #self.hovered_brick.setZ(self.hovered_brick.getZ() + delta_z)
                    

                if self.model is None:
                    self.load_model(pos3d)

                elif not self.locked and not self.selected and not self.selectMove:
                    print("moving")
                    new_pos = pos3d + Vec3(0, 0, 1)
                    new_pos.x = round(new_pos.x / 19) * 19
                    new_pos.y = round(new_pos.y / 19) * 19
                    new_pos.z = round(new_pos.z / 19) * 19
                    clamped_pos = self.clamp_position(new_pos)
                    self.model.setPos(clamped_pos)

            # Create a new CollisionRay and replace the old one
            picker_ray = CollisionRay()
            picker_ray.setFromLens(self.camNode, mouse_pos.getX(), mouse_pos.getY())
            picker_node = CollisionNode('pickerNode')
            picker_node.addSolid(picker_ray)
            picker_node.setFromCollideMask(BitMask32.bit(1))
            picker_node.setIntoCollideMask(BitMask32.allOff())
            self.picker_node_path.removeNode()
            self.picker_node_path = self.camera.attachNewNode(picker_node)
            self.picker.addCollider(self.picker_node_path, self.pq)
        
            self.picker.traverse(self.render)
            if self.pq.getNumEntries() > 0:
                print("got")
                self.pq.sortEntries()
                self.picked_obj = self.pq.getEntry(0).getIntoNodePath()
                if self.picked_obj != self.hovered_brick:
                    if self.hovered_brick is not None:
                        self.hovered_brick.setColorScale(1, 1, 1, 1)
                    self.picked_obj.setColorScale(0.5, 0, 0.5, 1) #purple
                    self.hovered_brick = self.picked_obj
                    print("Hovered over: ", self.picked_obj)
                    self.hoveringOver = True
                    print(self.hoveringOver)
            else:
                #self.hovered_brick = None
                if self.hovered_brick is not None and not self.selected and self.mouseWatcherNode.hasMouse():
                    self.hovered_brick.setColorScale(1, 1, 1, 1) #white
                    #self.hovered_brick = None
                    
            

            return task.cont
        
    def create_bounding_box(self, node):
        bounds = node.getTightBounds()
        min_bound, max_bound = bounds

        # Calculate dimensions
        x_dim = max_bound.getX() - min_bound.getX()
        y_dim = max_bound.getY() - min_bound.getY()
        z_dim = max_bound.getZ() - min_bound.getZ()

        # Load a cube model
        bounding_box = loader.loadModel("/Users/jonathan/Documents/Resources/other/boundingboxcube.obj")
        bounding_box.reparentTo(node)

        # Scale and position the box
        bounding_box.setScale(x_dim, y_dim, z_dim)
        bounding_box.setPos((min_bound + max_bound) / 2)
        bounding_box.setColor(0.5, 0, 0.5, 1) # purple
        bounding_box.setTransparency(TransparencyAttrib.MAlpha) # semi-transparent

        return bounding_box

    def on_left_click(self):
        if self.mode == 'PLACE':
            if self.model is not None:
                self.model.setCollideMask(BitMask32.bit(1))
                self.placed_bricks.append(self.model)  # Add the model to the list of placed bricks
                self.model = None
                self.locked = False
                self.placing_brick = False
                self.current_brick_type = None  # Reset the brick type after placing a brick
                self.mode = 'SELECT'
        elif self.mode == 'SELECT':
            if self.hovered_brick is not None:
                if not self.selected:
                    ###print("moving!")
                    self.selected = True
                    # Change the color of the children nodes
                    self.hovered_brick.setColorScale(0, 0, 1, 1)
                    print("selected:", self.selected)
                else:
                    print("deselected")
                    self.selected = False
                    # Revert the color of the children nodes
                    self.picked_obj.setColorScale(1,1,1,1)
                    self.hovered_brick = None
                    self.picked_obj = None
                    self.mode = None
        elif self.mode == 'DELETE':
            self.delete_brick(self.picked_obj)


  
    def delete_brick(self, brick):
            if self.picked_obj is not None and self.hovered_brick == self.picked_obj:
                    if self.picked_obj in self.placed_bricks:
                        self.placed_bricks.remove(self.picked_obj)
                    self.picked_obj.removeNode()  # Remove the selected object
                    self.picked_obj = None  # Clear the reference
                                
                        
    def clamp_position(self, pos):
        x = max(0, min(pos.x, 600))
        y = max(0, min(pos.y, 800))
        z = max(-500, min(pos.z, 500))
        return Point3(x, y, z)

    def get_category_id(self, brick_name):
        xml_file_path = '/Users/jonathan/Documents/Resources/Primitives/{}.xml'.format(brick_name)
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        annotations = root.find('Annotations')
        if annotations is None:
            print(f'Warning: No Annotations tag found in {xml_file_path}')
            return None
        for annotation in annotations.findall('Annotation'):
            if 'maingroupid' in annotation.attrib:
                category_id = annotation.get('maingroupid')
                ###print(f'Brick: {brick_name}, Category: {category_id}')
                return category_id
        print(f'Warning: No maingroupid attribute found in any Annotation tag in {xml_file_path}')
        return None


    def load_model(self, pos):
        model_path = self.brick_types.get(self.current_brick_type)
        if model_path is None:
            #print("No brick type selected!")
            return

        if self.model:
            self.model.removeNode()

        self.model = self.loader.loadModel(model_path)
        self.model.reparentTo(self.render)
        self.model.setScale(28, 28, 28)  # adjust this as necessary
        #self.model.setPos(pos + Vec3(0, 0, 1))  # slightly above the plane to prevent Z-fighting
        self.model.setP(90)
        
    def calculate_slot_position(self, slot):
        x_pos = -0.20 + ((slot-1) % 3) * 0.2  # Adjust as necessary
        y_pos = 2.85 - ((slot-1) // 3) * 0.25  # Adjust as necessary
        return (x_pos, y_pos)

    def scroll_up(self, event=None):
        if self.mouse_on_frame:
            # Increase the vertical scroll value by some increment, e.g., 0.1
            self.frame['verticalScroll_value'] = min(self.frame['verticalScroll_value'] + 0.1, 1)

    def scroll_down(self, event=None):
        if self.mouse_on_frame:
            # Decrease the vertical scroll value by some increment, e.g., 0.1
            self.frame['verticalScroll_value'] = max(self.frame['verticalScroll_value'] - 0.1, 0)

    def create_gui(self):

        # Create the scrolled frame
        self.frame = DirectScrolledFrame(
            parent=self.aspect2d,
            pos=(-1, 0, 0),
            frameSize=(-0.3, 0.35, -1, .8),
            canvasSize=(-0.3, 0.3, -0.3, 3),
            scrollBarWidth=0.04,
            verticalScroll_relief=DGG.SUNKEN,
            verticalScroll_frameColor=(0.5, 0.5, 0.5, 1),  # grey color for vertical scrollbar
            horizontalScroll_frameColor=(0.5, 0.5, 0.5, 1),  # grey color for horizontal scrollbar
        )
        

        self.category_buttons = {}


        brick_images_folder_path = '/Users/jonathan/Documents/Resources/brick_images' 
        brick_images_file_paths = tuple(
            os.path.join(brick_images_folder_path, file)
            for file in os.listdir(brick_images_folder_path)
            if os.path.isfile(os.path.join(brick_images_folder_path, file)) and file != '.DS_Store'
        )

        brick_geom_files = [
                file for file in os.listdir(self.brick_geom_folder_path) 
                if file.endswith('.obj')
            ]
        
        brick_images_file_paths = sorted(brick_images_file_paths)
        num_bricks = len(brick_geom_files)
        print(num_bricks, len(brick_images_file_paths))
        
        self.button_slots = {}
        
        # Get a set of all category ids.
        category_ids = {self.get_category_id(os.path.basename(brick_image).split('.')[0]) for brick_image in brick_images_file_paths}

        # Initialize the categories dictionary.
        categories = {category_id: [] for category_id in category_ids}

        categories_copy = categories.copy()

        categories = {}

        
        # Create an empty ordered dictionary

        ordered_categories = collections.OrderedDict()

        # List of category ids in the order you want them to appear
        order = [201, 203, 202, 204, 205, 206, 207, 215, 217, 216, 277, 225, 265, 292, 301, 315, 385, 288, 312, 196, 218, 341, 353, 227, 272, 273, 274, 286, 240, 242, 243, 244, 245, 252, 251, 249, 259, 101]

        # Fill your dictionary in the required order
        for category_id in order:
            ordered_categories[str(category_id)] = categories.get(str(category_id), [])

        categories = ordered_categories



        # Create category buttons and assign to dictionary
        for category_id, brick_names in ordered_categories.items():


            
            if str(category_id) in ['290', '391', '291', '208', '226', '228', '235', '236', '281', '285', '296', '250', '246', '247', '253', '255', '559', '266', '268', '366', '267', '368', '367', '396', '275', '276', '375', '376', '287', '387', '388', '293', '392', '393', '310', '381', '320', '313', '340', '342', '347', '350', '351', '352', '359', '302', '386', '311', '321', '372', '107', '115', '128', '199']:
                continue
            x_pos, y_pos = self.calculate_slot_position(self.category_slot)
            category_button_pos = (x_pos, 0, y_pos)
            category_button_image_path = '/Users/jonathan/Documents/Resources/MainGroupDividers/{}.png'.format(category_id)
            if category_id not in self.category_buttons:
                self.category_buttons[category_id] = []
            
            self.category_buttons[category_id] = [DirectButton(
                parent=self.frame.getCanvas(),
                pos=category_button_pos,
                scale=0.08,  # Adjust as necessary
                command=self.expand_category,
                extraArgs=[category_id],
                image=category_button_image_path # Set the button image
            )]

            self.button_slots[category_id] = self.category_slot

            self.category_slot += 1
            #print(category_id, self.category_slot)



        
        # Create brick buttons and assign to dictionary
        for i in range(num_bricks):
            brick_geom_files = sorted(brick_geom_files)
            brick_geom = brick_geom_files[i]
  
            brick_name = os.path.basename(brick_geom).split('.')[0]
            category_id = self.get_category_id(brick_name)

            if category_id not in self.category_buttons:
                self.category_buttons[category_id] = []

            if str(category_id) == '250':  # if category_id is 250, change it to 244
                category_id = '244'
            elif str(category_id) in ['228', '235', '236', '281', '285', '296']:
                category_id = '227'
            elif str(category_id) in ['290', '391', '291', '299', '399', '0']: #change this 299 later
                category_id = '196'
            elif str(category_id) == '208':
                category_id = '206'
            elif str(category_id) == '226':
                category_id = '225'
            elif str(category_id) in ['246', '247']:
                category_id = '251'
            elif str(category_id) in ['253', '255']:
                category_id = '252'
            elif str(category_id) == '559':
                category_id = '259'
            elif str(category_id) in ['266', '268', '366', '267', '368', '367', '396']:
                category_id = '265'
            elif str(category_id) in ['275', '276', '375', '376']:
                category_id = '272'
            elif str(category_id) in ['287', '387', '388']:
                category_id = '288'
            elif str(category_id) in ['293', '392', '393']:
                category_id = '292'
            elif str(category_id) == '310':
                category_id = '301'
            elif str(category_id) == '381':
                category_id = '312'
            elif str(category_id) == '320':
                category_id = '315'
            elif str(category_id) in ['313', '340']:
                category_id = '341'
            elif str(category_id) in ['342', '347', '350', '351', '352', '359']:
                category_id = '353'
            elif str(category_id) in ['302', '386', '311', '321', '372']:
                category_id = '385'
            elif str(category_id) in ['107', '115', '128', '199']:
                category_id = '101'

            model_path = self.brick_types[f'brick{i+1}']
            bricknum = i + 1

            x_pos, y_pos = self.calculate_slot_position(self.category_slot)
            brick_button_pos = (x_pos, 0, y_pos)

            #brick_image = os.path.join(brick_images_folder_path, brick_name + ".png")
            brick_geometry = os.path.join(self.brick_geom_folder_path, brick_name + ".obj")

            card_maker = CardMaker('card')
            card_maker.set_frame(-0.5, 0.5, -0.5, 0.5)  # Set size and position
            card = NodePath(card_maker.generate())
            card.reparent_to(self.aspect2d)  # Add it to the 2D scene graph
            card.hide()

            # Set the texture
            self.render_obj_to_texture(brick_geometry, card)
            


 
            
            if i+1 < len(brick_images_file_paths) and brick_images_file_paths[i] is not None:
                    brick_image = brick_images_file_paths[i]

                
                    # Create button with image
                    self.brick_buttons[brick_name] = DirectButton(
                            parent=self.frame.getCanvas(),
                            image=card.get_texture(),  
                            pos=brick_button_pos,
                            scale=0.08,  # Adjust as necessary
                            command=self.set_brick_type,
                            extraArgs=["brick"+str(bricknum)],
                        )
                   # print(brick_name)
                    #print(i)
                        
            elif i+1 >= len(brick_images_file_paths):
                        # Create button with text (brick_name)
                        self.brick_buttons[brick_name] = DirectButton(
                            parent=self.frame.getCanvas(),
                            text=brick_name,
                            scale = 0.08,
                            pos=brick_button_pos,
                            command=self.set_brick_type,
                            extraArgs=["brick"+str(bricknum)],
                        )
                       # print("text brick")
                        #print(brick_name)
            else:
                    print(f"No geometry file found for {brick_name}")

                    
            self.brick_buttons[brick_name].hide()
            categories[category_id].append(brick_name)


            self.cat_buttons = self.category_buttons

            self.category_buttons[category_id] = self.brick_buttons[brick_name] # assign the created button to the dictionary
            self.button_slots[brick_name] = self.category_slot

            self.category_slot += 1
            #print(self.category_slot, f'Brick: {brick_name}')


        self.categories = categories
        self.category_visibility = {category_id: False for category_id in category_ids}


    def move_category_button(self, category_id, direction):
        total_buttons = self.category_slot
        new_slot_start = self.button_slots[category_id] + 1

        for brick_name in self.categories[category_id]:
            new_xpos = -0.2 + ((new_slot_start-1) % 3) * 0.2
            new_ypos = 2.85 - ((new_slot_start-1) // 3) * 0.25
            button = self.brick_buttons[brick_name]
            button.setPos(new_xpos, 0, new_ypos)
            new_slot_start += 1

        brick_cat_count = len(self.categories[category_id])
        brick_offput_slot = self.button_slots[category_id] + brick_cat_count + 1
        ###print(self.button_slots[category_id], new_slot_start, brick_cat_count, ",", brick_offput_slot)

        #for brick_name not in self.categories[category_id]:
            


    def expand_category(self, category_id):
        #self.category_slot = 0
        buttons = self.category_buttons[category_id]
        if self.category_visibility[category_id]: # If category is currently expanded
            # Hide brick buttons
            for brick_name in self.categories[category_id]:
                self.brick_buttons[brick_name].hide()
            # Move down category buttons
            for other_category_id in list(self.categories.keys())[self.category_slot:]:
                self.move_category_button(other_category_id, "down")
            
            # Update category visibility
            self.category_visibility[category_id] = False
        else: # If category is currently collapsed
            # Show brick buttons
            for i, brick_name in enumerate(self.categories[category_id]):
                self.move_category_button(category_id, "down")
                self.brick_buttons[brick_name].show()
            #print(self.cat_buttons[category_id])
            # Move up category buttons
            #for i, category_id in enumerate(self.cat_buttons[category_id]):
                
                #print (self.categories[category_id],"hey")
                #self.move_category_button(other_category_id, "up", len(self.categories[category_id]))

            # Update category visibility
            self.category_visibility[category_id] = True

    def set_cursor_image(self, image_path):
        wp = WindowProperties()
        wp.setCursorFilename(image_path)
        base.win.requestProperties(wp)




    def create_toolbar(self):
        aspect_ratio = base.getAspectRatio()

        self.toolbar = DirectFrame(
            frameSize=(-aspect_ratio, aspect_ratio, -0.1, 0.1),  # This will make a toolbar that spans the top of the window
            #frameColor=(0.2, 0.2, 0.2, 0.8),
            frameColor=(0.7529, 0.7529, 0.7529, 1),
            pos=(0, 0, 0.9)  # This positions the toolbar at the top of the window
        )
        self.toolbar.setBin('fixed', -10)

        # list of tool image paths
        paint_image = "/Users/jonathan/Documents/Resources/paint.png"
        
        tools = [
            {
                "image": "/Users/jonathan/Documents/Resources/Select.png",
                "text": "Select",
                "rollover_image": "/Users/jonathan/Documents/Resources/paint_bucket.png",
                "command": self.select_mode,
            },
            {
                "image": "/Users/jonathan/Documents/Resources/clone.png",
                "rollover_image": "/Users/jonathan/Documents/Resources/clone_hovered.png",
                "text": "Clone",
                "command": self.clone_mode,
            },
            {
                "image": "/Users/jonathan/Documents/Resources/hinge.png",
                "rollover_image": "/Users/jonathan/Documents/Resources/paint_bucket.png",
                "text": "Hinge",
                "command": self.hinge_mode
            },
            {
                "image": "/Users/jonathan/Documents/Resources/hinge_2.png",
                "rollover_image": "/Users/jonathan/Documents/Resources/paint_bucket.png",
                "text": "Hinge Align",
                "command": self.hingealign_mode
            },
            {
                "image": "/Users/jonathan/Documents/Resources/flex.png",
                "rollover_image": "/Users/jonathan/Documents/Resources/paint_bucket.png",
                "text": "Flex",
                "command": self.flex_mode
            },
            {
                "image": "/Users/jonathan/Documents/Resources/paint.png",
                "rollover_image": "/Users/jonathan/Documents/Resources/paint_bucket.png",
                "text": "Paint",
                "command": self.paint_mode
            },
            {
                "image": "/Users/jonathan/Documents/Resources/hide.png",
                "rollover_image": "/Users/jonathan/Documents/Resources/paint_bucket.png",
                "text": "Hide",
                "command": self.hide_mode
            },
            {
                "image": "/Users/jonathan/Documents/Resources/delete.png",
                "rollover_image": "/Users/jonathan/Documents/Resources/paint_bucket.png",
                "text": "Delete",
                "command": self.delete_mode
            }              

                
        ]

        for i, tool in enumerate(tools):

            button_pos = (-.55 + i * 0.25, 0, 0)  # calculate button position based on index

            tool_button = DirectButton(
                image=tool["image"],
                scale=0.09,
                pos=button_pos,
                parent=self.toolbar,
                relief=None,  # No border around the image
                rolloverSound=None,  # No sound on hover
                clickSound=None,  # No sound on click
                command=tool["command"],


            )       
            # Add hover text to the button
            tool_button.bind(DGG.ENTER, self.on_button_hover, extraArgs=[tool_button, tool["text"], tool["rollover_image"]])
            tool_button.bind(DGG.EXIT, self.on_button_exit, extraArgs=[tool_button, tool["image"]])
    def set_rollover_image(self, button, image, event):
        button['image'] = image

    def set_normal_image(self, button, image, event):
        button['image'] = image

    def on_button_hover(self, tool_button, tool_text, rollover_image, event):
        self.show_hover_text(tool_text, event)
        self.set_rollover_image(tool_button, rollover_image, event)  # pass event

    def on_button_exit(self, tool_button, tool_image, event):
        self.hide_hover_text(event)
        self.set_normal_image(tool_button, tool_image, event)  # pass event




    def create_toolbar_options(self):
        aspect_ratio = self.getAspectRatio()
        self.toolbar_options = DirectFrame(
            frameSize=(-aspect_ratio, aspect_ratio, -0.1, 0.1),  # This will make a toolbar that spans the width of the window
            frameColor=(1, 1, 1, 1),
            pos=(0, 0, 0.8)  # This positions the toolbar below the first toolbar
        )
        self.toolbar_options.setBin('fixed', -10)

    def add_toolbar_options(self):
        print("adding toolbar")
        for child in self.toolbar_options.getChildren():
            child.removeNode()

        if self.mode == 'PAINT':
            paint_options = [
                {
                    "image": "/Users/jonathan/Documents/Resources/paint_bucket.png",
                    "text": "Paint Bucket",
                    "command": self.select_mode,
                },
                {
                    "image": "/Users/jonathan/Documents/Resources/color_picker.png",
                    "text": "Color Picker",
                    "command": self.toggle_color_selection_window,
                },

                {
                    "image": "/Users/jonathan/Documents/Resources/eyedropper.png",
                    "text": "Eyedropper",
                    "command": self.clone_mode,
                },
                {
                    "image": "/Users/jonathan/Documents/Resources/decorations.png",
                    "text": "Decorations",
                    "command": self.hinge_mode,
                }
            ]


            for i, tool in enumerate(paint_options):

                button_pos = (0 + i * .12, 0, -.05)  # calculate button position based on index

                tool_button = DirectButton(
                    image=tool["image"],
                    scale=0.05,
                    pos=button_pos,
                    parent=self.toolbar_options,
                    relief=None,  # No border around the image
                    rolloverSound=None,  # No sound on hover
                    clickSound=None,  # No sound on click
                    command=tool["command"],

                )
        elif self.mode == 'FLEX':
            for child in self.toolbar_options.getChildren():
                child.removeNode()
            print("flexing!")

        elif self.mode == 'DELETE':
            for child in self.toolbar_options.getChildren():
                child.removeNode()

        else:
            print("No mode selected!")
        

        
    def show_hover_text(self, text, event):
        if self.hover_text is not None:
            self.hover_text.destroy()

        mouseX, mouseY = self.win.getPointer(0).getX(), self.win.getPointer(0).getY()
        aspect_ratio = self.getAspectRatio()

        # Calculate the position of the text based on the mouse position and aspect ratio
        xpos = (mouseX / float(self.win.getXSize()) - 0.5) * 2 * aspect_ratio
        ypos = (0.5 - mouseY / float(self.win.getYSize())) * 2

        self.hover_text_frame = DirectFrame(
            frameSize=(-0.15, 0.15, -0.05, 0.05),
            frameColor=(0.2, 0.2, 0.2, 0.8),
            pos=(xpos + 0.2, 0, ypos - 0.05)
        )
        self.hover_text = OnscreenText(text=text, pos=(xpos + 0.2, ypos - 0.075), scale=0.07)


 #   def select_tool(self, tool_button):
        # If there is a currently selected tool, set its state back to normal
  #      if self.current_tool:
   #         self.current_tool['state'] = DGG.NORMAL

        # Set the selected tool button's state to disabled
    #    tool_button['state'] = DGG.DISABLED

        # Update the currently selected tool
     #   self.current_tool = tool_button
        
    def hide_hover_text(self, event):
        if self.hover_text is not None:
            self.hover_text.destroy()
            self.hover_text_frame.destroy()
            self.hover_text = None
###############################################################################################################
#                                               TOOLBAR METHODS                                               #
###############################################################################################################
                                     

    def paint_mode(self):
        self.mode = 'PAINT'
        self.add_toolbar_options()
        self.set_cursor_image('/Users/jonathan/Documents/Resources/202.png')

    def clone_mode(self):
        return
    
    def hinge_mode(self):
            return

    def delete_mode(self):
        self.mode = 'DELETE'
        self.add_toolbar_options()
        
    def hingealign_mode(self):
            return

    def flex_mode(self):
        self.mode = 'FLEX'
        self.add_toolbar_options()

    def hide_mode(self):
            return
        
    def select_mode(self):
        self.mode = 'SELECT'

    

    def place_mode(self):
        self.mode = 'PLACE'

    def select_model(self):
        # Check if mouse is in screen
        #if self.mouseWatcherNode.hasMouse():
            # Get the mouse position
            mouse_pos = self.mouseWatcherNode.getMouse()
            # Set the position of the ray based on the mouse position
            self.picker_node_path.node().getSolid(0).setFromLens(self.camNode, mouse_pos.getX(), mouse_pos.getY())
            # Traverse the scene graph
            self.picker.traverse(render)
            # If we have a collision, handle it
            if self.pq.getNumEntries() > 0:
                # Sort the entries (closest first)
                self.pq.sortEntries()
                # Get the closest entry
                self.picked_obj = self.pq.getEntry(0).getIntoNodePath()
                # Change the color of the picked model
                self.picked_obj.setColor(0, 0, 1, 1)  # RGB alpha: blue color
                self.selected = True
    
    
app = MyApp()
app.run()

