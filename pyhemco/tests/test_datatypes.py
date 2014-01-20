
import unittest
from collections import namedtuple

from pyhemco.datatypes import ObjectCollection


class TestObjectCollection(unittest.TestCase):

    def setUp(self):
        """Using namedtuple for tests."""
        self.MyObject = namedtuple("MyObject", ['x', 'y', 'z'])

        self.obj1 = self.MyObject(x=1, y=1.0, z='1')
        self.obj1b = self.MyObject(x=1, y=1.0, z='1')
        self.obj2 = self.MyObject(x=2, y=2.0, z='2')
        self.obj3 = self.MyObject(x=3, y=3.0, z='3')
        self.obj4 = self.MyObject(x=4, y=4.0, z='4')

        self.obj_list1 = [self.obj1, self.obj2, self.obj3]
        self.obj_list2 = [self.obj1, self.obj1b]
        self.obj_list3 = [self.obj1, 'a string']

    def test_add(self):
        with self.assertRaises(ValueError):
            ObjectCollection(self.obj_list2)
        with self.assertRaises(TypeError):
            ObjectCollection(self.obj_list3)
        col = ObjectCollection(self.obj_list1)
        col.add(self.obj4, index=1)
        self.assertEqual(col._list,
                         [self.obj1, self.obj4, self.obj2, self.obj3])

    def test_filter(self):
        col = ObjectCollection(self.obj_list1)
        self.assertEqual(col.filter(x=1, z='1')._list,
                         [self.obj1])
        self.assertEqual(col.filter(lambda obj: obj.y > 1.0)._list,
                         [self.obj2, self.obj3])

    def test_get(self):
        col = ObjectCollection(self.obj_list1)
        with self.assertRaises(ValueError):
            col.get(lambda obj: obj.y > 1.0)
            col.get(x=5)
        self.assertEqual(col.get(x=1, y=1.0, z='1')._list,
                         [self.obj1])

    def test_get_object(self):
        col = ObjectCollection(self.obj_list1)
        self.assertIsInstance(col.get_object(x=1, y=1.0, z='1'),
                              self.MyObject)

    def test_remove(self):
        col = ObjectCollection(self.obj_list1)
        col.get(x=1, y=1.0, z='1').remove()
        self.assertEqual(col._list,
                         [self.obj2, self.obj3])
        del col[1]
        self.assertEqual(col._list,
                         [self.obj2])

    def test_replace(self):
        col = ObjectCollection(self.obj_list1)
        col.get(x=1, y=1.0, z='1').replace(self.obj4)
        self.assertEqual(col._list,
                         [self.obj4, self.obj2, self.obj3])
        col[-1] = self.obj1
        self.assertEqual(col._list,
                         [self.obj4, self.obj2, self.obj1])

    # def test_duplicate(self):
    #     self.fail()

    def test__check_read_only(self):
        col = ObjectCollection(self.obj_list1, read_only=True)
        with self.assertRaises(ValueError):
            col.get(x=1, y=1.0, z='1').remove()
            col.add(self.obj4)

    def test_index(self):
        col = ObjectCollection(self.obj_list1)
        self.assertEqual(col.filter(lambda obj: obj.y > 1.0).index(),
                         [1, 2])

    def test_sorted(self):
        col_inv = ObjectCollection([self.obj3, self.obj2, self.obj1])
        self.assertEqual(col_inv.sorted('x')._list,
                         ObjectCollection(self.obj_list1)._list)

    def tearDown(self):
        pass
