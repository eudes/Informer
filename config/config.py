import time
from itertools import chain
from configobj import ConfigObj
from validate import Validator

from config import PluginManager
from project import Project


def load_config(config_file_path):
    """
    Compone una configuración a partir de las configspecs base y específicas de las secciones
    incluídas en el archivo de configuración, asignando valores por defecto y validándolas
    """
    configspecs_folder = "configspecs/"

    if not config_file_path:
        raise Exception;

    with open(configspecs_folder + "base.ini") as configspec:
        config = ConfigObj(config_file_path, configspec=configspec, interpolation="Template")

    for section in set(chain(config.sections, config['plugins'])):
        try:
            with open(configspecs_folder + section + ".ini") as section_conf:
                if config.get(section):
                    config[section].configspec = ConfigObj(configspec=section_conf, interpolation="Template").configspec
                else:
                    config[section] = ConfigObj(configspec=section_conf, interpolation="Template")
        except FileNotFoundError:
            continue

    validator = Validator()
    config.validate(validator)

    return Config(config)


class MalformedConfigError(Exception):
    pass


class Config(ConfigObj):
    """
    Configuración base cargada del archivo de configuración
    """

    output_filename = "informe_" + time.strftime("%Y%m%d-%H%M%S")

    def __init__(self, configobj):
        """
        Setea los valores globales de la configuración como propiedades.
        Las configuraciones de los plugins serán accesibles como parte
        del diccionario de la clase
        """

        super().__init__(configobj)
        self._config = configobj
        self.projects = []
        self.output_folder = self._config['output_folder']
        self.last_report = self._config['last_report']

        # Mediante el PluginManager se cargan dinámicamente las clases de los plugins
        plugin_manager = PluginManager()

        for index, project in enumerate(self._config['projects'].iteritems()):
            project_obj = Project(name=project[0], folder=project[1]['folder'])

            # Los plugins se cargan y se ejecutarán en el orden especificado en
            # la lista de la config
            project_obj.plugins = [plugin_manager.get_plugin(plugin_name.lower())(self)
                                   for plugin_name in self._config['plugins']]

            self.projects.append(project_obj)

    def save_config(self, result_report_path):
        """
        Añade la ubicación del último informe y guarda el archivo de configuración
        """
        self._config['last_report'] = result_report_path
        self._config.write()
