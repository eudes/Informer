import json
import sys
import logging

from config import load_config
from project import Project, Report
from utils import run_command
from plugins import ReportParseError

logging.basicConfig(level=logging.DEBUG)
_log = logging

def test():
    try:
        config_file = sys.argv[1]
    except IndexError:
        config_file = "config.ini"

    config = load_config(config_file)

    projects = config.projects
    # Carga el último informe y lo mapea a los nuevos
    if config.last_report:
        map_new_to_old_projects(config, projects)

    print(projects)


def main():
    try:
        config_file = sys.argv[1]
    except IndexError:
        config_file = "config.ini"

    config = load_config(config_file)

    projects = config.projects
    # Carga el último informe y lo mapea a los nuevos
    if config.last_report:
        map_new_to_old_projects(config, projects)

    # Ejecuta los comandos de los plugins
    if not config.skip_commands:
        exec_commands(projects)

    # Parsea los resultados
    parse_results(projects)

    # Guarda el informe en formato json
    result_json_filepath = config.output_folder + "\\" + config.output_filename + ".json"
    #save_projects(projects, result_json_filepath)

    # Guarda el informe en formato txt
    #save_report(config, projects)

    # Guarda la ubicación del último informe en la config
    #config.save_config(result_report_path=result_json_filepath)

def main2():
    try:
        config_file = sys.argv[1]
    except IndexError:
        config_file = "config.ini"

    config = load_config(config_file)

    projects = config.projects


    # Desacoplar los reports antiguos de los actuales
    # Definir una fase de comparación, posiblemente dentro de la fase de generación de formatted_reports
    # Quitar los formatted reports de la info guardada, hacerlos solo obtenibles mediante la ejecución de una función

    # Carga el último informe y lo mapea a los nuevos
    if config.last_report:
        map_new_to_old_projects(config, projects)

    # Ejecuta los comandos de los plugins
    if not config.skip_commands:
        exec_commands(projects)

    # Parsea los resultados
    parse_results(projects)

    # Guarda el informe en formato json
    result_json_filepath = config.output_folder + "\\" + config.output_filename + ".json"
    #save_projects(projects, result_json_filepath)

    # Guarda el informe en formato txt
    #save_report(config, projects)

    # Guarda la ubicación del último informe en la config
    #config.save_config(result_report_path=result_json_filepath)

def map_new_to_old_projects(config, projects):
    """
    Carga el último report indicado en la config y lo asigna a los projects correspondientes
    para poder comparar luego los resultados
    """
    with open(config.last_report, mode='r') as old_projects_file:
        old_projects_json = json.load(old_projects_file)

    old_projects = {}
    for old_project_json in old_projects_json:
        old_project = Project(**old_project_json)
        old_projects[old_project.name] = old_project

    for new_project in projects:
        try:
            old_project = old_projects[new_project.name]
            new_project.old_reports.update(old_project.reports)
        except KeyError:
            continue


def exec_commands(projects):
    """
    Ejecuta los comandos para los plugins activos de cada proyecto
    """
    for project in projects:
        if project.subprojects:
            # TODO: si un proyecto tiene subproyectos no se ejecutan los comandos
            # Definir explicitamente la lista de plugins a ejecutar para un proyecto
            # Aquí está claro que un proyecto se está comportando de dos formas completamente
            # diferentes. No son el mismo objeto

            # Puede ser necesario que un proyecto contenga otros, pero necesite ejecutar comandos
            exec_commands(project.subprojects)

        else:
            # extraer los plugins del proyecto? en realidad la instanciación de plugins por proyecto no
            # da mal resultado. Permite diferentes configuraciones de la instancia por cada proyecto
            for plugin in project.plugins:
                if not plugin.makes_command:
                    continue

                if project.error:
                    break

                command = plugin.get_build_command(project_folder=project.folder)
                print(command)
                command_result = run_command(command)
                if command_result.returncode:
                    project.handle_plugin_error(plugin, 'Error al ejecutar el comando \n' + command)


def parse_results(projects):
    """
    LLama a la función parse de cada plugin para generar los reports
    """
    for project in projects:
        if project.subprojects:
            print(project.name)

            parse_results(project.subprojects)
            plugin_report_dict = sum_reports(project.subprojects)

            # Genera el report formateado
            for plugin in project.plugins:
                if plugin.name in plugin_report_dict:

                    old_report = project.old_reports.get(plugin.name, None)
                    old_unformatted_report = None
                    if old_report:
                        old_unformatted_report = old_report.get('report')
                    formatted_report = plugin.format_report(
                        new_report=plugin_report_dict[plugin.name], old_report=old_unformatted_report)

                    project.reports[plugin.name] = Report(report=plugin_report_dict[plugin.name],
                                                              formatted_report=formatted_report)

            print(project.reports)

        else:

            for plugin in project.plugins:
                if not plugin.makes_report or project.error:
                    continue

                old_report = project.old_reports.get(plugin.name, None)
                try:
                    report = plugin.make_report(project_folder=project.folder,
                                                old_report=old_report)
                    project.reports[plugin.name] = report

                except FileNotFoundError:
                    project.handle_plugin_error(plugin,
                                                'Error al generar el informe, no se encontró el archivo generado por el plugin')
                except ReportParseError as error:
                    project.handle_plugin_error(plugin, error)


def save_projects(projects, result_json_filepath):
    """
    Guarda los projects en formato json para poder compararlos en el futuro
    """
    with open(result_json_filepath, "w") as json_file:
        json.dump(projects, json_file, default=Project.json_encode, indent=4)


def save_report(config, projects):
    """
    Guarda el informe en formato de texto
    """
    _log.debug("Guardando reports")
    with open(config.output_folder + "/" + config.output_filename + ".txt", "w") as text_file:

        for project in projects:
            _log.debug(project.name)
            print(project.name, file=text_file)

            if project.error:
                for plugin_name, error_desc in project.error_plugins:
                    print(": ".join([plugin_name, error_desc]), file=text_file)
                    _log.debug(": ".join([plugin_name, error_desc]))

            for plugin, result in project.reports.items():
                print(result.formatted_report, file=text_file)
                _log.debug(result.formatted_report)
            print("", file=text_file)


def sum_reports(projects):
    """
    Suma los reports de la lista de proyectos pasada
    """
    plugin_reports = {}
    for project in projects:
        if project.error:
            _log.debug("Error en: %s" % project.name)
            continue

        for plugin_name, report in project.reports.items():
            if plugin_name not in plugin_reports:
                plugin_reports[plugin_name] = report.report
            else:
                for index in range(len(plugin_reports[plugin_name])):
                    plugin_reports[plugin_name][index] += report.report[index]

    return plugin_reports


main()
