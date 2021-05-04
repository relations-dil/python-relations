"""
Module for Model Relations
"""

# pylint: disable=too-few-public-methods

import relations

class Relation:
    """
    Base Relation class
    """

    SAME = None

    @classmethod
    def relative_field(cls, model, relative):
        """
        Returns the name of the relative field, based on the relative name
        """

        # Check for the standard convention

        standard = f"{model.NAME}_id"

        if standard in relative._fields:
            return standard

        # Check to see if we're using the relative.ID, model.ID, model.relative_ID convention (diffent name for ID)

        model_id = model._field_name(model.ID)

        simple = f"{model.NAME}_{model_id}"

        if simple in relative._fields:
            return simple

        # Check to see if we're using the relative.relative_id, model.model_id, model.relative_id patten

        if model_id in relative._fields and (cls.SAME or model_id != relative._field_name(relative.ID)):
            return model_id

        raise relations.ModelError(model, f"cannot determine field for {model.NAME} in {relative.NAME}")

class OneTo(Relation):
    """
    Class that specific one to * relationships
    """

    Parent = None       # Model having one record
    parent_field = None # The id field of the parent to connect to the child
    parent_child = None # The name of the attribute on the parent model to reference children
    Child = None        # Model having many reocrds
    child_field = None  # The if field in the child to connect to the parent field
    child_parent = None # The name of the attribute on the child to reference the parent

    def __init__(self, Parent, Child, parent_child=None, child_parent=None, parent_field=None, child_field=None):

        self.Parent = Parent
        self.Child = Child

        parent = self.Parent.thy()
        child = self.Child.thy()

        self.parent_child = parent_child if parent_child is not None else child.NAME
        self.child_parent = child_parent if child_parent is not None else parent.NAME
        self.parent_field = parent._field_name(parent_field if parent_field is not None else parent._id)
        self.child_field = child._field_name(child_field) if child_field is not None else self.relative_field(parent, child)

        self.Parent._child(self)
        self.Child._parent(self)

class OneToMany(OneTo):
    """
    Class that specific one to many relationships
    """

    MODE = "many"
    SAME = False

class OneToOne(OneTo):
    """
    Class that specific one to one relationships
    """

    MODE = "one"
    SAME = True
