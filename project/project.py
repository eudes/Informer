class Project:

    def __init__(self, name, folder, plugins=None, reports=None, old_reports=None, error=False, error_plugins=None):
        if plugins is None: plugins = []
        if reports is None: reports = {}
        if old_reports is None: old_reports = {}
        if error_plugins is None: error_plugins = []

        self.plugins = plugins
        self.reports = reports
        self.old_reports = old_reports
        self.name = name
        self.folder = folder
        self.error = error
        self.error_plugins = error_plugins

    def handle_plugin_error(self, plugin, error_desc):
        """
        Añade el error a la lista de errores y marca el projecto como fallido
        """
        self.error = True
        self.error_plugins.append((plugin.__class__.__name__, error_desc))

    def json_encode(self):
        return self.__dict__

    def __repr__(self):
        return ", ".join([self.name, str(self.reports)])
