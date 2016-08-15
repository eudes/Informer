class Project(object):

    def __init__(self, name, folder="", subprojects=None,
                 plugins=None, reports=None, old_reports=None,
                 error=False, error_plugins=None):

        if subprojects is None: subprojects = []
        if plugins is None: plugins = []
        if reports is None: reports = {}
        if old_reports is None: old_reports = {}
        if error_plugins is None: error_plugins = []

        self._subprojects = []
        self.subprojects = subprojects
        self._plugins = []
        self.plugins = plugins
        self.reports = reports
        self.old_reports = old_reports
        self.name = name
        self.folder = folder
        self.error = error
        self.error_plugins = error_plugins

    @property
    def subprojects(self):
        return self._subprojects

    @subprojects.setter
    def subprojects(self, subprojects):
        for project in subprojects:
            self._subprojects.append(Project(**project))

    @property
    def plugins(self):
        return self._plugins

    @plugins.setter
    def plugins(self, plugins):
        self._plugins = plugins
        for subproject in self.subprojects:
            subproject.plugins = plugins

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
