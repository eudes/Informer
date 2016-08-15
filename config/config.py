import time
from itertools import chain
from configobj import ConfigObj
from validate import Validator

from config import PluginManager
from project import Project


class PluginConfigNotFoundError(BaseException):
    pass


def load_config(config_file_path):
    """
    Compone una configuración a partir de las configspecs base y específicas de las secciones
    incluídas en el archivo de configuración, asignando valores por defecto y validándolas
    """
    configspecs_folder = "configspecs/"

    if not config_file_path:
        raise Exception("Es necesario indicar un fichero de configuración")

    with open(configspecs_folder + "base.ini") as configspec:
        config = ConfigObj(config_file_path, configspec=configspec, interpolation="Template")

    # Por cada section y por cada plugin indicado en la config intenta cargar una plantilla
    # con el mismo nombre
    for section in set(chain(config.sections, config['plugins'])):
        try:
            with open(configspecs_folder + section + ".ini") as section_conf:
                if section in config:
                    config[section].configspec = ConfigObj(configspec=section_conf, interpolation="Template").configspec
                else:
                    # TODO: crear una nueva sección a partir de la configspec correspondiente
                    # si no se indica la sección del plugin en la config
                    # ejemplo: se añade el plugin svn a la config pero no se añade la
                    # sección [svn]
                    # config[section] = ConfigObj(configspec=section_conf, interpolation="Template")
                    print("Error al parsear la config para: %s. Probablemente no se haya añadido"
                          "la sección correspondiente al plugin" % section)
                    raise PluginConfigNotFoundError

        except FileNotFoundError:
            continue

    # Valida y setea los parámetros por defecto de la config
    validator = Validator()
    config.validate(validator)

    return Config(config)


class MalformedConfigError(Exception):
    pass


class Config(ConfigObj):
    """
    Configuración base cargada del archivo de configuración
    """

    def __init__(self, configobj):
        """
        Setea los valores globales de la configuración como propiedades.
        Las configuraciones de los plugins serán accesibles como parte
        del diccionario de la clase
        """
        super().__init__(configobj)
        self._config = configobj
        self.report_filename_prefix = self._config['report_filename_prefix']
        self.output_filename = self.report_filename_prefix + '_'+ time.strftime("%Y%m%d-%H%M%S")
        self.output_folder = self._config['output_folder']
        self.last_report = self._config['last_report']
        self.skip_commands = self._config['skip_commands']
        # Mediante el PluginManager se cargan dinámicamente las clases de los plugins
        self.plugin_manager = PluginManager()
        self.projects = self._parse_projects()

    def _parse_projects(self):
        projects = []
        for index, project_tuple in enumerate(self._config['projects'].iteritems()):
            project_name = project_tuple[0]
            project = project_tuple[1]

            project_instance = Project(name=project_name, folder=project.get('folder'))

            # Los plugins se cargan y se ejecutarán en el orden especificado en
            # la lista de la config
            project_instance.plugins = [self.plugin_manager.get_plugin(plugin_name.lower())(self)
                                        for plugin_name in self._config['plugins']]
            projects.append(project_instance)

        return projects

    def save_config(self, result_report_path, indent=''):
        """
        Añade la ubicación del último informe y guarda el archivo de configuración
        """
        self._config.indent_type = indent
        self._config['last_report'] = result_report_path
        self._config.write()
