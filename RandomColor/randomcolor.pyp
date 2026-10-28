# Author: safina3d
# Version: 1.3
# Url: https://safina3d.blogspot.com
# Repo: https://github.com/safina3d/c4d-random-color
# Compatibility: Cinema 4D R20+ (Python 2.7 and Python 3)

import os
import colorsys
import random
import c4d
from c4d import bitmaps, plugins, Vector, gui

PLUGIN_ID_COLOR = 1039790
PLUGIN_ID_UNCOLOR = 1039791
PLUGIN_ID_CONVERT = 1039792

# Golden ratio conjugate: successive hues are spread evenly around the color wheel
GOLDEN_RATIO_CONJUGATE = 0.618033988749895


class Utils:

    @staticmethod
    def get_icon_instance(image_file):
        """ Return BaseBitmap instance """
        _path, _file_name = os.path.split(__file__)
        icon = bitmaps.BaseBitmap()
        icon.InitWith(os.path.join(_path, 'res', image_file))
        return icon


class ColorGenerator(object):
    """ Generate visually distinct colors without collision checks """

    # Saturation/value pairs cycled to add contrast between consecutive colors
    SHADES = ((0.75, 0.95), (0.55, 0.75), (0.9, 0.85))

    def __init__(self, start_hue=None):
        self.hue = random.random() if start_hue is None else start_hue
        self.index = 0

    def next_color(self):
        """ Return the next color as c4d.Vector """
        self.hue = (self.hue + GOLDEN_RATIO_CONJUGATE) % 1.0
        saturation, value = ColorGenerator.SHADES[self.index % len(ColorGenerator.SHADES)]
        self.index += 1
        return Vector(*colorsys.hsv_to_rgb(self.hue, saturation, value))


class Helper:

    CHANNEL_COLOR, CHANNEL_SHADER, CHANNEL_REFLECTION = range(3)

    # (channel activation ID, channel color parameter ID, how the color is applied)
    # Order must match the dialog rows (res/dialogs/dlg_settings.res)
    MATERIAL_CHANNELS = (
        (c4d.MATERIAL_USE_COLOR, c4d.MATERIAL_COLOR_COLOR, CHANNEL_COLOR),
        (c4d.MATERIAL_USE_DIFFUSION, c4d.MATERIAL_DIFFUSION_SHADER, CHANNEL_SHADER),
        (c4d.MATERIAL_USE_LUMINANCE, c4d.MATERIAL_LUMINANCE_COLOR, CHANNEL_COLOR),
        (c4d.MATERIAL_USE_TRANSPARENCY, c4d.MATERIAL_TRANSPARENCY_COLOR, CHANNEL_COLOR),
        (c4d.MATERIAL_USE_REFLECTION, c4d.REFLECTION_LAYER_COLOR_COLOR, CHANNEL_REFLECTION),
        (c4d.MATERIAL_USE_ENVIRONMENT, c4d.MATERIAL_ENVIRONMENT_COLOR, CHANNEL_COLOR),
        (c4d.MATERIAL_USE_FOG, c4d.MATERIAL_FOG_COLOR, CHANNEL_COLOR),
        (c4d.MATERIAL_USE_BUMP, c4d.MATERIAL_BUMP_SHADER, CHANNEL_SHADER),
        (c4d.MATERIAL_USE_NORMAL, c4d.MATERIAL_NORMAL_SHADER, CHANNEL_SHADER),
        (c4d.MATERIAL_USE_ALPHA, c4d.MATERIAL_ALPHA_SHADER, CHANNEL_SHADER),
        (c4d.MATERIAL_USE_GLOW, c4d.MATERIAL_GLOW_COLOR, CHANNEL_COLOR),
        (c4d.MATERIAL_USE_DISPLACEMENT, c4d.MATERIAL_DISPLACEMENT_SHADER, CHANNEL_SHADER),
    )

    MATERIAL_CHANNELS_COUNT = len(MATERIAL_CHANNELS)

    @staticmethod
    def get_next_object(current_object):
        """ Return the next object in the hierarchy """
        if current_object.GetDown():
            return current_object.GetDown()
        while not current_object.GetNext() and current_object.GetUp():
            current_object = current_object.GetUp()
        return current_object.GetNext()

    @staticmethod
    def iter_hierarchy(obj):
        """ Yield obj and every object after it in the hierarchy (depth-first) """
        while obj is not None:
            yield obj
            obj = Helper.get_next_object(obj)

    @staticmethod
    def iter_target_objects(doc):
        """ Yield selected objects (with their children), or all objects if nothing is selected """
        selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_CHILDREN)
        if selected_objects:
            return iter(selected_objects)
        return Helper.iter_hierarchy(doc.GetFirstObject())

    @staticmethod
    def get_display_color(doc, obj):
        """
        Return the display color explicitly chosen for obj, or None.
        Only "On" (object color) and "Layer" (layer color) modes are converted;
        "Automatic" is ignored because it only shows when the object has no material.
        """
        mode = obj[c4d.ID_BASEOBJECT_USECOLOR]
        if mode == c4d.ID_BASEOBJECT_USECOLOR_ALWAYS:
            return obj[c4d.ID_BASEOBJECT_COLOR]
        if mode == c4d.ID_BASEOBJECT_USECOLOR_LAYER:
            layer = obj.GetLayerObject(doc)
            if layer is not None:
                return layer[c4d.ID_LAYER_COLOR]
        return None

    @staticmethod
    def set_reflection_color(material, color):
        """ Apply color to the primary specular layer, or to the primary reflection layer as fallback """
        reflection_layer, specular_layer = material.GetReflectionPrimaryLayers()
        # -1 means no layer
        layer_index = specular_layer if specular_layer != -1 else reflection_layer
        if layer_index == -1:
            return
        layer = material.GetReflectionLayerIndex(layer_index)
        if layer is not None:
            material[layer.GetDataID() + c4d.REFLECTION_LAYER_COLOR_COLOR] = color

    @staticmethod
    def create_material(doc, name, color, settings):
        """ Create and insert a material using color on the channels enabled in settings """
        material = c4d.Material(c4d.Mmaterial)
        material.SetName(name)
        doc.InsertMaterial(material)
        doc.AddUndo(c4d.UNDOTYPE_NEW, material)

        for index, (use_id, property_id, kind) in enumerate(Helper.MATERIAL_CHANNELS):
            is_active = settings[2 * index]
            apply_color = settings[2 * index + 1]
            material[use_id] = is_active
            if not (is_active and apply_color):
                continue
            if kind == Helper.CHANNEL_SHADER:
                shader = c4d.BaseList2D(c4d.Xcolor)
                shader[c4d.COLORSHADER_COLOR] = color
                # The shader must belong to the material before being linked
                material.InsertShader(shader)
                material[property_id] = shader
            elif kind == Helper.CHANNEL_REFLECTION:
                Helper.set_reflection_color(material, color)
            else:
                material[property_id] = color

        material.Message(c4d.MSG_UPDATE)
        material.Update(True, True)
        return material


class Settings:
    """ Material channels settings: one (active, apply color) pair per channel, saved in C4D preferences """

    DEFAULTS = [True, True] + [False] * (2 * (Helper.MATERIAL_CHANNELS_COUNT - 1))

    _values = None

    @staticmethod
    def get():
        """ Return the settings list, loaded from preferences on first access """
        if Settings._values is None:
            container = plugins.GetWorldPluginData(PLUGIN_ID_CONVERT)
            if container is None:
                Settings._values = list(Settings.DEFAULTS)
            else:
                Settings._values = [container.GetBool(index, default) for index, default in enumerate(Settings.DEFAULTS)]
        return Settings._values

    @staticmethod
    def set(values):
        """ Store the settings and save them in preferences """
        Settings._values = list(values)
        container = c4d.BaseContainer()
        for index, value in enumerate(Settings._values):
            container.SetBool(index, value)
        plugins.SetWorldPluginData(PLUGIN_ID_CONVERT, container, False)


class RandomColor(plugins.CommandData):

    def Execute(self, doc):
        c4d.StopAllThreads()
        doc.StartUndo()
        try:
            self.perform(doc)
        finally:
            # Always close the undo step, even if perform fails
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
        """ Assign a distinct random color to target objects """
        color_generator = ColorGenerator()
        for obj in Helper.iter_target_objects(doc):
            doc.AddUndo(c4d.UNDOTYPE_CHANGE_SMALL, obj)
            obj[c4d.ID_BASEOBJECT_USECOLOR] = c4d.ID_BASEOBJECT_USECOLOR_ALWAYS
            obj[c4d.ID_BASEOBJECT_COLOR] = color_generator.next_color()


class RcUncolor(RandomColor):

    def perform(self, doc):
        """ Disable display color """
        for obj in Helper.iter_target_objects(doc):
            if obj[c4d.ID_BASEOBJECT_USECOLOR] != c4d.ID_BASEOBJECT_USECOLOR_OFF:
                doc.AddUndo(c4d.UNDOTYPE_CHANGE_SMALL, obj)
                obj[c4d.ID_BASEOBJECT_USECOLOR] = c4d.ID_BASEOBJECT_USECOLOR_OFF


class RcConvertSettingsGUI(gui.GeDialog):

    # IDs defined in res/c4d_symbols.h
    ID_DLG_SETTINGS = 1000  # DLG_SETTINGS
    ID_BTN_SAVE = 2000  # ID_BTN_SAVE
    ID_CHECKBOX_REF = 3000  # ID_CHOICE_00, then one (active, apply color) checkbox pair per channel

    @staticmethod
    def get_active_checkbox_id(channel_index):
        return RcConvertSettingsGUI.ID_CHECKBOX_REF + 2 * channel_index

    @staticmethod
    def get_apply_checkbox_id(channel_index):
        return RcConvertSettingsGUI.ID_CHECKBOX_REF + 2 * channel_index + 1

    @staticmethod
    def get_channel_index_from_active_checkbox(gadget_id):
        """ Return the channel index if gadget_id is an "active" checkbox, otherwise None """
        offset = gadget_id - RcConvertSettingsGUI.ID_CHECKBOX_REF
        if 0 <= offset < 2 * Helper.MATERIAL_CHANNELS_COUNT and offset % 2 == 0:
            return offset // 2
        return None

    def InitValues(self):
        settings = Settings.get()
        for channel_index in range(Helper.MATERIAL_CHANNELS_COUNT):
            is_active = settings[2 * channel_index]
            apply_id = RcConvertSettingsGUI.get_apply_checkbox_id(channel_index)
            self.SetBool(RcConvertSettingsGUI.get_active_checkbox_id(channel_index), is_active)
            self.SetBool(apply_id, settings[2 * channel_index + 1])
            # "Apply color" is only editable when its channel is active
            self.Enable(apply_id, is_active)
        return super(RcConvertSettingsGUI, self).InitValues()

    def Command(self, id, msg):
        if id == RcConvertSettingsGUI.ID_BTN_SAVE:
            settings = []
            for channel_index in range(Helper.MATERIAL_CHANNELS_COUNT):
                settings.append(self.GetBool(RcConvertSettingsGUI.get_active_checkbox_id(channel_index)))
                settings.append(self.GetBool(RcConvertSettingsGUI.get_apply_checkbox_id(channel_index)))
            Settings.set(settings)
            self.Close()
        else:
            channel_index = RcConvertSettingsGUI.get_channel_index_from_active_checkbox(id)
            if channel_index is not None:
                is_active = self.GetBool(id)
                apply_id = RcConvertSettingsGUI.get_apply_checkbox_id(channel_index)
                self.Enable(apply_id, is_active)
                self.SetBool(apply_id, is_active)

        return super(RcConvertSettingsGUI, self).Command(id, msg)

    def CreateLayout(self):
        return self.LoadDialogResource(RcConvertSettingsGUI.ID_DLG_SETTINGS)


class RcConvert(RandomColor):

    DIALOG = None

    def perform(self, doc):
        """ Convert display colors to materials, sharing one material per color """
        settings = Settings.get()
        materials_by_color = {}
        for obj in Helper.iter_target_objects(doc):
            color = Helper.get_display_color(doc, obj)
            if color is None:
                continue

            color_key = (color.x, color.y, color.z)
            material = materials_by_color.get(color_key)
            if material is None:
                material = Helper.create_material(doc, obj.GetName(), color, settings)
                materials_by_color[color_key] = material

            doc.AddUndo(c4d.UNDOTYPE_CHANGE_SMALL, obj)
            obj[c4d.ID_BASEOBJECT_USECOLOR] = c4d.ID_BASEOBJECT_USECOLOR_OFF
            tag = obj.MakeTag(c4d.Ttexture)
            doc.AddUndo(c4d.UNDOTYPE_NEW, tag)
            tag[c4d.TEXTURETAG_MATERIAL] = material

    def ExecuteOptionID(self, doc, plugid, subid):
        if RcConvert.DIALOG is None:
            RcConvert.DIALOG = RcConvertSettingsGUI()

        screen = gui.GeGetScreenDimensions(0, 0, True)
        return RcConvert.DIALOG.Open(c4d.DLG_TYPE_MODAL, plugid, int(screen['sx2'] / 2) - 300, int(screen['sy2'] / 2) - 300)


if __name__ == '__main__':

    plugins.RegisterCommandPlugin(
        id=PLUGIN_ID_COLOR,
        str='Assign random color',
        info=0,
        icon=Utils.get_icon_instance('color.tif'),
        help='Assign random color to selected/all objects',
        dat=RcColor()
    )

    plugins.RegisterCommandPlugin(
        id=PLUGIN_ID_UNCOLOR,
        str='Disable display color',
        info=0,
        icon=Utils.get_icon_instance('uncolor.tif'),
        help='Uncolor selected/all objects',
        dat=RcUncolor()
    )

    plugins.RegisterCommandPlugin(
        id=PLUGIN_ID_CONVERT,
        str='Convert display color to material',
        info=c4d.PLUGINFLAG_COMMAND_OPTION_DIALOG,
        icon=Utils.get_icon_instance('color_to_material.tif'),
        help='Convert display colors to materials',
        dat=RcConvert()
    )
