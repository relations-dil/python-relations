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


class ManyToMany(Relation):
    """
    Class that specific many to many relationships
    """

    Sister = None         # Model having fewer records
    sister_field = None   # The field of the sister to connect to the brother
    sister_brother = None # The name of the attribute on the sister model to reference brotherren
    Brother = None        # Model having more reocrds
    brother_field = None  # The id field in the brother to connect to the sister
    brother_sister = None # The name of the attribute on the brother to reference the sister
    Tie = None            # Model of the Tie table
    tie_sister = None     # The id field of the sister in the tie table
    tie_brother = None    # The id field of the brother in the tie table

    def __init__(
            self,
            Sister,
            Brother,
            Tie,
            sister_brother=None,
            brother_sister=None,
            sister_field=None,
            brother_field=None,
            tie_sister=None,
            tie_brother=None
        ):

        self.Sister = Sister
        self.Brother = Brother
        self.Tie = Tie

        if self.Tie.TIE is None:
            self.Tie.TIE = True

        sister = self.Sister.thy()
        brother = self.Brother.thy()
        tie = self.Tie.thy()

        self.sister_brother = sister._field_name(sister_brother if sister_brother is not None else self.relative_field(brother, sister))
        self.brother_sister = brother._field_name(brother_sister) if brother_sister is not None else self.relative_field(sister, brother)
        self.sister_field = sister._field_name(sister_field if sister_field is not None else sister._id)
        self.brother_field = brother._field_name(brother_field if brother_field is not None else brother._id)
        self.tie_sister = tie._field_name(tie_sister if tie_sister is not None else self.relative_field(sister, tie))
        self.tie_brother = tie._field_name(tie_brother if tie_brother is not None else self.relative_field(brother, tie))

        self.Sister._brother(self)
        self.Brother._sister(self)
