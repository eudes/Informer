import re
import xml.etree.ElementTree as elementTree

from string import Template

from project import Report
from plugins import BasePlugin, ReportParseError
from utils import format_path

__all__ = ['Pmd', 'Checkstyle']


class GoalNotImplementedError(BaseException):
    pass


class MavenGoal(BasePlugin):
    """
    Clase base para las maven goals
    """

    pom_filename = '/pom.xml'

    def __init__(self, config):
        super().__init__(config)
        self.mvn_command_template = self._make_mvn_command_template(config['maven'])

    def _make_mvn_command_template(self, maven_config):
        """
        Construye la plantilla del comando en función de la config.
        Esta plantilla acepta los parámetros folder y goal
        """

        profiles = ''
        # TODO: arreglar el caso de que solo haya un valor (forcelist)
        if maven_config.get('profiles'):
            profiles = ' '.join(['-P', ','.join(maven_config['profiles'])])

        settings = ''
        if maven_config.get('settings_file'):
            settings = ' '.join(['-s', format_path(maven_config['settings_file'])])

        pom_file = ' '.join(['-f', '$folder' + self.pom_filename])

        flags_array = ['-B']
        if maven_config.get('quiet'):
            flags_array.append('-q')
        if maven_config.get('skip_tests'):
            flags_array.append('-DskipTests')
        if maven_config.get('flags'):
            flags_array.extend(maven_config['flags'])
        flags = ' '.join(flags_array)

        base_template_string = ' '.join(['mvn', flags, profiles, settings, pom_file, '$goal'])
        return Template(base_template_string)

    def get_diff_report(self, new_report, old_report):
        diff_report = new_report[:]
        if not old_report:
            return ['X' for index in new_report]

        for index, value in enumerate(new_report):
            diff = 'X'

            try:
                if index < len(old_report) and old_report[index] != 'X':
                    diff = value - old_report[index]
            except KeyError:
                pass

            diff_report[index] = diff

        return diff_report

    def make_report(self, project_folder, old_report):
        new_report = self.parse_report(project_folder)
        formatted_report = self.format_report(new_report, old_report)
        return Report(report=new_report, formatted_report=formatted_report)

    def format_report(self, new_report, old_report):
        diff_report = self.get_diff_report(new_report, old_report)
        return self.template.format(*diff_report, *new_report)

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
    report_document_path = '/target/site/checkstyle.rss'
    command_maven_goal = 'checkstyle:checkstyle'
    template = 'Checkstyle: {}/{}/{} ({}/{}/{})'

    def parse_report(self, project_folder):
        """
        Parsea el archivo rss generado por checkstyle
        """
        report = [0, 0, 0]

        checkstyle_file = (project_folder + self.report_document_path).replace('\\', '/')

        # Obtiene el XML
        tree = elementTree.parse(checkstyle_file)
        root = tree.getroot()

        # Busca el elemento que contiene los datos
        for title in root.find('channel').find('item').find('title').itertext():
            cs_text = title
            break
        else:
            raise ReportParseError('No se encontraron resultados en el archivo checkstyle')

        report[0] = int(re.findall('Errors: (\d+)', cs_text)[0])
        report[1] = int(re.findall('Warnings: (\d+)', cs_text)[0])
        report[2] = int(re.findall('Infos: (\d+)', cs_text)[0])

        return report


# noinspection PyUnusedLocal
class Pmd(MavenGoal):
    report_document_path = '/target/pmd.xml'
    command_maven_goal = 'pmd:pmd -Dformat="xml"'
    template = 'PMD: {}/{}/{} ({}/{}/{})'

    def __init__(self, config):
        super().__init__(config)
        self.max_priority = config['maven']['pmd_max_priority']

    def parse_report(self, project_folder):
        """
        Parsea el archivo pmd.xml generado por pmd
        """
        report = [0 for __ in range(self.max_priority)]

        pmd_file_path = (project_folder + self.report_document_path).replace('\\', '/')

        # Genera la regexs para buscar en las líneas ('priority="x"')
        pmd_patterns = []
        for index in range(len(report)):
            regex = 'priority=\"%s\"' % (index + 1)
            pmd_patterns.append(regex)

        # Busca en cada línea las regexs y aumenta los contadores si las encuentra
        with open(pmd_file_path) as pmd_file:
            for line in pmd_file.readlines():
                for report_index in range(len(report)):
                    report[report_index] += len(re.findall(pmd_patterns[report_index], line))

        return report

