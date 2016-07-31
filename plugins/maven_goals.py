import re
import xml.etree.ElementTree as elementTree

from string import Template

from plugins import BasePlugin, Report
from utils import format_path

__all__ = ["Pmd", "Checkstyle"]


class GoalNotImplementedError(BaseException):
    pass


class MavenGoal(BasePlugin):
    """
    Clase base para las maven goals
    """

    pom_filename = "/pom.xml"

    def __init__(self, config):
        super().__init__(config)
        self.mvn_command_template = self._make_mvn_command_template(config['maven'])

    def _make_mvn_command_template(self, maven_config):
        """
        Construye la plantilla del comando en función de la config.
        Esta plantilla acepta los parámetros folder y goal
        """

        profiles = ""
        if maven_config['profiles']:
            profiles = " ".join(["-P", ",".join(maven_config['profiles'])])

        settings = ""
        if maven_config['settings_file']:
            settings = " ".join(["-s", format_path(maven_config['settings_file'])])
        else:
            print(self.name + ": No se ha indicado un archivo de configuración de maven, usando la configuración por defecto")

        pom_file = " ".join(["-f", "$folder" + self.pom_filename])

        flags_array = ["-B"]
        if maven_config['quiet']:
            flags_array.append("-q")
        flags = " ".join(flags_array)

        base_template_string = " ".join(["mvn", flags, profiles, settings, pom_file, "$goal"])
        return Template(base_template_string)

    def get_diff_report(self, new_report, old_report):
        diff_report = new_report[:]
        old_report_results = None
        if old_report:
            old_report_results = old_report['report']

        for index, value in enumerate(new_report):
            if old_report_results and old_report_results[index]:
                diff_report[index] = value - old_report_results[index]
            else:
                diff_report[index] = "X"

        return diff_report

    def make_report(self, project_folder, old_report):
        new_report = self.parse_report(project_folder)
        diff_report = self.get_diff_report(new_report, old_report)

        formatted_report = self.template.format(*diff_report, *new_report)
        return Report(report=new_report, formatted_report=formatted_report)

    def get_build_command(self, project_folder):
        return self.mvn_command_template.substitute(folder=format_path(project_folder),
                                                    goal=self.command_maven_goal)

    def parse_report(self, project_folder):
        raise NotImplementedError

    @property
    def template(self):
        """
        Plantilla para mostrar el resultado del parseo del informe
        """
        raise NotImplementedError

    @property
    def command_maven_goal(self):
        """
        Goal de maven para el comando mvn
        """
        raise NotImplementedError


class Checkstyle(MavenGoal):
    report_document_path = "/target/site/checkstyle.rss"
    command_maven_goal = "checkstyle:checkstyle"
    template = "Checkstyle: {}/{}/{} ({}/{}/{})"

    def parse_report(self, project_folder):
        """
        Parsea el archivo rss generado por checkstyle
        """
        report = []

        checkstyle_file = (project_folder + self.report_document_path).replace("\\", "/")

        # Obtiene el XML
        tree = elementTree.parse(checkstyle_file)
        root = tree.getroot()

        # Busca el elemento que contiene los datos
        for title in root.find("channel").find("item").find("title").itertext():
            cs_text = title

        report[0] = int(re.findall("Errors: (\d+)", cs_text)[0])
        report[1] = int(re.findall("Warnings: (\d+)", cs_text)[0])
        report[2] = int(re.findall("Infos: (\d+)", cs_text)[0])

        return report


class Pmd(MavenGoal):
    report_document_path = "/target/pmd.xml"
    command_maven_goal = "pmd:pmd"
    template = "PMD: {}/{}/{} ({}/{}/{})"

    def __init__(self, config):
        super().__init__(config)
        self.max_priority = config['maven']['pmd_max_priority']

    def parse_report(self, project_folder):
        """
        Parsea el archivo pmd.xml generado por pmd
        """
        report = [0 for __ in range(self.max_priority)]

        pmd_file = (project_folder + self.report_document_path).replace('\\', '/')

        # Genera la regexs para buscar en las líneas ('priority="x"')
        pmd_patterns = []
        for index in range(len(report)):
            pmd_patterns.append(re.compile('priority=\"{}\"'.format(index)))

        # Busca en cada línea las regexs y aumenta los contadores si las encuentra
        for line, report_index in zip(open(pmd_file), range(len(report))):
            report[report_index] += len(re.findall(pmd_patterns[report_index], line))

        return report

