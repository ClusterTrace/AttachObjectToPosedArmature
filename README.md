# AttachObjectToPosedArmature
An addon for blender that allows attaching a rigged object to a posed armature without the rig's pose altering the object.

The purpose of the addon is to assist in cases where objects, such as clothes, were created for a character when the character is posed.
The addon requires the objects contain weight painting/rigging for the armature prior to the attachment. It is recommended to thus either have done it with conventional methods or manaully, or perhaps using an automated method such as:
1. Haing a duplicate version of the armature, with the pose applied to be the rest pose, so one can attach the object to this duplicate armature to get automatic deformations (can unparent and delete the duplicate armature after)
2. Using weight paint transfer if the object is like a piece of clothing and there is character to pull weight painting from

The button can be found in the 3D viewport under Object -> Parent -> Armature Deform With Current Pose
The button requires an armature be selected and active as well as some selected objects to attach to the armature.
