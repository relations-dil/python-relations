import flask
import flask_restful

import functools
import traceback
import werkzeug.exceptions

def exceptions(endpoint):
    """
    Decorator that adds and handles a database session
    """

    @functools.wraps(endpoint)
    def wrap(*args, **kwargs):

        try:

            response = endpoint(*args, **kwargs)

        except werkzeug.exceptions.BadRequest as exception:

            response = {
                "message": exception.description
            }, 400

        except Exception as exception:

            response = {
                "message": str(exception),
                "traceback": traceback.format_exc()
            }, 500

        return response

    return wrap

class Resource(flask_restful.Resource):
    """
    Base Model class for Relations Restful classes
    """

    MODEL = None
    SINGULAR = None
    PLURAL = None

    model = None

    def __init__(self, *args, **kwargs):

        super(Resource).__init__(*args, **kwargs)

        self.model = self.MODEL._thyself()

        if self.SINGULAR is None:
            if hasattr(self.model, "SINGULAR") and self.model.SINGULAR is not None:
                self.SINGULAR = self.model.SINGULAR
            else:
                self.SINGULAR = self.model.NAME

        if self.PLURAL is None:
            if hasattr(self.model, "PLURAL") and self.model.PLURAL is not None:
                self.PLURAL = self.model.PLURAL
            else:
                self.PLURAL = f"{self.SINGULAR}s"

    @staticmethod
    def criteria(verify=False):
        """
        Gets criteria from the flask request
        """

        if verify and not flask.request.args and "filter" not in (flask.request.json or {}):
            raise werkzeug.exceptions.BadRequest("to confirm all, send a blank filter {}")

        criteria = {}

        if flask.request.args:
            criteria.update(flask.request.args.to_dict())

        if flask.request.json is not None and "filter" in flask.request.json:
            criteria.update(flask.request.json["filter"])

        return criteria

    @exceptions
    def post(self):
        """
        Creates one or more models
        """

        if self.SINGULAR not in (flask.request.json or {}) and self.PLURAL not in (flask.request.json or {}):
            raise werkzeug.exceptions.BadRequest(f"either {self.SINGULAR} or {self.PLURAL} required")

        if self.SINGULAR in flask.request.json:

            return {self.SINGULAR: dict(self.MODEL(**flask.request.json[self.SINGULAR]).create())}, 201

        if self.PLURAL in flask.request.json:

            return {self.PLURAL: [dict(model) for model in self.MODEL(flask.request.json[self.PLURAL]).create()]}, 201

    @exceptions
    def get(self, id=None):
        """
        Retrieves one or more models
        """

        if id is not None:
            return {self.SINGULAR: dict(self.MODEL.one(**{self.model._id: id}))}, 200

        return {self.PLURAL: [dict(model) for model in self.MODEL.many(**self.criteria())]}, 200

    @exceptions
    def patch(self, id=None):
        """
        Updates models
        """

        if self.SINGULAR not in (flask.request.json or {}) and self.PLURAL not in (flask.request.json or {}):
            raise werkzeug.exceptions.BadRequest(f"either {self.SINGULAR} or {self.PLURAL} required")

        if id is not None:

            model = self.MODEL.one(**{self.model._id: id}).set(**flask.request.json[self.SINGULAR])

        elif self.SINGULAR in flask.request.json:

            model = self.MODEL.one(**self.criteria(True)).set(**flask.request.json[self.SINGULAR])

        elif self.PLURAL in flask.request.json:

            model = self.MODEL.many(**self.criteria(True)).set(**flask.request.json[self.PLURAL])

        return {"updated": model.update()}, 202

    @exceptions
    def delete(self, id=None):
        """
        Deletes models
        """

        if id is not None:

            model = self.MODEL.one(**{self.model._id: id})

        else:

            model = self.MODEL.many(**self.criteria(True))

        return {"deleted": model.delete()}, 202
