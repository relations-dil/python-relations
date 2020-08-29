"""
Module for general SQL functionality
"""


def delimit_clause(clause, major, minor, reverse=False):
    """
    Base method for building clauses
    """

    if isinstance(clause, dict):
        clause = [(f"{clause[key]}{minor}{key}" if reverse else f"{key}{minor}{clause[key]}") for key in sorted(clause.keys())]

    if isinstance(clause, list):
        clause = major.join([str(piece) for piece in clause])

    return clause


def as_clause(values):
    """
    Builds SELECT or FROM clauses
    """

    return delimit_clause(values, ',', ' AS ', True) if values else ''


def equals_clause(values):
    """
    Builds WHERE or HAVING clause
    """

    return delimit_clause(values, ' AND ', '=') if values else ''


def comma_clause(values):
    """
    Builds GROUP BY or ORDER BY clause
    """

    return delimit_clause(values, ',', ',') if values else ''


def assign_clause(values):
    """
    Builds SET clause
    """

    return delimit_clause(values, ',', '=') if values else ''


def options_clause(values):
    """
    Builds options in SELECT clause
    """

    return delimit_clause(values, ' ', ' ') if values else ''


def values_clause(clause):
    """
    Builds VALUES clause for inserting
    """

    if isinstance(clause, dict):
        clause = [clause]

    if isinstance(clause, list):

        fields = sorted(clause[0].keys())

        values = [f"({','.join([str(row[field]) for field in fields])})" for row in clause]

        clause = f"({','.join(fields)}) VALUES {','.join(values)}"

    return clause


def as_clause_add(clause, values):
    """
    Adds to an as clause
    """

    if not values:
        return clause

    values = as_clause(values)

    if clause:
        return f"{clause},{values}"

    return values


def equals_clause_add(clause, values):
    """
    Adds to an equals clause
    """

    if not values:
        return clause

    values = equals_clause(values)

    if clause:
        return f"{clause} AND {values}"

    return values


def comma_clause_add(clause, values):
    """
    Adds to an comma clause
    """

    if not values:
        return clause

    values = comma_clause(values)

    if clause:
        return f"{clause},{values}"

    return values


def assign_clause_add(clause, values):
    """
    Adds to an assign clause
    """

    if not values:
        return clause

    values = assign_clause(values)

    if clause:
        return f"{clause},{values}"

    return values


def options_clause_add(clause, values):
    """
    Adds to an options clause
    """

    if not values:
        return clause

    values = options_clause(values)

    if clause:
        return f"{clause} {values}"

    return values


def as_clause_set(clause, values):
    """
    Sets an as clause
    """

    if not values:
        return clause

    return as_clause(values)


def equals_clause_set(clause, values):
    """
    Sets an equals clause
    """

    if not values:
        return clause

    return equals_clause(values)


def comma_clause_set(clause, values):
    """
    Sets an comma clause
    """

    if not values:
        return clause

    return comma_clause(values)


def assign_clause_set(clause, values):
    """
    Sets an assign clause
    """

    if not values:
        return clause

    return assign_clause(values)


def options_clause_set(clause, values):
    """
    Sets an options clause
    """

    if not values:
        return clause

    return options_clause(values)


def ensure_list(value, split=','):
    """
    Ensures value is a list, splitting if necessary
    """

    if isinstance(value, list):
        return value

    if value:
        return value.split(split)

    return []


def ensure_dict(value, split=','):
    """
    Ensures value is a dict, splitting/comprehending if necessary
    """

    if isinstance(value, dict):
        return value

    return {key: True for key in ensure_list(value, split)}
