import os
import c4d
from c4d import bitmaps, plugins, Vector, BaseMaterial
from random import randint


class Utils:
    @staticmethod
    def get_icon_instance(image_file):
        """ Return BaseBitmap instance """
        _path, _file_name = os.path.split(__file__)
        icon = bitmaps.BaseBitmap()
        icon.InitWith(os.path.join(_path, 'res', image_file))
        return icon

class Helper:
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
    def convert_color_to_material(doc, obj):
        display_color_is_active = obj[c4d.ID_BASEOBJECT_USECOLOR]
        if display_color_is_active == c4d.ID_BASEOBJECT_USECOLOR_ALWAYS:
            # Create new material
            material = BaseMaterial(c4d.Mmaterial)
            material.SetName(obj.GetName())
            doc.InsertMaterial(material)
            # Retrieve current object color and assign it to the created material
            object_color = obj[c4d.ID_BASEOBJECT_COLOR]
            material[c4d.MATERIAL_COLOR_COLOR] = object_color
            material.Message(c4d.MSG_UPDATE)
            # Disable display color
            obj[c4d.ID_BASEOBJECT_USECOLOR] = c4d.ID_BASEOBJECT_USECOLOR_OFF
            # Assign material tag to the object
            tag = obj.MakeTag(c4d.Ttexture)
            tag[c4d.TEXTURETAG_MATERIAL] = material


class RandomColor(plugins.CommandData):

    def Execute(self, doc):
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


class RcConvert(RandomColor):

    def perform(self, doc):
        """ Convert display colors to materials """
        selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_SELECTIONORDER)

        if len(selected_objects) > 0:
            for obj in selected_objects:
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                Helper.convert_color_to_material(doc, obj)
        else:
            obj = doc.GetFirstObject()
            while obj is not None:
                doc.AddUndo(c4d.UNDOTYPE_CHANGE, obj)
                Helper.convert_color_to_material(doc, obj)
                obj = Helper.get_next_object(obj)


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
        str='Convert color to material',
        info=0,
        icon=Utils.get_icon_instance('color_to_material.tif'),
        help='Convert display colors to materials',
        dat=RcConvert()
    )
