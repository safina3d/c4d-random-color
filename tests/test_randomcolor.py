""" Unit tests for the pure logic of randomcolor.pyp, run outside Cinema 4D with a fake c4d module.

Usage: python -m unittest discover tests
"""

import importlib.util
import itertools
import os
import sys
import types
import unittest
from importlib.machinery import SourceFileLoader

PLUGIN_PATH = os.path.join(os.path.dirname(__file__), '..', 'RandomColor', 'randomcolor.pyp')


class FakeVector(object):

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = x, y, z


class FakeC4dModule(types.ModuleType):
    """ Any unknown constant resolves to a unique integer """

    _ids = itertools.count(100000)

    def __getattr__(self, name):
        value = next(FakeC4dModule._ids)
        setattr(self, name, value)
        return value


def load_plugin(world_plugin_data=None):
    c4d = FakeC4dModule('c4d')
    c4d.Vector = FakeVector
    c4d.bitmaps = types.SimpleNamespace(BaseBitmap=object)
    c4d.gui = types.SimpleNamespace(GeDialog=type('GeDialog', (object,), {}))
    c4d.plugins = types.SimpleNamespace(
        CommandData=type('CommandData', (object,), {}),
        GetWorldPluginData=lambda plugin_id: world_plugin_data,
    )
    sys.modules['c4d'] = c4d

    loader = SourceFileLoader('randomcolor', PLUGIN_PATH)
    spec = importlib.util.spec_from_loader('randomcolor', loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module, c4d


class FakeObject(object):

    def __init__(self, name, children=()):
        self.name = name
        self.up = self.next = None
        self.down = children[0] if children else None
        for child in children:
            child.up = self
        for previous, current in zip(children, children[1:]):
            previous.next = current

    def GetDown(self):
        return self.down

    def GetNext(self):
        return self.next

    def GetUp(self):
        return self.up


class FakeDocument(object):

    def __init__(self, first_object, selection=()):
        self.first_object = first_object
        self.selection = list(selection)

    def GetFirstObject(self):
        return self.first_object

    def GetActiveObjects(self, flags):
        return self.selection


def build_scene():
    """ A(B(C), D), E """
    c = FakeObject('C')
    b = FakeObject('B', [c])
    d = FakeObject('D')
    a = FakeObject('A', [b, d])
    e = FakeObject('E')
    a.next = e
    return a, e


class ColorGeneratorTest(unittest.TestCase):

    def setUp(self):
        self.plugin, _ = load_plugin()

    def test_colors_are_unique_and_in_range(self):
        generator = self.plugin.ColorGenerator()
        colors = [generator.next_color() for _ in range(10000)]
        keys = set((c.x, c.y, c.z) for c in colors)
        self.assertEqual(len(keys), len(colors))
        for color in colors:
            for component in (color.x, color.y, color.z):
                self.assertTrue(0.0 <= component <= 1.0)

    def test_consecutive_hues_are_far_apart(self):
        generator = self.plugin.ColorGenerator(start_hue=0.0)
        previous = generator.hue
        for _ in range(100):
            generator.next_color()
            distance = abs(generator.hue - previous)
            self.assertGreater(min(distance, 1.0 - distance), 0.3)
            previous = generator.hue


class HierarchyTest(unittest.TestCase):

    def setUp(self):
        self.plugin, _ = load_plugin()

    def test_iter_hierarchy_is_depth_first(self):
        first, _ = build_scene()
        names = [obj.name for obj in self.plugin.Helper.iter_hierarchy(first)]
        self.assertEqual(names, ['A', 'B', 'C', 'D', 'E'])

    def test_iter_hierarchy_empty_scene(self):
        self.assertEqual(list(self.plugin.Helper.iter_hierarchy(None)), [])

    def test_iter_target_objects_uses_selection(self):
        first, e = build_scene()
        doc = FakeDocument(first, selection=[e])
        self.assertEqual(list(self.plugin.Helper.iter_target_objects(doc)), [e])

    def test_iter_target_objects_without_selection_returns_all(self):
        first, _ = build_scene()
        doc = FakeDocument(first)
        self.assertEqual(len(list(self.plugin.Helper.iter_target_objects(doc))), 5)


class SettingsTest(unittest.TestCase):

    def test_defaults_when_no_saved_settings(self):
        plugin, _ = load_plugin(world_plugin_data=None)
        settings = plugin.Settings.get()
        self.assertEqual(len(settings), 2 * plugin.Helper.MATERIAL_CHANNELS_COUNT)
        self.assertEqual(settings[:2], [True, True])
        self.assertFalse(any(settings[2:]))

    def test_loads_saved_settings(self):
        class Container(object):
            def GetBool(self, index, default):
                return index == 4

        plugin, _ = load_plugin(world_plugin_data=Container())
        settings = plugin.Settings.get()
        self.assertEqual([index for index, value in enumerate(settings) if value], [4])


class DialogIdsTest(unittest.TestCase):

    def setUp(self):
        plugin, _ = load_plugin()
        self.dialog = plugin.RcConvertSettingsGUI

    def test_only_active_checkboxes_map_to_a_channel(self):
        get_index = self.dialog.get_channel_index_from_active_checkbox
        self.assertIsNone(get_index(self.dialog.ID_BTN_SAVE))
        self.assertEqual(get_index(3000), 0)
        self.assertIsNone(get_index(3001))
        self.assertEqual(get_index(3022), 11)
        self.assertIsNone(get_index(3024))

    def test_checkbox_ids(self):
        self.assertEqual(self.dialog.get_active_checkbox_id(1), 3002)
        self.assertEqual(self.dialog.get_apply_checkbox_id(1), 3003)


if __name__ == '__main__':
    unittest.main()
