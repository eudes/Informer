from project import Project


class ProjectGroup(Project):

    def __init__(self, *args, **kwargs):
        self.subprojects = []
        self._plugins = []
        super().__init__(*args, folder=None, **kwargs)

    @property
    def plugins(self):
        return self._plugins

    @plugins.setter
    def plugins(self, plugin_list):
        self._plugins = plugin_list
        for project in self.subprojects:
            project.plugins = plugin_list
