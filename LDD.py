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






class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        # self.disableMouse()

        # Set camera position and orientation
        self.camera.setPos(50, -50, 500)
        self.camera.lookAt(Point3(0, 0, 0))
        self.camera.setHpr(25, -15, 0)

        # Reset trackball position
       # self.trackball.node().setPos(500, 500, -100)
        self.disableMouse() 

        self.brick_types = {
            "brick1": "/Users/jonathan/Documents/2439.obj",
            "brick2": "/Users/jonathan/Documents/99010.obj",
        }

        # Create a plane at z=0
        self.plane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
        planeNode = PlaneNode('plane')
        planeNode.setPlane(self.plane)
        self.render.attachNewNode(planeNode)

        cm = CardMaker("ground")
        cm.setFrame(-1000, 1000, -1000, 1000)  # adjust as necessary
        ground = self.render.attachNewNode(cm.generate())
        ground.setPos(0, 0, 0)  # adjust as necessary
        ground.setP(-90)
        ground.setTwoSided(True)

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
        ground.setTexScale(tsAlpha, 25, 25)

        # Set texture scale
        ground.setTexScale(ts, 25, 25)

        self.selected = False
        self.hovered_brick = None

        self.setBackgroundColor(0.9, 0.9, 0.9, 1)
        self.create_gui()
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
        self.accept('arrow_up', self.move_camera, [0, 30, 0])
        self.accept('arrow_down', self.move_camera, [0, -30, 0])

        




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

        self.mode = 'PLACE'  # Set default mode to 'PLACE'

        self.selectMove = False

        self.accept('mouse1', self.on_left_click)  # Left click
        self.hover_text = None
        self.hover_text_frame = None


    def move_camera(self, dx, dy, dz):
        # Move the camera by the specified amount
        self.camera.setPos(self.camera.getPos() + Vec3(dx, dy, dz))

    def zoom_in(self):
        """This function is called when the mouse wheel is scrolled up."""
        lens = base.cam.node().getLens()
        new_fov = max(30, lens.getFov() - 2)  # Lower limit is 30
        lens.setFov(new_fov)

    def zoom_out(self):
        """This function is called when the mouse wheel is scrolled down."""
        lens = base.cam.node().getLens()
        new_fov = min(120, lens.getFov() + 2)  # Upper limit is 120
        lens.setFov(new_fov)

    def clone_selected(self):
        if self.selected and self.hovered_brick is not None:  # Check if a brick is selected
            # Create a new copy of the hovered_brick
            print(self.hovered_brick.getPos())
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
                if not self.locked and self.selected and self.hovered_brick is not None and not self.selectMove: #if a brick is NOT locked but IS selected
                    print("near world:",near_world)
                    print("far world:",far_world)
                    print("pos3d",pos3d)
                    # the new position will be pos3d + Vec3(0, 0, 1)
                    new_pos = pos3d + Vec3(0, 0, 1)
                    new_pos.x = round(new_pos.x / 5) * 5
                    new_pos.y = round(new_pos.y / 5) * 5
                    new_pos.z = round(new_pos.z / 5) * 5
                    clamped_pos = self.clamp_position(new_pos)

                    # calculate how much to move the brick in each direction
                    delta_x = clamped_pos.x - self.hovered_brick.getX()
                    delta_y = clamped_pos.y - self.hovered_brick.getY()
                    delta_z = clamped_pos.z - self.hovered_brick.getZ()

                    # move the brick
                    self.hovered_brick.setX(self.hovered_brick.getX() + delta_x)
                    self.hovered_brick.setY(self.hovered_brick.getY() + delta_y)
                    self.hovered_brick.setZ(self.hovered_brick.getZ() + delta_z)
                    
                elif self.selected and self.hovered_brick is not None: #if a brick is selected AND you are currently hovering over it
                    self.locked = False
                    self.selected = True
                    #new_pos = pos3d + Vec3(0, 0, 1)
                    #new_pos.x = round(new_pos.x / 5) * 5
                    #new_pos.y = round(new_pos.y / 5) * 5
                    #new_pos.z = round(new_pos.z / 5) * 5
                    #clamped_pos = self.clamp_position(new_pos)
                    #self.hovered_brick.setPos(clamped_pos)
                elif self.model is None:
                    self.load_model(pos3d)

                else:
                    new_pos = pos3d + Vec3(0, 0, 1)
                    new_pos.x = round(new_pos.x / 5) * 5
                    new_pos.y = round(new_pos.y / 5) * 5
                    new_pos.z = round(new_pos.z / 5) * 5
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
                self.pq.sortEntries()
                picked_obj = self.pq.getEntry(0).getIntoNodePath()
                if picked_obj != self.hovered_brick:
                    if self.hovered_brick is not None:
                        self.hovered_brick.setColorScale(1, 1, 1, 1)
                    picked_obj.setColorScale(0.5, 0, 0.5, 1) #purple
                    self.hovered_brick = picked_obj
                    print(self.hovered_brick)
                    print(picked_obj)
                    print("Hovered over: ", picked_obj.getName())
                    self.hoveringOver = True
                    print(self.hoveringOver)
            else:
                if self.hovered_brick is not None and not self.selected:
                    self.hovered_brick.setColorScale(1, 1, 1, 1) #white
                    self.hovered_brick = None

            return task.cont

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
                    print("moving!")
                    self.selected = True
                    # Change the color of the children nodes
                    self.hovered_brick.setColorScale(0, 0, 1, 1)
                    print("selected:", self.selected)
                else:
                    print("deselected")
                    self.selected = False
                    # Revert the color of the children nodes
                    for child in self.hovered_brick.getChildren():
                        child.setColorScale(1, 1, 1, 1)  # Revert to original color






    def clamp_position(self, pos):
        x = max(-500, min(pos.x, 500))
        y = max(-500, min(pos.y, 500))
        z = max(-500, min(pos.z, 500))
        return Point3(x, y, z)


    def load_model(self, pos):
        model_path = self.brick_types.get(self.current_brick_type)
        if model_path is None:
            #print("No brick type selected!")
            return

        if self.model:
            self.model.removeNode()

        self.model = self.loader.loadModel(model_path)
        self.model.reparentTo(self.render)
        self.model.setScale(40, 40, 40)  # adjust this as necessary
        #self.model.setPos(pos + Vec3(0, 0, 1))  # slightly above the plane to prevent Z-fighting
        self.model.setP(90)


    def create_gui(self):
        panel = DirectFrame(
            frameSize=(-0.8, 0.2, -2, 1),
            frameColor=(0.2, 0.2, 0.2, 0.8),
            pos=(-1, 0, 0.7)
        )

        brick1_image = "/Users/jonathan/Documents/Resources/2439.png"  # Replace with the actual path to your image
        brick2_image = "/Users/jonathan/Documents/Resources/99010.png"

        brick1_button = DirectButton(
            image=brick1_image,  # Use the image parameter instead of text
            scale=0.2,
            command=self.set_brick_type,
            extraArgs=["brick1"],
            pos=(-0.1, 0, 0),
            parent=panel
        )

        brick2_button = DirectButton(
            image=brick2_image,
            scale=0.2,
            command=self.set_brick_type,
            extraArgs=["brick2"],
            pos=(-0.1, 0, -0.8),
            parent=panel
        )

        self.taskMgr.add(self.update_model_position, "update_model_position")

    def create_toolbar(self):
        toolbar = DirectFrame(
            frameSize=(-1, 1, -0.1, 0.1),  # This will make a toolbar that spans the top of the window
            frameColor=(0.2, 0.2, 0.2, 0.8),
            pos=(0, 0, 0.9)  # This positions the toolbar at the top of the window
        )

        # list of tool image paths
        tool_images = [
            "/Users/jonathan/Documents/Resources/Select.png",
            "/Users/jonathan/Documents/Resources/clone.png",
            "/Users/jonathan/Documents/Resources/hinge.png",
            "/Users/jonathan/Documents/Resources/hinge_2.png",
            "/Users/jonathan/Documents/Resources/flex.png",
            "/Users/jonathan/Documents/Resources/paint.png",
            "/Users/jonathan/Documents/Resources/hide.png",
            "/Users/jonathan/Documents/Resources/delete.png"
        ]

        # corresponding list of tool hover text
        tool_texts = [
            "Select",
            "Clone",
            "Hinge",
            "Hinge_2",
            "Flex",
            "Paint",
            "Hide",
            "Delete"
        ]

        num_tools = len(tool_images)  # number of tools (assumes tool_images and tool_texts have the same length)
        for i in range(num_tools):
            tool_image = tool_images[i]
            tool_text = tool_texts[i]

            button_pos = (-0.875 + i * 0.25, 0, 0)  # calculate button position based on index

            tool_button = DirectButton(
                image=tool_image,
                scale=0.09,
                pos=button_pos,
                parent=toolbar,
                relief=None,  # No border around the image
                rolloverSound=None,  # No sound on hover
                clickSound=None,  # No sound on click
            )

            # Add hover text to the button
            tool_button.bind(DGG.ENTER, self.show_hover_text, extraArgs=[tool_text])
            tool_button.bind(DGG.EXIT, self.hide_hover_text)
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

    def hide_hover_text(self, event):
        if self.hover_text is not None:
            self.hover_text.destroy()
            self.hover_text_frame.destroy()
            self.hover_text = None


    def select_mode(self):
        self.mode = 'SELECT'

    def place_mode(self):
        self.mode = 'PLACE'

    def select_model(self):
        # Check if mouse is in screen
        if self.mouseWatcherNode.hasMouse():
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
                picked_obj = self.pq.getEntry(0).getIntoNodePath()
                # Change the color of the picked model
                picked_obj.setColor(0, 0, 1, 1)  # RGB alpha: blue color
    
    
app = MyApp()
app.run()

