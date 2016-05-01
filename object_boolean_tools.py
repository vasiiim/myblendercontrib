# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK ##### actObj.grease_pencil.clear()" by "bpy.context.scene.grease_pencil.clear()
# Contributed to by TynkaTopi, meta-androcto

bl_info = {
    "name": "Bool Tool",
    "author": "Vitor Balbio, Mikhail Rachinskiy",
    "version": (0, 3, 1),
    "blender": (2, 77),
    "location": "View3D > Toolshelf > BoolTool",
    "description": "Bool Tools Hotkey: Ctrl Shift B",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Object/BoolTool",
    "tracker_url": "https://developer.blender.org/maniphest/task/create/?project=3&type=Bug",
    "category": "Object"}

import bpy
import bmesh
import time
from bpy.app.handlers import persistent
from bpy.types import (
    Operator,
    Panel,
)


# -------------------  Bool Tool FUNCTIONS------------------------------
# Utils:

# Hide boolean objects
def update_BoolHide(self, context):
    ao = context.scene.objects.active
    objs = [i.object for i in ao.modifiers if i.type == 'BOOLEAN']
    hide_state = context.scene.BoolHide

    for o in objs:
        o.hide = hide_state

# Object is a Canvas
def isCanvas(_obj):
    try:
        if _obj["BoolToolRoot"]:
            return True
    except:
        return False


# Object is a Brush Tool Bool
def isBrush(_obj):
    try:
        if _obj["BoolToolBrush"]:
            return True
    except:
        return False


# Object is a Poly Brush Tool Bool collection
def isPolyBrush(_obj):
    try:
        if _obj["BoolToolPolyBrush"]:
            return True
    except:
        return False


def BT_ObjectByName(obj):
    for ob in bpy.context.scene.objects:
        if isCanvas(ob) or isBrush(ob):
            if ob.name == obj:
                return ob


def FindCanvas(obj):
    for ob in bpy.context.scene.objects:
        if isCanvas(ob):
            for mod in ob.modifiers:
                if ("BTool_" in mod.name):
                    if (obj.name in mod.name):
                        return ob


def isFTransf():
    addons = bpy.context.user_preferences.addons
    user_preferences = bpy.context.user_preferences
    addon_prefs = addons[__name__].preferences
    if addon_prefs.fast_transform:
        return True
    else:
        return False


"""
# EXPERIMENTAL FEATURES
def isMakeVertexGroup():
    user_preferences = bpy.context.user_preferences
    addon_prefs = user_preferences.addons[bl_info["name"]].preferences
    if addon_prefs.make_vertex_groups:
        return True
    else:
        return False

def isMakeBoundary():
    user_preferences = bpy.context.user_preferences
    addon_prefs = user_preferences.addons[bl_info["name"]].preferences
    if addon_prefs.make_boundary:
        return True
    else:
        return False
"""


def ConvertToMesh(obj):
    act = bpy.context.scene.objects.active
    bpy.context.scene.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    bpy.context.scene.objects.active = act


# Do the Union, Difference and Intersection Operations with a Brush
def Operation(context, _operation):

    useWire = bpy.context.user_preferences.addons['object_boolean_tools'].preferences.use_wire

    for selObj in bpy.context.selected_objects:
        if selObj != context.active_object and (selObj.type == "MESH" or selObj.type == "CURVE"):
            if selObj.type == "CURVE":
                ConvertToMesh(selObj)
            actObj = context.active_object
            selObj.hide_render = True
            cyclesVis = selObj.cycles_visibility
            # for obj in bpy.context.scene.objects:
            #   if isCanvas(obj):
            #      for mod in obj.modifiers:
            #         if(mod.name == "BTool_" + selObj.name):
            #            obj.modifiers.remove(mod)

            if useWire:
                selObj.draw_type = "WIRE"
            else:
                selObj.draw_type = "BOUNDS"

            cyclesVis.camera = False;
            cyclesVis.diffuse = False;
            cyclesVis.glossy = False;
            cyclesVis.shadow = False;
            cyclesVis.transmission = False;
            if _operation=="SLICE":
                clone=context.active_object.copy() #copies dupli_group property(empty), but group property is empty (users_group = None)
                # clone.select=True
                context.scene.objects.link(clone)
                sliceMod = clone.modifiers.new("BTool_" + selObj.name, "BOOLEAN") #add mod to clone obj
                sliceMod.object = selObj
                sliceMod.operation = "DIFFERENCE"
                clone["BoolToolRoot"] = True
            newMod = actObj.modifiers.new("BTool_" + selObj.name, "BOOLEAN")
            newMod.object = selObj
            if _operation=="SLICE":
                newMod.operation = "INTERSECT"
            else:
                newMod.operation = _operation

            actObj["BoolToolRoot"] = True
            selObj["BoolToolBrush"] = _operation
            selObj["BoolTool_FTransform"] = "False"


# Do Direct Union, Difference and Intersection Operations
def Operation_Direct(context, _operation):
    actObj = context.active_object

    useWire = bpy.context.user_preferences.addons['object_boolean_tools'].preferences.use_wire
    for selObj in bpy.context.selected_objects:
        if selObj != context.active_object and (selObj.type == "MESH" or selObj.type == "CURVE"):
            if selObj.type == "CURVE":
                ConvertToMesh(selObj)
            actObj = context.active_object
            if useWire:
                selObj.draw_type = "WIRE"
            else:
                selObj.draw_type = "BOUNDS"
            if _operation=="SLICE":
                clone=context.active_object.copy() #copies dupli_group property(empty), but group property is empty (users_group = None)
                # clone.select=True
                clone.data=context.active_object.data.copy()
                context.scene.objects.link(clone)
                sliceMod = clone.modifiers.new("BTool_" + selObj.name, "BOOLEAN") #add mod to clone obj
                sliceMod.object = selObj
                sliceMod.operation = "DIFFERENCE"

                bpy.ops.object.modifier_apply(modifier=sliceMod.name)

            newMod = actObj.modifiers.new("BTool_" + selObj.name, "BOOLEAN")
            if _operation=="SLICE":
                newMod.operation = "INTERSECT"
            else:
                newMod.operation = _operation
            newMod.object = selObj
            bpy.ops.object.modifier_apply(modifier=newMod.name)
            bpy.ops.object.select_all(action='DESELECT')
            # selObj.select = True
            # bpy.ops.object.delete()


# Remove Obejcts form the BoolTool System
def Remove(context, thisObj_name, Prop):
    # Find the Brush pointed in the Tree View and Restore it, active is the Canvas
    actObj = context.active_object

    # Restore the Brush
    def RemoveThis(_thisObj_name):
        for obj in bpy.context.scene.objects:
            # if it's the brush object
            if obj.name == _thisObj_name:
                cyclesVis = obj.cycles_visibility
                obj.draw_type = "TEXTURED"
                del obj["BoolToolBrush"]
                del obj["BoolTool_FTransform"]
                cyclesVis.camera = True;
                cyclesVis.diffuse = True;
                cyclesVis.glossy = True;
                cyclesVis.shadow = True;
                cyclesVis.transmission = True;

                # Remove it from the Canvas
                for mod in actObj.modifiers:
                    if ("BTool_" in mod.name):
                        if (_thisObj_name in mod.name):
                            actObj.modifiers.remove(mod)

    if Prop == "THIS":
        RemoveThis(thisObj_name)

    # If the remove was called from the Properties:
    else:
        # Remove the Brush Property
        if Prop == "BRUSH":
            Canvas = FindCanvas(actObj)
            for mod in Canvas.modifiers:
                if ("BTool_" in mod.name):
                    if (actObj.name in mod.name):
                        Canvas.modifiers.remove(mod)
                        cyclesVis = actObj.cycles_visibility
                        actObj.draw_type = "TEXTURED"
                        del actObj["BoolToolBrush"]
                        del actObj["BoolTool_FTransform"]
                        cyclesVis.camera = True;
                        cyclesVis.diffuse = True;
                        cyclesVis.glossy = True;
                        cyclesVis.shadow = True;
                        cyclesVis.transmission = True;

        if Prop == "CANVAS":
            for mod in actObj.modifiers:
                if ("BTool_" in mod.name):
                    RemoveThis(mod.object.name)


# Tooble the Enable the Brush Object Propertie
def EnableBrush(context, objList, canvas):
    for obj in objList:
        for mod in canvas.modifiers:
            if ("BTool_" in mod.name and mod.object.name == obj):

                if (mod.show_viewport):
                    mod.show_viewport = False
                    mod.show_render = False
                else:
                    mod.show_viewport = True
                    mod.show_render = True


# Find the Canvas and Enable this Brush
def EnableThisBrush(context, set):
    canvas = None
    for obj in bpy.context.scene.objects:
        if obj != bpy.context.active_object:
            if isCanvas(obj):
                for mod in obj.modifiers:
                    if ("BTool_" in mod.name):
                        if mod.object == bpy.context.active_object:
                            canvas = obj

    for mod in canvas.modifiers:
        if ("BTool_" in mod.name):
            if mod.object == bpy.context.active_object:
                if set == "None":
                    if (mod.show_viewport):
                        mod.show_viewport = False
                        mod.show_render = False
                    else:
                        mod.show_viewport = True
                        mod.show_render = True
                else:
                    if (set == "True"):
                        mod.show_viewport = True
                    else:
                        mod.show_viewport = False
                return


# Tooble the Fast Transform Propertie of the Active Brush
def EnableFTransf(context):
    actObj = bpy.context.active_object

    if actObj["BoolTool_FTransform"] == "True":
        actObj["BoolTool_FTransform"] = "False"
    else:
        actObj["BoolTool_FTransform"] = "True"
    return


# Apply All Brushes to the Canvas
def ApplyAll(context, list):
    objDeleteList = []
    for selObj in list:
        if isCanvas(selObj) and selObj == context.active_object:
            for mod in selObj.modifiers:
                if ("BTool_" in mod.name):
                    objDeleteList.append(mod.object)
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except: #if fails the means it is multiuser data
                    context.active_object.data=context.active_object.data.copy() #so just make data unique
                    bpy.ops.object.modifier_apply(modifier=mod.name)

            # bpy.ops.object.select_all(action='TOGGLE')
            # bpy.ops.object.select_all(action='DESELECT')
            # for obj in deleteList:
            #     obj.select = True
            # bpy.ops.object.delete()
    for obj in context.scene.objects:
        if isCanvas(obj):
            for mod in obj.modifiers:
                if mod.type == 'BOOLEAN':
                    if mod.object in objDeleteList: # do not delete brush that is used by another canvas
                        objDeleteList.remove(mod.object)  # remove it from deletion
    bpy.ops.object.select_all(action='DESELECT')
    # for obj in objDeleteList:
    #     obj.select = True
    #     bpy.ops.object.delete()


# Apply This Brush to the Canvas
def ApplyThisBrush(context, brush):
    for obj in context.scene.objects:
        if isCanvas(obj):
            for mod in obj.modifiers:
                if ("BTool_" + brush.name in mod.name):
                    """
                    # EXPERIMENTAL
                    if isMakeVertexGroup():
                        # Turn all faces of the Brush selected
                        bpy.context.scene.objects.active = brush
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='SELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')

                        #Turn off al faces of the Canvas selected
                        bpy.context.scene.objects.active = canvas
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')
                    """

                    # Apply This Brush
                    context.scene.objects.active = obj
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    except: #if fails the means it is multiuser data
                        context.active_object.data=context.active_object.data.copy() #so just make data unique
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    bpy.ops.object.select_all(action='TOGGLE')
                    bpy.ops.object.select_all(action='DESELECT')

                    """
                    # EXPERIMENTAL
                    if isMakeVertexGroup():
                        # Make Vertex Group
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.object.vertex_group_assign_new()
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.object.mode_set(mode='OBJECT')

                        canvas.vertex_groups.active.name = "BTool_" + brush.name
                    """

                # Garbage Colletor
    brush.select = True
    # bpy.ops.object.delete()


def GCollector(_obj):
    if isCanvas(_obj):
        BTRoot = False
        for mod in _obj.modifiers:
            if ("BTool_" in mod.name):
                BTRoot = True
                if (mod.object == None):
                    _obj.modifiers.remove(mod)
        if not BTRoot:
            del _obj["BoolToolRoot"]


# Handle the callbacks when modifing things in the scene
@persistent
def HandleScene(scene):
    if bpy.data.objects.is_updated:
        for ob in bpy.data.objects:
            if ob.is_updated:
                GCollector(ob)


# ------------------ Bool Tool OPERATORS-----------------------------------------------------
class BTool_DrawPolyBrush(Operator):
    """Draw Polygonal Mask, can be applyied to Canvas > Brush or Directly. ESC to Exit"""
    bl_idname = "btool.draw_polybrush"
    bl_label = "Draw Poly Brush"

    count = 0

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def modal(self, context, event):
        self.count += 1
        actObj = bpy.context.active_object
        if self.count == 1:
            actObj.select = True
            bpy.ops.gpencil.draw('INVOKE_DEFAULT', mode="DRAW_POLY")

        if event.type in {'RET', 'NUMPAD_ENTER'}:

            bpy.ops.gpencil.convert(type='POLY')
            for obj in context.selected_objects:
                if obj.type == "CURVE":
                    obj.name = "PolyDraw"
                    bpy.context.scene.objects.active = obj
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select = True
                    bpy.ops.object.convert(target="MESH")
                    bpy.ops.object.mode_set(mode='EDIT')
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.edge_face_add()
                    bpy.ops.mesh.flip_normals()
                    bpy.ops.object.mode_set(mode='OBJECT')
                    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
                    bpy.ops.object.modifier_add(type="SOLIDIFY")
                    for mod in obj.modifiers:
                        if mod.name == "Solidify":
                            mod.name = "BTool_PolyBrush"
                            mod.thickness = 1
                            mod.offset = 0
                    obj["BoolToolPolyBrush"] = True

                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.context.scene.objects.active = actObj
                    bpy.context.scene.update()
                    actObj.select = True
                    obj.select = True
                    # try:
                    bpy.context.scene.grease_pencil.clear()
                    bpy.ops.gpencil.data_unlink()

            return {'FINISHED'}

        if event.type in {'ESC'}:
            bpy.ops.ed.undo()  # remove o Grease Pencil
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.object:
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "No active object, could not finish")
            return {'CANCELLED'}


# Fast Transform
class BTool_FastTransform(Operator):
    """Enable Fast Transform"""
    bl_idname = "btool.fast_transform"
    bl_label = "Fast Transform"

    operator = bpy.props.StringProperty("")

    count = 0
    def modal(self, context, event):
        self.count += 1
        actObj = bpy.context.active_object
        useWire = bpy.context.user_preferences.addons[__name__].preferences.use_wire
        if self.count == 1:

            if isBrush(actObj) and actObj["BoolTool_FTransform"] == "True":
                EnableThisBrush(bpy.context, "False")
                if useWire:
                    actObj.draw_type = "WIRE"
                else:
                    actObj.draw_type = "BOUNDS"

            if self.operator == "Translate":
                bpy.ops.transform.translate('INVOKE_DEFAULT')
            if self.operator == "Rotate":
                bpy.ops.transform.rotate('INVOKE_DEFAULT')
            if self.operator == "Scale":
                bpy.ops.transform.resize('INVOKE_DEFAULT')

        if event.type == 'LEFTMOUSE':
            if isBrush(actObj):
                EnableThisBrush(bpy.context, "True")
                actObj.draw_type = "WIRE"
            return {'FINISHED'}

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            if isBrush(actObj):
                EnableThisBrush(bpy.context, "True")
                actObj.draw_type = "WIRE"
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.object:
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "No active object, could not finish")
            return {'CANCELLED'}


# -------------------  Bool Tool OPERATOR CLASSES --------------------------------------------------------

# Brush Operators --------------------------------------------

# Boolean Union Operator
class BTool_Union(Operator):
    """This operator add a union brush to a canvas"""
    bl_idname = "btool.boolean_union"
    bl_label = "Brush Union"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        Operation(context, "UNION")
        return {'FINISHED'}


# Boolean Intersection Operator
class BTool_Inters(Operator):
    """This operator add a intersect brush to a canvas"""
    bl_idname = "btool.boolean_inters"
    bl_label = "Brush Intersection"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        Operation(context, "INTERSECT")
        return {'FINISHED'}


# Boolean Difference Operator
class BTool_Diff(Operator):
    """This operator add a difference brush to a canvas"""
    bl_idname = "btool.boolean_diff"
    bl_label = "Brush Difference"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        Operation(context, "DIFFERENCE")
        return {'FINISHED'}

# Boolean Slices Operator
class BTool_Slice(Operator):
    """This operator add a intersect brush to a canvas"""
    bl_idname = "btool.boolean_slice"
    bl_label = "Brush Slice"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        Operation(context, "SLICE")
        return {'FINISHED'}

# Booltron Direct FUNCTIONS ---------------------------------------------------

def mesh_selection(ob, select_action):
    context = bpy.context
    scene = context.scene
    obj = context.active_object
    ops_me = bpy.ops.mesh
    ops_ob = bpy.ops.object

    scene.objects.active = ob
    ops_ob.mode_set(mode="EDIT")
    ops_me.select_all(action=select_action)
    ops_ob.mode_set(mode="OBJECT")
    scene.objects.active = obj


def modifier_boolean(obj, ob, mode, delete_not=False):
    md = obj.modifiers.new("BoolTool Direct", 'BOOLEAN')
    md.show_viewport = False
    md.show_render = False
    md.operation = mode
    md.object = ob

    bpy.ops.object.modifier_apply(modifier="BoolTool Direct")
    if delete_not is True:
        return
    bpy.context.scene.objects.unlink(ob)
    bpy.data.objects.remove(ob)


def boolean_each(mode):
    context = bpy.context
    obj = context.active_object

    obj.select = False
    obs = context.selected_objects

    mesh_selection(obj, 'DESELECT')
    for ob in obs:
        mesh_selection(ob, 'SELECT')
        modifier_boolean(obj, ob, mode)
    obj.select = True


def objects_get():
    context = bpy.context
    obj = context.active_object

    obj.select = False
    ob = context.selected_objects[0]

    mesh_selection(obj, 'DESELECT')
    mesh_selection(ob, 'SELECT')

    return obj, ob

# Booltron Direct Operators ---------------------------------------------------

class Direct_Union(Operator):
    """Combine selected objects"""
    bl_idname = "btool.direct_union"
    bl_label = "Union"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        boolean_each('UNION')
        return {'FINISHED'}

class Direct_Difference(Operator):
    """Subtract selected objects from active object"""
    bl_idname = "btool.direct_difference"
    bl_label = "Difference"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        boolean_each('DIFFERENCE')
        return {'FINISHED'}

class Direct_Intersect(Operator):
    """Keep only intersecting geometry"""
    bl_idname = "btool.direct_intersect"
    bl_label = "Intersect"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        boolean_each('INTERSECT')
        return {'FINISHED'}

class Direct_Slice(Operator):
    """Slice active object along the selected object (can handle only two objects at a time)"""
    bl_idname = "btool.direct_slice"
    bl_label = "Slice"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) == 2

    def execute(self, context):
        scene = context.scene
        obj, ob = objects_get()

        def object_duplicate(ob):
            ops_ob = bpy.ops.object
            ops_ob.select_all(action="DESELECT")
            ops_ob.select_pattern(pattern=ob.name)
            ops_ob.duplicate()
            scene.objects.active = obj
            return context.selected_objects[0]

        obj_copy = object_duplicate(obj)
        modifier_boolean(obj, ob, 'DIFFERENCE', delete_not=True)
        scene.objects.active = obj_copy
        modifier_boolean(obj_copy, ob, 'INTERSECT')
        return {'FINISHED'}

class Direct_Subtract(Operator):
    """Subtract selected object from active object, subtracted object not removed (can handle only two objects at a time))"""
    bl_idname = "btool.direct_subtract"
    bl_label = "Subtract"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) == 2

    def execute(self, context):
        obj, ob = objects_get()
        modifier_boolean(obj, ob, 'DIFFERENCE', delete_not=True)
        return {'FINISHED'}

# Utils Class ---------------------------------------------------------------

# Find the Brush Selected in Three View
class BTool_FindBrush(Operator):
    """Find the this brush"""
    bl_idname = "btool.find_brush"
    bl_label = ""
    obj = bpy.props.StringProperty("")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        for ob in bpy.context.scene.objects:
            if (ob.name == self.obj):
                bpy.ops.object.select_all(action='TOGGLE')
                bpy.ops.object.select_all(action='DESELECT')
                bpy.context.scene.objects.active = ob
                ob.select = True
        return {'FINISHED'}


# Mode The Modifier in The Stack Up or Down
class BTool_MoveStack(Operator):
    """Move this Brush Up/Down in the Stack"""
    bl_idname = "btool.move_stack"
    bl_label = ""
    modif = bpy.props.StringProperty("")
    direction = bpy.props.StringProperty("")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        if (self.direction == "UP"):
            bpy.ops.object.modifier_move_up(modifier=self.modif)
        if (self.direction == "DOWN"):
            bpy.ops.object.modifier_move_down(modifier=self.modif)
        return {'FINISHED'}


# Enable or Disable a Brush in th Three View
class BTool_EnableBrush(Operator):
    """Removes all BoolTool config assigned to it"""
    bl_idname = "btool.enable_brush"
    bl_label = ""

    thisObj = bpy.props.StringProperty("")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # in this case is just one object but the function accept more than one at once
        EnableBrush(context, [self.thisObj], context.active_object)
        return {'FINISHED'}


# Enable or Disabel a Brush Directly
class BTool_EnableThisBrush(Operator):
    """ Toggles this brush"""
    bl_idname = "btool.enable_this_brush"
    bl_label = ""

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        EnableThisBrush(context, "None")
        return {'FINISHED'}


# Enable or Disabel a Brush Directly
class BTool_EnableFTransform(Operator):
    """Use Fast Transformations to improve speed"""
    bl_idname = "btool.enable_ftransf"
    bl_label = ""

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        EnableFTransf(context)
        return {'FINISHED'}


# Other Operations -------------------------------------------------------

# Remove a Brush or a Canvas
class BTool_Remove(Operator):
    """Removes all BoolTool config assigned to it"""
    bl_idname = "btool.remove"
    bl_label = ""
    bl_options = {'UNDO'}
    thisObj = bpy.props.StringProperty("")
    Prop = bpy.props.StringProperty("")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        Remove(context, self.thisObj, self.Prop)
        return {'FINISHED'}


# Apply All to Canvas
class BTool_AllBrushToMesh(Operator):
    """Apply all brushes of this canvas"""
    bl_idname = "btool.to_mesh"
    bl_label = "Apply All Canvas"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        list = bpy.context.selected_objects
        ApplyAll(context, list)
        return {'FINISHED'}


# Apply This Brush to the Canvas
class BTool_BrushToMesh(Operator):
    """Apply this brush to the canvas"""
    bl_idname = "btool.brush_to_mesh"
    bl_label = "Apply this Brush to Canvas"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):

        if isBrush(context.active_object):
            return True
        else:
            return False

    def execute(self, context):
        ApplyThisBrush(context, bpy.context.active_object)
        return {'FINISHED'}


# TODO
# Apply This Brush To Mesh


# ------------------- MENU CLASSES ------------------------------
# 3Dview Header Menu
class BoolTool_Menu(bpy.types.Menu):
    bl_label = "BoolTool Operators"
    bl_idname = "OBJECT_MT_BoolTool_Menu"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Auto Boolean:")
        self.layout.operator(Direct_Difference.bl_idname, icon="ROTACTIVE")
        self.layout.operator(Direct_Union.bl_idname, icon="ROTATECOLLECTION")
        self.layout.operator(Direct_Intersect.bl_idname, icon="ROTATECENTER")
        self.layout.operator(Direct_Slice.bl_idname, icon="ROTATECENTER")
        self.layout.operator(Direct_Subtract.bl_idname, icon="ROTACTIVE")
        self.layout.separator()

        layout.label(text="Brush Boolean:")
        self.layout.operator(BTool_Diff.bl_idname, icon="ROTACTIVE")
        self.layout.operator(BTool_Union.bl_idname, icon="ROTATECOLLECTION")
        self.layout.operator(BTool_Inters.bl_idname, icon="ROTATECENTER")
        self.layout.operator(BTool_Slice.bl_idname, icon="ROTATECENTER")
        self.layout.separator()

        self.layout.operator(BTool_DrawPolyBrush.bl_idname, icon="LINE_DATA")

        if (isCanvas(context.active_object)):
            self.layout.separator()
            self.layout.operator(BTool_AllBrushToMesh.bl_idname, icon="MOD_LATTICE", text="Apply All")
            Rem = self.layout.operator(BTool_Remove.bl_idname, icon="CANCEL", text="Remove All")
            Rem.thisObj = ""
            Rem.Prop = "CANVAS"

        if (isBrush(context.active_object)):
            self.layout.separator()
            self.layout.operator(BTool_BrushToMesh.bl_idname, icon="MOD_LATTICE", text="Apply Brush")
            Rem = self.layout.operator(BTool_Remove.bl_idname, icon="CANCEL", text="Remove Brush")
            Rem.thisObj = ""
            Rem.Prop = "BRUSH"


def VIEW3D_BoolTool_Menu(self, context):
    self.layout.menu(BoolTool_Menu.bl_idname)


# ---------------- Bool Tools ---------------------
class BoolTool_Tools(Panel):
    bl_label = "Bool Tool Operators"
    bl_idname = "BoolTool_Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "BoolTool"
    bl_context = "objectmode"

    def draw(self, context):
        row = self.layout.row(True)
        col = row.column(True)
        col.label("Auto Boolean:", icon="MODIFIER")
        col.separator()
        col.operator(Direct_Difference.bl_idname, icon="ROTACTIVE")
        col.operator(Direct_Union.bl_idname, icon="ROTATECOLLECTION")
        col.operator(Direct_Intersect.bl_idname, icon="ROTATECENTER")
        col.separator()
        col.operator(Direct_Slice.bl_idname, icon="ROTATECENTER")
        col.operator(Direct_Subtract.bl_idname, icon="ROTACTIVE")

        self.layout.separator()
        row = self.layout.row(True)
        col = row.column(True)
        col.label("Brush Boolean:", icon="MODIFIER")
        col.separator()
        col.operator(BTool_Diff.bl_idname, text="Difference", icon="ROTACTIVE")
        col.operator(BTool_Union.bl_idname, text="Union", icon="ROTATECOLLECTION")
        col.operator(BTool_Inters.bl_idname, text="Intersect", icon="ROTATECENTER")
        col.operator(BTool_Slice.bl_idname, text="Slice", icon="ROTATECENTER")

        self.layout.separator()
        row = self.layout.row(True)
        col = row.column(True)
        col.label("Draw:", icon="MESH_CUBE")
        col.separator()
        col.operator(BTool_DrawPolyBrush.bl_idname, icon="LINE_DATA")
        col.separator()


# ---------- Properties --------------------------------------------------------
class BoolTool_Config(Panel):
    bl_label = "Properties"
    bl_idname = "BoolTool_BConfig"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "BoolTool"
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):

        result = False
        actObj = bpy.context.active_object
        if (isCanvas(actObj) or isBrush(actObj) or isPolyBrush(actObj)):
            result = True
        return result

    def draw(self, context):
        actObj = bpy.context.active_object
        icon = ""

        row = self.layout.row(True)

        # CANVAS ---------------------------------------------------
        if isCanvas(actObj):
            row.label("CANVAS", icon="MESH_GRID")
            row = self.layout.row()
            row.prop(context.scene,'BoolHide', text ="Hide Bool objects")
            row = self.layout.row(True)
            row.operator(BTool_AllBrushToMesh.bl_idname, icon="MOD_LATTICE", text="Apply All")

            row = self.layout.row(True)
            Rem = row.operator(BTool_Remove.bl_idname, icon="CANCEL", text="Remove All")
            Rem.thisObj = ""
            Rem.Prop = "CANVAS"

            if isBrush(actObj):
                self.layout.separator()

        # BRUSH ------------------------------------------------------
        if isBrush(actObj):

            if (actObj["BoolToolBrush"] == "UNION"):
                icon = "ROTATECOLLECTION"
            if (actObj["BoolToolBrush"] == "DIFFERENCE"):
                icon = "ROTATECENTER"
            if (actObj["BoolToolBrush"] == "INTERSECT"):
                icon = "ROTACTIVE"
            if (actObj["BoolToolBrush"] == "SLICE"):
                icon = "ROTATECENTER"


            row = self.layout.row(True)
            row.label("BRUSH", icon=icon)
            # self.layout.separator()

            icon = ""
            if actObj["BoolTool_FTransform"] == "True":
                icon = "PMARKER_ACT"
            else:
                icon = "PMARKER"
            if isFTransf():
                pass

            if isFTransf():
                row = self.layout.row(True)
                row.operator(BTool_EnableFTransform.bl_idname, text="Fast Vis", icon=icon)
                Enable = row.operator(BTool_EnableThisBrush.bl_idname, text="Enable", icon="VISIBLE_IPO_ON")
                row = self.layout.row(True)
            else:
                Enable = row.operator(BTool_EnableThisBrush.bl_idname, icon="VISIBLE_IPO_ON")
                row = self.layout.row(True)

        if isPolyBrush(actObj):
            row = self.layout.row(False)
            row.label("POLY BRUSH", icon="LINE_DATA")
            mod = actObj.modifiers["BTool_PolyBrush"]
            row = self.layout.row(False)
            row.prop(mod, "thickness", text="Size")
            self.layout.separator()

        if isBrush(actObj):
            row = self.layout.row(True)
            row.operator(BTool_BrushToMesh.bl_idname, icon="MOD_LATTICE", text="Apply Brush")
            row = self.layout.row(True)
            Rem = row.operator(BTool_Remove.bl_idname, icon="CANCEL", text="Remove Brush")
            Rem.thisObj = ""
            Rem.Prop = "BRUSH"

        self.layout.separator()


# ---------- Tree Viewer-------------------------------------------------------
class BoolTool_BViwer(Panel):
    bl_label = "Brush Viewer"
    bl_idname = "BoolTool_BViwer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "BoolTool"
    bl_context = "objectmode"

    @classmethod
    def poll(cls, context):
        actObj = bpy.context.active_object

        if isCanvas(actObj):
            return True
        else:
            return False

    def draw(self, context):

        actObj = bpy.context.active_object
        icon = ""

        if isCanvas(actObj):

            for mod in actObj.modifiers:
                container = self.layout.box()
                row = container.row(True)
                icon = ""
                if ("BTool_" in mod.name):
                    if (mod.operation == "UNION"):
                        icon = "ROTATECOLLECTION"
                    if (mod.operation == "DIFFERENCE"):
                        icon = "ROTATECENTER"
                    if (mod.operation == "INTERSECT"):
                        icon = "ROTACTIVE"
                    if (mod.operation == "SLICE"):
                        icon = "ROTATECENTER"

                    objSelect = row.operator("btool.find_brush", text=mod.object.name, icon=icon, emboss=False)
                    objSelect.obj = mod.object.name

                    EnableIcon = "RESTRICT_VIEW_ON"
                    if (mod.show_viewport):
                        EnableIcon = "RESTRICT_VIEW_OFF"
                    Enable = row.operator(BTool_EnableBrush.bl_idname, icon=EnableIcon, emboss=False)
                    Enable.thisObj = mod.object.name

                    Remove = row.operator("btool.remove", icon="CANCEL", emboss=False)
                    Remove.thisObj = mod.object.name
                    Remove.Prop = "THIS"

                    # Stack Changer
                    Up = row.operator("btool.move_stack", icon="TRIA_UP", emboss=False)
                    Up.modif = mod.name
                    Up.direction = "UP"

                    Dw = row.operator("btool.move_stack", icon="TRIA_DOWN", emboss=False)
                    Dw.modif = mod.name
                    Dw.direction = "DOWN"

                else:
                    row.label(mod.name)
                    # Stack Changer
                    Up = row.operator("btool.move_stack", icon="TRIA_UP", emboss=False)
                    Up.modif = mod.name
                    Up.direction = "UP"

                    Dw = row.operator("btool.move_stack", icon="TRIA_DOWN", emboss=False)
                    Dw.modif = mod.name
                    Dw.direction = "DOWN"


# ------------------ BOOL TOOL ADD-ON PREFERENCES ----------------------------

def UpdateBoolTool_Pref(self, context):
    if self.fast_transform:
        RegisterFastT()
    else:
        UnRegisterFastT()


class BoolTool_Pref(bpy.types.AddonPreferences):
    bl_idname = __name__

    fast_transform = bpy.props.BoolProperty(name="Fast Transformations", default=False, update=UpdateBoolTool_Pref,
                                            description="Replace the Transform HotKeys (G,R,S) for a custom version that can optimize the visualization of Brushes")

    make_vertex_groups = bpy.props.BoolProperty(name="Make Vertex Groups", default=False,
                                                description="When Apply a Brush to de Object it will create a new vertex group of the new faces")
    make_boundary = bpy.props.BoolProperty(name="Make Boundary", default=False,
                                           description="When Apply a Brush to de Object it will create a new vertex group of the bondary boolean area")
    use_wire = bpy.props.BoolProperty(name="Use Bmesh", default=False, description="Use The Wireframe Instead Of Boolean")

    def draw(self, context):
        layout = self.layout
        layout.label(text="Experimental Features:")
        layout.prop(self, "fast_transform")
        layout.prop(self, "use_wire", text = "Use Wire Instead Of Bbox ")
        """
        # EXPERIMENTAL
        layout.prop(self, "make_vertex_groups")
        layout.prop(self, "make_boundary")
        """

# ------------------- Class List ------------------------------------------------
classes = (
#Booltron
    Direct_Union,
    Direct_Difference,
    Direct_Intersect,
    Direct_Slice,
    Direct_Subtract,
#Bool Tools
    BTool_Union,
    BTool_Diff,
    BTool_Inters,
    BTool_Slice,
    BTool_DrawPolyBrush,
    BTool_Remove,
    BTool_AllBrushToMesh,
    BTool_BrushToMesh,
    BTool_FindBrush,
    BTool_MoveStack,
    BTool_EnableBrush,
    BTool_EnableThisBrush,
    BTool_EnableFTransform,
    BoolTool_Menu,
    BoolTool_Tools,
    BoolTool_Config,
    BoolTool_BViwer,
    BTool_FastTransform,
    BoolTool_Pref,
)
# ------------------- REGISTER ------------------------------------------------
addon_keymaps = []
addon_keymapsFastT = []


# Fast Transform HotKeys Register
def RegisterFastT():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')

    kmi = km.keymap_items.new(BTool_FastTransform.bl_idname, 'G', 'PRESS')
    kmi.properties.operator = "Translate"
    addon_keymapsFastT.append((km, kmi))

    kmi = km.keymap_items.new(BTool_FastTransform.bl_idname, 'R', 'PRESS')
    kmi.properties.operator = "Rotate"
    addon_keymapsFastT.append((km, kmi))

    kmi = km.keymap_items.new(BTool_FastTransform.bl_idname, 'S', 'PRESS')
    kmi.properties.operator = "Scale"
    addon_keymapsFastT.append((km, kmi))


# Fast Transform HotKeys UnRegister
def UnRegisterFastT():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode', space_type='EMPTY')

    for km, kmi in addon_keymapsFastT:
        km.keymap_items.remove(kmi)
    addon_keymapsFastT.clear()


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
        # Scene variables
    bpy.types.Scene.BoolHide = bpy.props.BoolProperty(default = False, description ='Hide boolean objects', update = update_BoolHide)
    # Handlers
    bpy.app.handlers.scene_update_post.append(HandleScene)

    bpy.types.VIEW3D_MT_object.append(VIEW3D_BoolTool_Menu)

    # create the boolean menu hotkey
    km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
    kmi = km.keymap_items.new('wm.call_menu', 'B', 'PRESS', ctrl=True, shift=True)
    kmi.properties.name = 'OBJECT_MT_BoolTool_Menu'

    addon_keymaps.append(km)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_object.remove(VIEW3D_BoolTool_Menu)

    # Add Handlers
    bpy.app.handlers.scene_update_post.remove(HandleScene)

    # Keymapping
    # remove keymaps when add-on is deactivated
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        wm.keyconfigs.addon.keymaps.remove(km)
    del addon_keymaps[:]
    del bpy.types.Scene.BoolHide

if __name__ == "__main__":
    register()
