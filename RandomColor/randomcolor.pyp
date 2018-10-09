# Author: safina3d
# Url: https://safina3d.blogspot.com
# Repo: https://github.com/safina3d/c4d-random-color

import os
import c4d
from c4d import bitmaps, plugins, Vector, BaseList2D, gui
from random import randint

IS_NEW_C4D_VERSION = c4d.GetC4DVersion() > 18000

if IS_NEW_C4D_VERSION:
    from c4d import Material as C4dMaterial
else:
    from c4d import BaseMaterial as C4dMaterial


class Utils:

    @staticmethod
    def get_icon_instance(image_file):
        """ Return BaseBitmap instance """
        _path, _file_name = os.path.split(__file__)
        icon = bitmaps.BaseBitmap()
        icon.InitWith(os.path.join(_path, 'res', image_file))
        return icon


class Helper:

    MATERIAL_CHANNELS = [
        c4d.MATERIAL_USE_COLOR,
        c4d.MATERIAL_USE_DIFFUSION,
        c4d.MATERIAL_USE_LUMINANCE,
        c4d.MATERIAL_USE_TRANSPARENCY,
        c4d.MATERIAL_USE_REFLECTION,
        c4d.MATERIAL_USE_ENVIRONMENT,
        c4d.MATERIAL_USE_FOG,
        c4d.MATERIAL_USE_BUMP,
        c4d.MATERIAL_USE_NORMAL,
        c4d.MATERIAL_USE_ALPHA,
        c4d.MATERIAL_USE_GLOW,
        c4d.MATERIAL_USE_DISPLACEMENT
    ]

    MATERIAL_CHANNELS_PROPERTIES = [
        c4d.MATERIAL_COLOR_COLOR,
        c4d.MATERIAL_DIFFUSION_SHADER,
        c4d.MATERIAL_LUMINANCE_COLOR,
        c4d.MATERIAL_TRANSPARENCY_COLOR,
        c4d.REFLECTION_LAYER_COLOR_COLOR,
        c4d.MATERIAL_ENVIRONMENT_COLOR,
        c4d.MATERIAL_FOG_COLOR,
        c4d.MATERIAL_BUMP_SHADER,
        c4d.MATERIAL_NORMAL_SHADER,
        c4d.MATERIAL_ALPHA_SHADER,
        c4d.MATERIAL_GLOW_COLOR,
        c4d.MATERIAL_DISPLACEMENT_SHADER
    ]

    MATERIAL_CHANNELS_COUNT = len(MATERIAL_CHANNELS)

    @staticmethod
    def is_shader(prop):
        return prop in [
            c4d.MATERIAL_DIFFUSION_SHADER,
            c4d.MATERIAL_BUMP_SHADER,
            c4d.MATERIAL_NORMAL_SHADER,
            c4d.MATERIAL_ALPHA_SHADER,
            c4d.MATERIAL_DISPLACEMENT_SHADER,
    ]

    @staticmethod
    def is_reflection_layer(prop):
        return prop == c4d.REFLECTION_LAYER_COLOR_COLOR and IS_NEW_C4D_VERSION

    @staticmethod
    def get_random_color():
        """ Return a random color as c4d.Vector """
        def get_random_value():
            """ Return a random value between 0.0 and 1.0 """
            return randint(0, 255) / 256.0
        return Vector(get_random_value(), get_random_value(), get_random_value())

    @staticmethod
    def get_next_object(current_object):
        """ Return the next object in the hierarchy """
        if current_object.GetDown():
            return current_object.GetDown()
        while not current_object.GetNext() and current_object.GetUp():
            current_object = current_object.GetUp()
        return current_object.GetNext()

    @staticmethod
    def set_color(obj, used_colors):
        """ Apply a random color to an object """
        color = Helper.get_random_color()
        # Check that the current color is not already used
        while color in used_colors:
            color = Helper.get_random_color()
        used_colors.append(color)
        # Apply the chosen color to the object
        obj[c4d.ID_BASEOBJECT_USECOLOR] = c4d.ID_BASEOBJECT_USECOLOR_ALWAYS
        obj[c4d.ID_BASEOBJECT_COLOR] = color

    @staticmethod
    def remove_color(obj):
        """ Remove color from """
        obj[c4d.ID_BASEOBJECT_USECOLOR] = c4d.ID_BASEOBJECT_USECOLOR_OFF

    @staticmethod
    def convert_display_color_to_material(doc, obj, settings):
        display_color_is_active = obj[c4d.ID_BASEOBJECT_USECOLOR]
        if display_color_is_active == c4d.ID_BASEOBJECT_USECOLOR_ALWAYS:
            # Create new material
            material = C4dMaterial(c4d.Mmaterial)
            material.SetName(obj.GetName())
            doc.InsertMaterial(material)
            # Retrieve current object color and assign it to the created material
            offset = 0
            object_color = obj[c4d.ID_BASEOBJECT_COLOR]
            for i in xrange(Helper.MATERIAL_CHANNELS_COUNT):
                is_active_channel = settings[offset]
                apply_color = settings[offset + 1]
                if is_active_channel:
                    material[Helper.MATERIAL_CHANNELS[i]] = 1
                    if apply_color:
                        channel_propertie = Helper.MATERIAL_CHANNELS_PROPERTIES[i]
                        # Shader color case
                        if Helper.is_shader(channel_propertie):
                            shader = c4d.BaseList2D(c4d.Xcolor)
                            shader[c4d.COLORSHADER_COLOR] = object_color
                            material[channel_propertie] = shader
                            material.InsertShader(shader)
                        # Reflection layer case
                        elif Helper.is_reflection_layer(channel_propertie):
                            reflection_layers = material.GetReflectionPrimaryLayers()
                            layer = material.GetReflectionLayerIndex(reflection_layers[1])
                            material[layer.GetDataID() + c4d.REFLECTION_LAYER_COLOR_COLOR] = object_color
                        # Basic color case
                        else:
                            material[channel_propertie] = object_color
                else:
                    material[Helper.MATERIAL_CHANNELS[i]] = 0
                offset += 2

            material.Message(c4d.MSG_UPDATE)
            material.Update(True, True)
            # Disable display color
            obj[c4d.ID_BASEOBJECT_USECOLOR] = c4d.ID_BASEOBJECT_USECOLOR_OFF
            # Assign material tag to the object
            tag = obj.MakeTag(c4d.Ttexture)
            tag[c4d.TEXTURETAG_MATERIAL] = material


class RandomColor(plugins.CommandData):

    def Execute(self, doc):
        c4d.StopAllThreads()
        doc.StartUndo()
        self.perform(doc)
        doc.EndUndo()
        c4d.EventAdd()
        return True

    def GetState(self, doc):
        if doc.GetFirstObject() is None:
            return 0
        return c4d.CMD_ENABLED

    def perform(self, doc):
        pass


class RcColor(RandomColor):

    def perform(self, doc):
        """ Assign a random color to selected objects """
        used_colors_list = []
        selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_SELECTIONORDER)

        if len(selected_objects) > 0:
            for obj in selected_objects:
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                Helper.set_color(obj, used_colors_list)
        else:
            obj = doc.GetFirstObject()
            while obj is not None:
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                Helper.set_color(obj, used_colors_list)
                obj = Helper.get_next_object(obj)


class RcUncolor(RandomColor):

    def perform(self, doc):
        """ Disable display color """
        selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_SELECTIONORDER)

        if len(selected_objects) > 0:
            for obj in selected_objects:
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                Helper.remove_color(obj)
        else:
            obj = doc.GetFirstObject()
            while obj is not None:
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                Helper.remove_color(obj)
                obj = Helper.get_next_object(obj)


class RcConvertSettingsGUI(gui.GeDialog):

    ID_DLG_SETTINGS = 1000
    ID_BTN_SAVE = 2000
    ID_CHECKBOX_REF = 3000

    def InitValues(self):
        for index, value in enumerate(RcConvert.SETTINGS):
            self.SetBool(RcConvertSettingsGUI.ID_CHECKBOX_REF + index, value)
            if index % 2 == 1 and not value:
                self.Enable(RcConvertSettingsGUI.ID_CHECKBOX_REF + index, False)
        return super(RcConvertSettingsGUI, self).InitValues()

    def Command(self, id, msg):
        # Handle save button behaviour
        if id == RcConvertSettingsGUI.ID_BTN_SAVE:
            offset = 0
            for idx in xrange(Helper.MATERIAL_CHANNELS_COUNT):
                RcConvert.SETTINGS[offset] = self.GetBool(RcConvertSettingsGUI.ID_CHECKBOX_REF + offset)
                RcConvert.SETTINGS[offset + 1] = self.GetBool(RcConvertSettingsGUI.ID_CHECKBOX_REF + offset + 1)
                offset += 2
            self.Close()

        # Handle checkboxes behaviour
        if (id - RcConvertSettingsGUI.ID_CHECKBOX_REF) % 2 == 0:
            cbx_state = self.GetBool(id)
            id_next = id + 1
            if cbx_state:
                self.Enable(id_next, True)
                self.SetBool(id_next, True)
            else:
                self.Enable(id_next, False)
                self.SetBool(id_next, False)

        return super(RcConvertSettingsGUI, self).Command(id, msg)

    def CreateLayout(self):
        return self.LoadDialogResource(RcConvertSettingsGUI.ID_DLG_SETTINGS)


class RcConvert(RandomColor):

    DIALOG = None
    SETTINGS = [True, True] + [False for i in range(22)]

    def perform(self, doc):
        """ Convert display colors to materials """
        selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_SELECTIONORDER)

        if len(selected_objects) > 0:
            for obj in selected_objects:
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                Helper.convert_display_color_to_material(doc, obj, RcConvert.SETTINGS)
        else:
            obj = doc.GetFirstObject()
            while obj is not None:
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                Helper.convert_display_color_to_material(doc, obj, RcConvert.SETTINGS)
                obj = Helper.get_next_object(obj)

    def ExecuteOptionID(self, doc, plugid, subid):
        if RcConvert.DIALOG is None:
            RcConvert.DIALOG = RcConvertSettingsGUI()

        screen = gui.GeGetScreenDimensions(0, 0, True)
        return RcConvert.DIALOG.Open(c4d.DLG_TYPE_MODAL, plugid, int(screen['sx2'] / 2) - 300, int(screen['sy2'] / 2) - 300)


if __name__ == '__main__':

    plugins.RegisterCommandPlugin(
        id=1039790,
        str='Assign random color',
        info=0,
        icon=Utils.get_icon_instance('color.tif'),
        help='Assign random color to selected/all objects',
        dat=RcColor()
    )

    plugins.RegisterCommandPlugin(
        id=1039791,
        str='Disable display color',
        info=0,
        icon=Utils.get_icon_instance('uncolor.tif'),
        help='Uncolor selected/all objects',
        dat=RcUncolor()
    )

    plugins.RegisterCommandPlugin(
        id=1039792,
        str='Convert display color to material',
        info=c4d.PLUGINFLAG_COMMAND_OPTION_DIALOG,
        icon=Utils.get_icon_instance('color_to_material.tif'),
        help='Convert display colors to materials',
        dat=RcConvert()
    )
