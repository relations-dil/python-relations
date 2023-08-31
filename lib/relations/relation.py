"""
Module for Model Relations
"""

# pylint: disable=too-few-public-methods,too-many-instance-attributes,too-many-arguments

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

    Parent = None            # Model having one record
    parent_id = None         # The id field of the parent to connect to the child
    parent_child_attr = None # The name of the attribute on the parent model to access children

    Child = None             # Model having many reocrds
    child_parent_ref = None  # The id field in the child to connect to the parent field
    child_parent_attr = None # The name of the attribute on the child to access the parent

    def __init__(
            self,
            Parent,
            Child,
            parent_child_attr=None,
            child_parent_attr=None,
            parent_id=None,
            child_parent_ref=None
        ):

        self.Parent = Parent
        self.Child = Child

        parent = self.Parent.thy()
        child = self.Child.thy()

        self.parent_id = parent._field_name(parent_id if parent_id is not None else parent._id)
        self.parent_child_attr = parent_child_attr if parent_child_attr is not None else child.NAME

        self.child_parent_attr = child_parent_attr if child_parent_attr is not None else parent.NAME
        self.child_parent_ref = child._field_name(child_parent_ref) if child_parent_ref is not None else self.relative_field(parent, child)

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

    Sister = None               # Model having fewer records
    sister_id = None            # The field of the sister to connect to the brother
    sister_brother_ref = None   # The name of the field on the sister model to reference brothers
    sister_brother_attr = None  # The name of the attribute on the sister model to access brothers

    Brother = None              # Model having more reocrds
    brother_id = None           # The id field in the brother to connect to the sister
    brother_sister_ref = None   # The name of the field on the brother to reference the sister
    brother_sister_attr = None  # The name of the attribute on the brother model to access sisters

    Tie = None                  # Model of the Tie table
    tie_sister_ref = None       # The id field of the sister in the tie table
    tie_brother_ref = None      # The id field of the brother in the tie table

    def __init__(
            self,
            Sister,
            Brother,
            Tie,
            sister_brother_attr=None,
            brother_sister_attr=None,
            sister_brother_ref=None,
            brother_sister_ref=None,
            sister_id=None,
            brother_id=None,
            tie_sister_ref=None,
            tie_brother_ref=None
        ):

        self.Sister = Sister
        self.Brother = Brother
        self.Tie = Tie

        if self.Tie.TIE is None:
            self.Tie.TIE = True

        sister = self.Sister.thy()
        brother = self.Brother.thy()
        tie = self.Tie.thy()

        self.sister_id = sister._field_name(sister_id if sister_id is not None else sister._id)
        self.sister_brother_ref = sister._field_name(sister_brother_ref) if sister_brother_ref is not None else \
                                  self.relative_field(brother, sister)
        self.sister_brother_attr = sister_brother_attr if sister_brother_attr is not None else brother.NAME

        self.brother_id = brother._field_name(brother_id if brother_id is not None else brother._id)
        self.brother_sister_ref = brother._field_name(brother_sister_ref) if brother_sister_ref is not None else \
                                  self.relative_field(sister, brother)
        self.brother_sister_attr = brother_sister_attr if brother_sister_attr is not None else sister.NAME

        self.tie_sister_ref = tie._field_name(tie_sister_ref if tie_sister_ref is not None else self.relative_field(sister, tie))
        self.tie_brother_ref = tie._field_name(tie_brother_ref if tie_brother_ref is not None else self.relative_field(brother, tie))

        self.Sister._brother(self)
        self.Brother._sister(self)
