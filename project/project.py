class Project:

    def __init__(self, name, folder, plugins=[], reports={}, old_reports={}, error=False, error_plugins=[]):
        self.name = name
        self.folder = folder
        self.plugins = plugins
        self.reports = reports
        self.old_reports = old_reports
        self.error = error
        self.error_plugins = error_plugins

    def handle_plugin_error(self, plugin):
        """
        Añade el error a la lista de errores y marca el projecto como fallido
        """
        self.error = True
        self.error_plugins.append(plugin.__class__.__name__)

    def json_encode(self):
        return self.__dict__

    def __repr__(self):
        return str(self.__dict__)
