import json
import sys

from config import load_config
from project import Project
from utils import run_command


def main():
    try:
        config_file = sys.argv[1]
    except IndexError:
        config_file = "config.ini"

    config = load_config(config_file)

    projects = config.projects
    # Carga el último informe y lo mapea a los nuevos
    if config.last_report:
        setup_projects(config, projects)

    # Ejecuta los comandos de los plugins
    if not config.skip_commands:
        exec_commands(projects)

    # Parsea los resultados
    parse_results(projects)

    # Guarda el informe en formato json
    result_json_filepath = config.output_folder + "/" + config.output_filename + ".json"
    save_projects(projects, result_json_filepath)

    # Guarda el informe en formato txt
    save_report(config, projects)

    # Guarda la ubicación del último informe en la config
    config.save_config(result_report_path=result_json_filepath)


def setup_projects(config, projects):
    with open(config.last_report, mode='r') as old_projects_file:
        old_projects_json = json.load(old_projects_file)

    old_projects = {}
    for project_json in old_projects_json:
        old_project = Project(**project_json)
        old_projects[old_project.name] = old_project

    for new_project in projects:
        try:
            old_project = old_projects[new_project.name]
            new_project.old_reports.update(old_project.reports)
        except KeyError:
            continue


def exec_commands(projects):
    for project in projects:
        if project.error:
            continue

        for plugin in project.plugins:
            if not plugin.makes_command:
                continue

            command = plugin.get_build_command(project_folder=project.folder)
            print(command)
            command_result = run_command(command)
            if command_result.returncode:
                project.handle_plugin_error(plugin, 'Error al ejecutar el comando \n' + command)
                print(command_result.stderr)
                print(command_result.stdout)


def parse_results(projects):
    for project in projects:
        for plugin in project.plugins:
            if not plugin.makes_report or project.error:
                continue

            old_report = project.old_reports.get(plugin.name, None)
            try:
                report = plugin.make_report(project_folder=project.folder,
                                            old_report=old_report)
                project.reports[plugin.name] = report

            except FileNotFoundError:
                project.handle_plugin_error(plugin, 'Error al generar el informe, no se encontró el archivo generado por el plugin')
                print('error file not found')


def save_projects(projects, result_json_filepath):
    with open(result_json_filepath, "w") as json_file:
        json.dump(projects, json_file, default=Project.json_encode, indent=4)


def save_report(config, projects):
    print("Guardando reports")
    with open(config.output_folder + "/" + config.output_filename + ".txt", "w") as text_file:

        for project in projects:
            print(project)
            print(project.name, file=text_file)

            if project.error:
                for plugin_name, error_desc in project.error_plugins:
                    print(": ".join([plugin_name, error_desc]), file=text_file)
                    print(": ".join([plugin_name, error_desc]))

            for plugin, result in project.reports.items():
                print(result.formatted_report, file=text_file)
                print(result.formatted_report)
            print("")

main()
