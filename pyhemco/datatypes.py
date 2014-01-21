# -*- coding: utf-8 -*-

# parts of pygchem (Python interface for GEOS-Chem Chemistry Transport Model)
#
# Copyright (C) 2013 Benoît Bovy
# see license.txt for more details
# 

"""
Misc classes for generic data structures.

"""


class ObjectCollection(object):
    """
    An ordered collection of unique objects that all belong to a same class.
    
    It is possible to select one or more objects in the collection
    using their attributes. It is also easy to remove, replace or
    duplicate selected objects. Callbacks can be set for adding/removing
    objects to/from the collection.
    
    This class may be useful for nested data structures (a collection may
    contain itself other collections).
    
    Parameters
    ----------
    objects : iterable
        Objects to append to the list. All items in the iterable must be
        objects of a same class.
    callbacks : (callable or None, callable or None)
        Functions called when an object is (added to, removed from) the
        collection. Each function must accepts one argument that must be any
        instance of class `ref_class`.
    read_only : bool
        If True, collection is read-only (will raise an exception when calling
        :meth:`add`, :meth:`remove` or :meth:`duplicate` methods).
    ref_class : class or None
        Specify explicitly the class expected for objects added to the
        collection (if None, the class will be determined from the first item
        found in `objects`).
    
    Notes
    -----
    Instances of this class have some similarities with Python lists
    (e.g., the ordered sequence is iterable, collection items can be accessed
    using their index...), but they are not lists.
    
    An object cannot be inserted more than once in a collection.
    """

    def __init__(self, objects=[], callbacks=(None, None),
                 read_only=False, ref_class=None):

        self._ref_class = ref_class
        self._list = []
        self._callback_add, self._callback_remove = callbacks
        self._ref_collection = None
        self._read_only = False

        for obj in objects:
            self.add(obj)

        self._read_only = read_only

    @property
    def ref_collection(self):
        """
        A 'reference' collection, i.e., another :class:`ObjectCollection`
        instance from which this collection is derived, as returned by
        :meth:`filter`, :meth:`get` or :meth:`sort` (or None if no reference
        collection exists for this collection).
        
        Using :meth:`replace`, :meth:`duplicate` or :meth:`remove` with
        this collection will affect the reference collection only !
        """
        return self._ref_collection

    def _create_subcollection(self, sel_objects):
        """
        Create a new collection of (selected) objects from this collection
        and set the correct reference collection.
        """
        cls = self.__class__
        selection = cls(objects=sel_objects)
        if self._ref_collection is None:
            selection._ref_collection = self
        else:
            selection._ref_collection = self._ref_collection
        return selection

    def _get_ref_collection_or_error(self, get=False):
        if self._ref_collection is None:
            raise TypeError("Invalid collection: the collection must be "
                            "returned by the 'filter' or 'get' method")
        elif get and len(self._list) != 1:
            raise TypeError("Invalid collection: the collection must be "
                            "returned by the 'get' method")
        return self._ref_collection

    def _check_read_only(self):
        if self._read_only:
            # TODO: raise a custom Exception
            raise ValueError("Operation not permitted on "
                             "read-only collections")

    def add(self, obj, index=-1):
        """
        Add a new object to the collection.
        
        Parameters
        ----------
        obj : object
            the object to add.
        index : int
            insert `obj` at this index (if index = -1, `obj` will be appended
            to the end of the collection).
        
        Raises
        ------
        TypeError
            If `obj` is not an object of the same class than all other objects
            of the collection.
        ValueError
            If `obj` is already in the collection.
        """
        if self._ref_class is None:
            self._ref_class = obj.__class__
        self._check_read_only()
        if not isinstance(obj, self._ref_class):
            raise TypeError("Cannot add object of class '{0}' in a "
                            "collection of only '{1}' objects"
                            .format(type(obj).__name__,
                                    self._ref_class.__name__))
        if obj in self._list:
            raise ValueError("Not allowed to add an object which is already "
                             "in the collection")
        if index == -1:
            self._list.append(obj)
        else:
            self._list.insert(index, obj)
        if self._callback_add is not None:
            self._callback_add(obj)

    def replace(self, new_obj):
        """
        Replace a given, selected object with
        another object `new_obj` in the reference collection.
        """
        self._check_read_only()
        ref = self._get_ref_collection_or_error(get=True)
        obj_index = self.index()[0]
        # call remove then add rather than direct replacement due to callbacks
        # and class checking.
        self.remove()
        ref.add(new_obj, index=obj_index)

    def duplicate(self, **kwargs):
        """
        Duplicate a given, selected object with changed attribute values
        in the reference collection.
        """
        self._check_read_only()
        ref = self._get_ref_collection_or_error(get=True)
        # TODO: object copy + change attributes with kwargs + call 'add' method

    def remove(self):
        """
        Remove selected objects in the reference collection.
        """
        self._check_read_only()
        ref = self._get_ref_collection_or_error()
        for obj in self._list:
            ref._list.remove(obj)
            if ref._callback_remove is not None:
                ref._callback_remove(obj)

    def index(self):
        """
        Get the indexes of selected objects in the reference collection.
        """
        ref = self._get_ref_collection_or_error()
        return [ref._list.index(obj) for obj in self._list]

    def sorted(self, key):
        """
        Sort objects in the collection.
        
        Parameters
        ----------
        key : string or callable
            Name of the attribute on which sorting is based, or a key function
            - which accepts any object in the collection as one argument - used
            to extract a comparison key from each object of the collection
            (see :func:`sorted`).
        
        Returns
        -------
        A new :class:`ObjectCollection` instance.
        
        Raises
        ------
        :err:`AttributeError` if `attr_name` doesn't exists.
        
        See Also
        --------
        :prop:`ref_collection`
        :func:`sorted`
        """
        try:
            sorted_objects = sorted(self._list, key=key)
        except TypeError:
            sorted_objects = sorted(self._list,
                                    key=lambda obj: getattr(obj, key))
        return self._create_subcollection(sorted_objects)

    def filter(self, *args, **kwargs):
        """
        Select objects in the collection based on their attributes.
        
        Parameters
        ----------
        *args : callable(s)
            Any callable(s) that accepts any object of `_ref_class` as
            argument and that returns True or False. Used to define custom
            conditions (useful for advanced filtering). 
        **kwargs : attr_name=value
            Used to define simple conditions, i.e., if the value of the
            attribute specified by 'attr_name' equals 'value'.
            
        Returns
        -------
        A new collection (:class:`ObjectCollection` instance) containing the
        selected objects.
        
        Notes
        -----
        If several args or kwargs are given, the returned selection satisfies
        all conditions (similar to the 'AND' operator).
        
        See Also
        --------
        :meth:`get`
        :meth:`get_object`
        :prop:`ref_collection`
        """
        selection = self._list
        for func in args:
            selection = filter(func, selection)
        for attr_name, attr_val in kwargs.items():
            selection = filter(lambda obj: getattr(obj, attr_name) == attr_val,
                               selection)
        return self._create_subcollection(selection)

    def get(self, *args, **kwargs):
        """
        Select one object based on its attributes.
        
        Similar to :meth:`filter` but raises error if the selection criteria
        result in other than one object.
        
        Returns
        -------
        A new collection (:class:`ObjectCollection` instance) containing
        the selected object.
        
        Raises
        ------
        `ValueError`
            if more than one object is found.
        `ValueError`
            if no object is found.
        
        See Also
        --------
        :meth:`filter`
        :meth:`get_object`
        :prop:`ref_collection`
        """
        # TODO: create specific exceptions.
        selection = self.filter(*args, **kwargs)
        if len(selection._list) > 1:
            raise ValueError("More than one object match the "
                             "selection criteria")
        elif not selection._list:
            raise ValueError("No object match the selection criteria")
        else:
            return selection

    def get_object(self, *args, **kwargs):
        """
        Select one object based on its attributes.
        
        Similar to :meth:`get` but returns the object rather than a new
        collection.
        
        See Also
        --------
        :meth:`filter`
        :meth:`get`
        """
        selection = self.get(*args, **kwargs)
        obj = selection._list[0]
        return obj

    def __setitem__(self, index, new_obj):
        # not the most efficient, but also not the preferred way to
        # replace an object in the collection.
        del_obj = self._list[index]
        self.get(lambda obj: obj == del_obj).replace(new_obj)

    def __getitem__(self, index):
        return self._list[index]

    def __delitem__(self, index):
        # not the most efficient, but also not the preferred way to
        # remove an object from the collection.
        del_obj = self._list[index]
        self.get(lambda obj: obj == del_obj).remove()

    def __len__(self):
        return len(self._list)

    def __iter__(self):
        return iter(self._list)

    def __str__(self):
        return "Collection of {0} objects{1}: {2}" \
            .format(self._ref_class.__name__,
                    ' (selection)' if self._ref_collection is not None else '',
                    '\n'.join(str(obj) for obj in self._list))

    def __repr__(self):
        return "<{0}{1}: {2}>"\
            .format(self.__class__.__name__,
                    ' (selection)' if self._ref_collection is not None else '',
                    list.__repr__(self._list))
