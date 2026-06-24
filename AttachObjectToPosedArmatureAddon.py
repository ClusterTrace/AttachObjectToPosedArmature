bl_info = {
    "name": "Armature Deform With Current Pose",
    "author": "ClusterTrace",
    "version": (1, 0, 0),
    "blender": (5, 1, 0),
    "location": "View3D > Object > Parent",
    "description": "Attaches selected objects to the active armature at the active armature's current pose",
    "category": "Rigging",
}

import bpy


def main(context):
    # grabs data
    armatureObject = bpy.context.active_object # assumes active object is the armature
    selectedObjects = bpy.context.selected_objects
    selectedObjects.remove(armatureObject) # removes armature object from selected objects for convenience later
    # duplicates armature
    duplicateArmature = armatureObject.copy()
    duplicateArmature.data = armatureObject.data.copy()
    bpy.context.collection.objects.link(duplicateArmature)
    #deletes keyframes on duplicate armature
    if duplicateArmature and duplicateArmature.animation_data:
        duplicateArmature.animation_data_clear()
    # applies rest pose to the duplicate armature
    with bpy.context.temp_override(active_object=duplicateArmature, selected_objects=[duplicateArmature]):
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.armature_apply(selected=False)
    # attaches each selected object to the duplicate armature using a modifier only method (assumes that it wasn't already attached to another armature)
    armatureModifiers = [] # stores the armature modifiers in sequence with the selectedObjects
    for tempObj in selectedObjects:
        armatureModifer = tempObj.modifiers.new("Armature", type='ARMATURE')
        armatureModifer.object = bpy.data.objects[duplicateArmature.name]
        armatureModifer.use_deform_preserve_volume = True # prevents shrinking when moving back to rest pose
        armatureModifiers.append(armatureModifer)
    # moves the armature modifiers to the top of the modifier stack
    for i in range(len(armatureModifiers)):
       selectedObjects[i].modifiers.move(selectedObjects[i].modifiers.find(armatureModifiers[i].name), 0)
    # adds a copy transform to each bone on the duplicate armature targeted at the corresponding bone on the original armature assuming the default settings for the constraint (Head/Tail = 0, Remove Target Shear = False, Mix = Replace, Target = World Space, Owner = World Space, Influence = 1)
    for poseBone in duplicateArmature.pose.bones:
        constraint = poseBone.constraints.new(type='COPY_TRANSFORMS')
        constraint.target = bpy.data.objects[armatureObject.name]
        constraint.subtarget = poseBone.name # names for the bones should be the same
    # stores the original pose
    originalPoseByBone = []
    for poseBone in armatureObject.pose.bones:
        tempRotation = None
        if poseBone.rotation_mode == 'QUATERNION': # grabs rotation based on mode
            tempRotation = poseBone.rotation_quaternion.copy()
        elif poseBone.rotation_mode == 'AXIS_ANGLE':
            tempRotation = poseBone.rotation_axis_angle.copy()
        else: # Handles Euler modes (XYZ, XZY, etc.)
            tempRotation = poseBone.rotation_euler.copy()
        originalPoseByBone.append({'location': poseBone.location.copy(), 'rotation': tempRotation, 'scale': poseBone.scale.copy()})
    # resets the pose on the original armature
    for poseBone in armatureObject.pose.bones:
        # reset displacement
        poseBone.location = (0.0, 0.0, 0.0)
        # Reset rotation based on the current rotation mode
        if poseBone.rotation_mode == 'QUATERNION':
            poseBone.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        elif poseBone.rotation_mode == 'AXIS_ANGLE':
            poseBone.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)
        else: # Handles Euler modes (XYZ, XZY, etc.)
            poseBone.rotation_euler = (0.0, 0.0, 0.0)
        # Reset scale vector
        poseBone.scale = (1.0, 1.0, 1.0)
    # applies the armature deformation on the objects so they are at where they should be at the original armature's rest pose
    for i in range(len(selectedObjects)):
        if selectedObjects[i] and armatureModifiers[i].name in selectedObjects[i].modifiers:
            with bpy.context.temp_override(object=selectedObjects[i]):
                bpy.ops.object.modifier_apply(modifier=armatureModifiers[i].name)
    # deletes the duplicate armature
    bpy.data.objects.remove(duplicateArmature, do_unlink=True)
    # attach the objects to the original armature using the parenting method
    with bpy.context.temp_override(active_object=armatureObject, selected_objects=selectedObjects):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.parent_set(type='ARMATURE')
    # reverts back to the original pose
    for i in range(len(originalPoseByBone)):
        armatureObject.pose.bones[i].location = originalPoseByBone[i].get("location")
        armatureObject.pose.bones[i].scale = originalPoseByBone[i].get("scale")
        if armatureObject.pose.bones[i].rotation_mode == 'QUATERNION': # grabs rotation based on mode
            armatureObject.pose.bones[i].rotation_quaternion = originalPoseByBone[i].get("rotation")
        elif armatureObject.pose.bones[i].rotation_mode == 'AXIS_ANGLE':
            armatureObject.pose.bones[i].rotation_axis_angle = originalPoseByBone[i].get("rotation")
        else: # Handles Euler modes (XYZ, XZY, etc.)
            armatureObject.pose.bones[i].rotation_euler = originalPoseByBone[i].get("rotation")


class ArmatureDeformWithCurrentPose(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.armature_deform_with_current_pose"
    bl_label = "Armature Deform With CurrentPose"
    bl_description = "This allows attaching selected objects to an active selection that is a posed armature without having the object then acquiring the deformations from that current pose (so intended for objects made with the pose in mind). To work correctly the objects should already contain appropriate weight painting (can try transfering weight painting from another object or using automatic weight painting from an applied rest pose version of the armature if in need of weight painting)."

    @classmethod
    def poll(cls, context):
        # grabs data here to check if data is valid
        armatureObject = bpy.context.active_object # assumes active object is the armature
        selectedObjects = bpy.context.selected_objects
        selectedObjects.remove(armatureObject) # removes armature object from selected objects for convenience later
        # performs requires prerunning checks to prevent errors
        validToContinue = True
        if (context.active_object is None):
            validToContinue = False
        elif (armatureObject.type != "ARMATURE"):
            validToContinue = False
            #self.report({'INFO'}, "Active object is not an armature") # Cannot use "self" in poll as only execute has "self"
        elif (not (len(selectedObjects) > 0)):
            validToContinue = False
            #self.report({'INFO'}, "No objects in selection to attach to armature") # Cannot use "self" in poll as only execute has "self"
        return validToContinue

    def execute(self, context):
        main(context)
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ArmatureDeformWithCurrentPose.bl_idname, text=ArmatureDeformWithCurrentPose.bl_label)

# draw section specification
def draw_in_parent_submenu(self, context):
    layout = self.layout 
    layout.separator()
    layout.operator(
        ArmatureDeformWithCurrentPose.bl_idname, 
        text="Armature Deform With Current Pose",
        #icon='ARMATURE_DATA'
    )


# Register and add to the "object" menu (required to also use F3 search "Simple Object Operator" for quick access).
def register():
    bpy.utils.register_class(ArmatureDeformWithCurrentPose)
    #bpy.types.VIEW3D_MT_object.append(menu_func)
    bpy.types.VIEW3D_MT_object_parent.append(draw_in_parent_submenu) # Append the custom tool to the standard Parent menu


def unregister():
    bpy.utils.unregister_class(ArmatureDeformWithCurrentPose)
    #bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.types.VIEW3D_MT_object_parent.remove(draw_in_parent_submenu) # Remove the draw function from the Parent menu


if __name__ == "__main__":
    register()
