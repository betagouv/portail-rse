class MetabaseRouter:
    def _route_from_model(self, model):
        return self._route_from_app_label(model._meta.app_label)

    def _route_from_app_label(self, app_label):
        if app_label == "metabase":
            return "metabase"

    def db_for_read(self, model, **hints):
        return self._route_from_model(model)

    def db_for_write(self, model, **hints):
        return self._route_from_model(model)

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return self._route_from_app_label(app_label)
