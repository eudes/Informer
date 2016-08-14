from .base_plugin import BasePlugin
from utils import format_path


class Svn(BasePlugin):
    makes_report = False

    def __init__(self, config):
        super().__init__(config)
        self.svn_config = config['svn']

    def get_build_command(self, project_folder):
        base_command = "svn"
        result_command = ""

        project_folder = format_path(project_folder)

        if self.svn_config.get('revert'):
            result_command += base_command + " revert -R " + project_folder + "; "

        params = []
        if self.svn_config.get('force_update'):
            params.append('update --force')
        elif self.svn_config.get('update'):
            params.append('update')

        result_command += " ".join([base_command, *params, project_folder])
        return result_command


