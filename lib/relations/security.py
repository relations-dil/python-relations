"""
Relations Security Module
"""

# pylint: disable=protected-access,too-few-public-methods,too-many-arguments

import contextlib
import contextvars
import copy

import overscore
import relations


class Denied(relations.ModelError):
    """
    An actor doing what no rule lets them. Never for a record they can't read, which is a miss (NotFoundError)
    """


class System:
    """
    Stands for the code itself, not an actor, so what it does isn't checked
    """


SYSTEM = System()

ACTOR = contextvars.ContextVar("relations_security_actor", default=None)
CACHE = contextvars.ContextVar("relations_security_cache", default=None)

POLICY = None  # What decides the rules for a model that doesn't have a POLICY of its own

VERBS = ["create", "count", "retrieve", "titles", "update", "delete"]


def current():
    """
    The actor in effect, None if there isn't one
    """

    return ACTOR.get()


def cache():
    """
    A dict kept for as long as the actor is acting, for a policy to keep the rules it looked up, None outside
    """

    return CACHE.get()


@contextlib.contextmanager
def acting(actor):
    """
    Everything inside is done by the actor
    """

    token = ACTOR.set(actor)
    kept = CACHE.set({})

    try:
        yield actor
    finally:
        CACHE.reset(kept)
        ACTOR.reset(token)


def system():
    """
    Everything inside is done by the code itself, which is how a policy reads its own rules
    """

    return acting(SYSTEM)


class Rule:
    """
    What an actor may do with a verb on a model. Everything but check can be a function of the actor

    allow  - whether the verb is allowed at all
    scope  - filter kwargs for the records it applies to, read to see them, and to change or delete them
    into   - for create and update, filter kwargs the new values have to satisfy, scope if not given, and
             {} to allow any (which is what lets a record be moved out of reach)
    force  - values set on create and update, whatever was sent
    fields - the names the actor may read (retrieve) or write (create and update), all if not given
    check  - a function of the actor and a record's values, False to deny
    """

    allow = None
    scope = None
    into = None
    force = None
    fields = None
    check = None

    def __init__(self, allow=True, *, scope=None, into=None, force=None, fields=None, check=None):

        self.allow = allow
        self.scope = scope
        self.into = into
        self.force = force
        self.fields = fields
        self.check = check

    @staticmethod
    def resolve(value, actor):
        """
        The value, or what it gives for the actor if it's a function
        """

        return value(actor) if callable(value) else value


class Policy:
    """
    Decides the rule for an actor, a model and a verb, None meaning no. These come from rules, by the model's
    name (or * for any), then by the verb (or * for any), count and titles being retrieve's unless given
    their own. Override rule to get them from somewhere else
    """

    INHERIT = {
        "count": "retrieve",
        "titles": "retrieve"
    }

    rules = None

    def __init__(self, rules=None):

        self.rules = rules or {}

    def rule(self, actor, model, verb): # pylint: disable=unused-argument
        """
        The rule for the actor to do the verb on the model
        """

        for name in (model.NAME, "*"):

            verbs = self.rules.get(name) or {}

            for each in (verb, self.INHERIT.get(verb), "*"):
                if each in verbs:
                    return verbs[each]

        return None


class Secure:
    """
    Mixes into a model, in front of it (class Person(Secure, UnifistModel)), to hold every verb to the rules of
    the actor, which is whoever is acting (relations.security.acting), the POLICY of the model or of this
    module giving the rules. No actor, or no rule, is no. A record the actor can't read is a miss, one they
    can read but can't write is Denied. The checks are done in memory where they can be, and what can only
    be done by the source is added to its query
    """

    POLICY = None

    _secure_adding = False  # Whether what is being filtered is the scope's, not what the actor asks
    _secure_asked = None    # Names of the fields the actor has filtered on, apart from the scope's criteria
    _secure_hidden = None   # Names of the fields that can't be read, access raises
    _secure_sealed = False  # Whether the record can't be read any more, any access raises

    def _secure_rule(self, actor, verb, deny=True):
        """
        The rule for the verb, Denied if there isn't one that allows it, or None if not to deny
        """

        policy = self.POLICY or POLICY
        rule = policy.rule(actor, self, verb) if policy else None

        if rule is None or not Rule.resolve(rule.allow, actor):

            if deny:
                raise Denied(self, f"cannot {verb}")

            return None

        return rule

    @staticmethod
    def _secure_scope(rule, actor, name="scope"):
        """
        The filter kwargs of a rule for the actor, none being an empty dict. For into, scope if not given
        """

        value = getattr(rule, name)

        if name == "into" and value is None:
            value = rule.scope

        return dict(Rule.resolve(value, actor) or {})

    @staticmethod
    def _secure_names(rule, actor):
        """
        The names a rule gives, None being all of them
        """

        names = Rule.resolve(rule.fields, actor)

        return None if names is None else {name.split('__')[0] for name in names}

    def _secure_split(self, scope):
        """
        Splits a scope in the criteria on this model's fields and the rest, which are of relations
        """

        own = {}
        other = {}

        for name, value in scope.items():
            (own if name.split('__')[0] in self._fields._names else other)[name] = value

        return own, other

    @staticmethod
    def _secure_stored(record, old=False):
        """
        The values of a record as the source keeps them, from before the changes if old
        """

        names = record._record._names
        values = {}
        injected = []

        for field in record._record._order:
            if field.inject:
                injected.append(field)
            else:
                values[field.store] = copy.deepcopy(field.original) if old else field.export()

        for field in injected:
            store = names[field.inject.split('__')[0]].store
            values[store] = values.get(store) or {}
            overscore.set(values[store], field.inject.split('__', 1)[-1], copy.deepcopy(field.original) if old else field.export())

        return values

    def _secure_scoped(self, own):
        """
        A copy of the fields holding the criteria of a scope
        """

        scoped = copy.deepcopy(self._fields)

        for name, value in own.items():
            scoped.filter(name, value)

        return scoped

    def _secure_holds(self, scope, record, state):
        """
        Whether a record satisfies a scope. In memory for criteria on this model's own fields, with the values
        from before the changes if the state is old, or after if new or now. What is on relations can only be
        asked of the source, so only of what is there to ask, old or now
        """

        own, other = self._secure_split(scope)

        if own and not self._secure_scoped(own).retrieve(self._secure_stored(record, state == "old")):
            return False

        if other:

            if state == "new" or self._id is None:
                raise relations.ModelError(self, f"scope {list(other)} needs the source, so a check on the rule")

            return self.__class__.many(**{self._id: record[self._id]}, **other).count() > 0

        return True

    def secure(self, **scope):
        """
        Narrows the query by the scope as the model does, but what is added isn't taken for what the actor asks.
        What can't be put together with what is there is a Denied
        """

        self._secure_adding = True

        try:
            return super().secure(**scope) # pylint: disable=no-member
        except relations.FieldError as exception:
            raise Denied(self, str(exception)) from exception
        finally:
            self._secure_adding = False

    def filter(self, *args, **kwargs):
        """
        What the actor filters on is kept apart from the scope's criteria, which are added the same but not through
        here, because it's checked differently. Checked now if the actor is known, and again before the source
        """

        if self._secure_adding:
            return super().filter(*args, **kwargs) # pylint: disable=no-member

        asked = {
            self._fields._order[index].name for index in range(len(args)) if index < len(self._fields)
        } | {
            name.split('__')[0] for name in kwargs if name.split('__')[0] in self._fields._names
        }

        self._secure_asked = (self._secure_asked or set()) | asked

        actor = current()
        read = self._secure_rule(actor, "retrieve", deny=False) if actor not in (None, SYSTEM) else None

        if read:
            self._secure_criteria(read, actor, asked)

        return super().filter(*args, **kwargs) # pylint: disable=no-member

    def _secure_criteria(self, rule, actor, asked=None):
        """
        Holds what is filtered, sorted and searched on to the names the actor can read, or it's a way to find
        out what they can't. Only what was asked, not the scope's criteria. Just the filtering if asked is given
        """

        names = self._secure_names(rule, actor)

        if names is None:
            return

        for name in self._secure_asked if asked is None else asked:
            if name not in names:
                raise Denied(self, f"cannot filter on {name}")

        if asked is not None:
            return

        for sort in self._sort or []:
            if sort[1:].split('__')[0] not in names:
                raise Denied(self, f"cannot sort on {sort[1:]}")

        if self._like is not None:
            for title in self._titles or []:
                if title.split('__')[0] not in names:
                    raise Denied(self, "cannot search")

    def _secure_writes(self, model, rule, actor, changed):
        """
        Holds what is written to the names the actor can write
        """

        names = self._secure_names(rule, actor)

        if names is None:
            return

        forced = Rule.resolve(rule.force, actor) or {}

        for field in model._record._order:
            if changed(field) and field.name not in names and field.name not in forced:
                raise Denied(self, f"cannot write {field.name}")

    @staticmethod
    def _secure_started(field):
        """
        Whether a new record's field has more than its default
        """

        default = field.default() if callable(field.default) else field.default

        return field.value != (field.valid(default) if default is not None else None)

    def _secure_create(self, rule, actor):
        """
        Forces values, then holds what's written and the new values to the rule
        """

        forced = Rule.resolve(rule.force, actor) or {}
        into = self._secure_scope(rule, actor, "into")

        for model in self._each("create"):

            for name, value in forced.items():
                model[name] = value

            self._secure_writes(model, rule, actor, lambda field: not field.auto and self._secure_started(field))

            if into and not self._secure_holds(into, model, "new"):
                raise Denied(self, f"cannot create that {self.NAME}")

            if rule.check and not rule.check(actor, model.export()):
                raise Denied(self, f"cannot create that {self.NAME}")

    def _secure_change(self, action, rule, actor):
        """
        For each record loaded, a miss if it can't be read, Denied if it can't be changed or isn't allowed to
        become what it's being changed to
        """

        if self._action == "retrieve":
            return  # By a query, narrowed in update and delete

        read = self._secure_rule(actor, "retrieve", deny=False)
        readable = self._secure_scope(read, actor) if read else None
        scope = self._secure_scope(rule, actor)
        into = self._secure_scope(rule, actor, "into")
        forced = Rule.resolve(rule.force, actor) or {}

        for model in self._each("update"):

            if read is None or not self._secure_holds(readable, model, "old"):
                raise relations.NotFoundError(model, "none retrieved")

            if action == "update":
                for name, value in forced.items():
                    model[name] = value
                self._secure_writes(model, rule, actor, lambda field: field.delta())

            if scope and not self._secure_holds(scope, model, "old"):
                raise Denied(self, f"cannot {action} that {self.NAME}")

            if action == "update" and into and not self._secure_holds(into, model, "new"):
                raise Denied(self, f"cannot {action} that {self.NAME} to that")

            if rule.check and not rule.check(actor, model.export()):
                raise Denied(self, f"cannot {action} that {self.NAME}")

    def pre(self, action, *args, **kwargs):
        """
        Holds the verb to the actor's rule, then does what the rest of the model does
        """

        actor = current()

        if actor is not SYSTEM:

            if actor is None:
                raise Denied(self, f"cannot {action} without an actor")

            rule = self._secure_rule(actor, action)

            if action in ("retrieve", "count", "titles"):

                if self._action == "retrieve":
                    self._secure_criteria(rule, actor)
                    self.secure(**self._secure_scope(rule, actor))

            elif action == "create":
                self._secure_create(rule, actor)

            else:
                self._secure_change(action, rule, actor)

        super().pre(action, *args, **kwargs) # pylint: disable=no-member

    @contextlib.contextmanager
    def _secure_unguarded(self):
        """
        Lets the rest of the model, and the source, which have to read ids and versions, at the records, whatever
        the actor can read
        """

        guarded = [(model, model._secure_hidden, model._secure_sealed) for model in self._each()]

        for model, _, _ in guarded:
            model._secure_hidden = None
            model._secure_sealed = False

        try:
            yield
        finally:
            for model, hidden, sealed in guarded:
                model._secure_hidden = hidden
                model._secure_sealed = sealed

    def _hook(self, action, *args, **kwargs):
        """
        Runs pre, the source action and post with every record open, because they have to read ids and versions
        whatever the actor can read, then guards them
        """

        with self._secure_unguarded():
            result = super()._hook(action, *args, **kwargs) # pylint: disable=no-member

        return self._secure_guard(action, result)

    def _secure_guard(self, action, result):
        """
        Hides what the actor can't read, and seals what is no longer theirs to, which is why a record that was
        moved out of reach can't be read after
        """

        actor = current()

        if actor is SYSTEM or actor is None or action not in ("create", "retrieve", "update") or self._action == "retrieve":
            return result

        read = self._secure_rule(actor, "retrieve", deny=False)
        names = self._secure_names(read, actor) if read else None
        readable = self._secure_scope(read, actor) if read else None

        for model in self._each():

            if read is None or (action != "retrieve" and readable and not self._secure_holds(readable, model, "now")):
                model._secure_sealed = True
            elif names is not None:
                model._secure_hidden = set(self._fields._names) - names

        return result

    def _secure_bulk(self, action):
        """
        For a change by a query, narrows it to what can be read and changed, and holds what is set to the
        names that can be written, and to what the values have to be
        """

        actor = current()

        if actor is SYSTEM or self._action != "retrieve" or self._mode != "many":
            return

        if actor is None:
            raise Denied(self, f"cannot {action} without an actor")

        rule = self._secure_rule(actor, action)
        read = self._secure_rule(actor, "retrieve", deny=False)

        if read is None:
            self._nothing()
            return

        self._secure_criteria(read, actor)
        self.secure(**self._secure_scope(read, actor))
        self.secure(**self._secure_scope(rule, actor))

        if action != "update":
            return

        for name, value in (Rule.resolve(rule.force, actor) or {}).items():
            self._record[name] = value
            self._record._action = "update"

        self._secure_writes(self, rule, actor, lambda field: field.changed)

        into, other = self._secure_split(self._secure_scope(rule, actor, "into"))

        if other:
            raise relations.ModelError(self, f"scope {list(other)} needs the source, so a check on the rule")

        if into:

            scoped = self._secure_scoped(into)

            for field in scoped._order:
                if not self._record._names[field.name].changed:
                    field.criteria = None

            if not scoped.retrieve({field.store: field.export() for field in self._record._order if field.changed}):
                raise Denied(self, f"cannot {action} {self.NAME} to that")

    def update(self, *args, **kwargs):
        """
        Narrows a change by a query before doing it
        """

        self._secure_bulk("update")

        return super().update(*args, **kwargs) # pylint: disable=no-member

    def delete(self, *args, **kwargs):
        """
        Narrows a delete by a query before doing it
        """

        self._secure_bulk("delete")

        return super().delete(*args, **kwargs) # pylint: disable=no-member

    def _secure_access(self, key):
        """
        Raises if the record is sealed or the field is hidden
        """

        if self._secure_sealed:
            raise Denied(self, "no longer yours to read")

        if isinstance(key, int):
            key = self._fields._order[key].name if self._mode == "one" and key < len(self._fields) else None

        if isinstance(key, str) and key.split('__')[0] in (self._secure_hidden or []):
            raise Denied(self, f"cannot read {key.split('__')[0]}")

    def __getattribute__(self, name):
        """
        Guards the fields
        """

        if name[0] != '_' and name == name.lower() and (
            object.__getattribute__(self, '_secure_sealed') or object.__getattribute__(self, '_secure_hidden')
        ) and name.split('__')[0] in (object.__getattribute__(self, '_fields') or []):
            self._secure_access(name)

        return super().__getattribute__(name)

    def __getitem__(self, key):
        """
        Guards the fields
        """

        self._secure_access(key)

        return super().__getitem__(key) # pylint: disable=no-member

    def export(self):
        """
        Leaves out the fields that can't be read, and raises if none can
        """

        if self._secure_sealed:
            raise Denied(self, "no longer yours to read")

        exported = super().export() # pylint: disable=no-member

        if self._secure_hidden and isinstance(exported, dict):
            return {name: value for name, value in exported.items() if name not in self._secure_hidden} # pylint: disable=unsupported-membership-test

        return exported
