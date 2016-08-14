class ReportParseError(BaseException):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class Report:
    # TODO: externalizar esta clase y usarla siempre que se use un report (para viejos informes, por ejemplo)

    def __init__(self, report=None, formatted_report=""):
        if report is None: report = []
        self.report = report
        self.formatted_report = formatted_report

    def __repr__(self):
        return str(self.__dict__)


class BasePlugin:
    """
    Interfaz/clase base para los plugins
    """
    makes_report = True
    makes_command = True

    # noinspection PyUnusedLocal
    def __init__(self, config):
        self.error = False
        pass

    @property
    def name(self):
        return self.__class__.__name__

    def json_encode(self):
        return self.__class__.__name__

    def get_diff_report(self, new_report, old_report):
        """
        Obtiene la diferencia entre los reports pasados
        """
        if self.makes_report:
            raise NotImplementedError

    def make_report(self, project_folder, old_report):
        """
        Devuelve un Report con el resultado del parseo y el resultado formateado como string
        """
        if self.makes_report:
            raise NotImplementedError

    def get_build_command(self, project_folder):
        """
        Genera el comando para lanzar el plugin
        """
        if self.makes_command:
            raise NotImplementedError

    def parse_report(self, project_folder):
        """
        Parsea el resultado de la ejecución del plugin
        """
        if self.makes_report:
            raise NotImplementedError
