import time


class Project(object):

    def __init__(self, name, folder="", subprojects=None,
                 plugins=None, reports=None, old_reports=None,
                 error=False, error_plugins=None, _subprojects = None, _plugins = None, date = None):

        if subprojects is None: subprojects = _subprojects
        if subprojects is None: subprojects = []
        if plugins is None: plugins = _plugins
        if plugins is None: plugins = []
        if _subprojects is None: _subprojects = []
        if _plugins is None: _plugins = []
        if reports is None: reports = {}
        if old_reports is None: old_reports = {}
        if error_plugins is None: error_plugins = []
        if date is None: date = time.strftime("%d/%m/%Y, %H:%M:%S")

        self._subprojects = subprojects or _subprojects
        self._plugins = plugins or _plugins
        self.reports = reports
        self.old_reports = old_reports
        self.name = name
        self.folder = folder
        self.error = error
        self.error_plugins = error_plugins
        self.date = date

    @property
    def subprojects(self):
        try:
            return self._subprojects
        except:
            return None

    @subprojects.setter
    def subprojects(self, subprojects):
        for project in subprojects:
            if isinstance(project, Project):
                project_instance = project
            else:
                project_instance = Project(**project)
            self._subprojects.append(project_instance)

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
