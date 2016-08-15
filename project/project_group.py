from project import Project


class ProjectGroup(Project):

    def __init__(self, _plugins=None, subprojects=None, *args, **kwargs):
        if subprojects is None: subprojects = []
        if not 'folder' in kwargs: kwargs['folder'] = None
        self._plugins = []
        if subprojects:
            self.subprojects = []
            for subproject in subprojects:
                project = Project(**subproject)
                self.subprojects.append(project)
        else:
            self.subprojects = subprojects
        super().__init__(*args, **kwargs)

    @property
    def plugins(self):
        return self._plugins

    @plugins.setter
    def plugins(self, plugin_list):
        self._plugins = plugin_list
        for project in self.subprojects:
            project.plugins = plugin_list
