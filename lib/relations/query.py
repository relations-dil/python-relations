"""
Module for Query objects
"""

import copy

import relations.sql

class Query:
    """
    Query objects for creating queries
    """

    def __init__(
        self,
        selects=None,
        froms=None,
        wheres=None,
        group_bys=None,
        havings=None,
        order_bys=None,
        limits=None,
        options=None
    ):

        self.selects = relations.sql.as_clause(selects)
        self.froms = relations.sql.as_clause(froms)
        self.wheres = relations.sql.equals_clause(wheres)
        self.group_bys = relations.sql.comma_clause(group_bys)
        self.havings = relations.sql.equals_clause(havings)
        self.order_bys = relations.sql.comma_clause(order_bys)
        self.limits = relations.sql.comma_clause(limits)
        self.options = relations.sql.options_clause(options)

    def add(
        self,
        selects=None,
        froms=None,
        wheres=None,
        group_bys=None,
        havings=None,
        order_bys=None,
        limits=None,
        options=None
    ):
        """
        Adds clauses to the query
        """

        self.selects = relations.sql.as_clause_add(self.selects, selects)
        self.froms = relations.sql.as_clause_add(self.froms, froms)
        self.wheres = relations.sql.equals_clause_add(self.wheres, wheres)
        self.group_bys = relations.sql.comma_clause_add(self.group_bys, group_bys)
        self.havings = relations.sql.equals_clause_add(self.havings, havings)
        self.order_bys = relations.sql.comma_clause_add(self.order_bys, order_bys)
        self.limits = relations.sql.comma_clause_add(self.limits, limits)
        self.options = relations.sql.options_clause_add(self.options, options)

    def set(
        self,
        selects=None,
        froms=None,
        wheres=None,
        group_bys=None,
        havings=None,
        order_bys=None,
        limits=None,
        options=None
    ):
        """
        Sets clauses on the query
        """

        self.selects = relations.sql.as_clause_set(self.selects, selects)
        self.froms = relations.sql.as_clause_set(self.froms, froms)
        self.wheres = relations.sql.equals_clause_set(self.wheres, wheres)
        self.group_bys = relations.sql.comma_clause_set(self.group_bys, group_bys)
        self.havings = relations.sql.equals_clause_set(self.havings, havings)
        self.order_bys = relations.sql.comma_clause_set(self.order_bys, order_bys)
        self.limits = relations.sql.comma_clause_set(self.limits, limits)
        self.options = relations.sql.options_clause_set(self.options, options)

    def get(self):
        """
        Converts to a string
        """

        clauses = []

        if self.selects:

            clauses.append("SELECT")

            if self.options:
                clauses.append(self.options)

            clauses.append(self.selects)

        if self.froms:
            clauses.append(f"FROM {self.froms}")

        if self.wheres:
            clauses.append(f"WHERE {self.wheres}")

        if self.group_bys:
            clauses.append(f"GROUP BY {self.group_bys}")

        if self.havings:
            clauses.append(f"HAVING {self.havings}")

        if self.order_bys:
            clauses.append(f"ORDER BY {self.order_bys}")

        if self.limits:
            clauses.append(f"LIMIT {self.limits}")

        return " ".join(clauses)

    def get_add(self, *args, **kwargs):
        """
        Adds clauses to the query and returns the string with changing the original query
        """

        query = copy.deepcopy(self)

        query.add(*args, **kwargs)

        return query.get()

    def get_set(self, *args, **kwargs):
        """
        Sets clauses on the query and returns the string with changing the original query
        """

        query = copy.deepcopy(self)

        query.set(*args, **kwargs)

        return query.get()


def get(query):
    """
    Converts a dict, query, or string to query string
    """

    if isinstance(query, str):
        return query

    if isinstance(query, dict):
        query = Query(**query)

    return query.get()
