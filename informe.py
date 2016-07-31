import json
import sys
from config import load_config
from contextlib import redirect_stdout
from project import Project
from utils import run_command


def main():
    try:
        config_file = sys.argv[1]
    except IndexError:
        config_file = "config.ini"

    config = load_config(config_file)

    # Carga el último informe y lo mapea a los nuevos
    if config.last_report:

        with open(config.last_report, mode='r') as old_projects_file:
            old_projects_json = json.load(old_projects_file)

        old_projects = {}
        for project_json in old_projects_json:
            old_project = Project(**project_json)
            old_projects[old_project.name] = old_project

        for new_project in config.projects:
            try:
                old_project = old_projects[new_project.name]
                new_project.old_reports = old_project.reports
            except KeyError:
                continue

    # Ejecuta los comandos de los plugins
    for project in config.projects:
        if project.error:
            continue

        for plugin in project.plugins:
            command = plugin.get_build_command(project_folder=project.folder)
            print(command)
            command_result = run_command(command)
            if command_result.returncode:
                project.handle_plugin_error(plugin)

    # Parsea los resultados
    for project in config.projects:
        if project.error:
            continue

        for plugin in project.plugins:
            if plugin.makes_report:
                old_report = project.old_reports.get(plugin.name, None)
                try:
                    report = plugin.make_report(project_folder=project.folder,
                                                old_report=old_report)
                    project.reports[plugin.name] = report

                except FileNotFoundError:
                    project.handle_plugin_error(plugin)

    # Guarda el informe en formato json
    result_json_filepath = config.output_folder + "/" + config.output_filename + ".json"
    with open(result_json_filepath, "w") as json_file:
        json.dump(config.projects, json_file, default=Project.json_encode, indent=4)

    # Guarda el informe en formato txt
    with open(config.output_folder + "/" + config.output_filename + ".txt", "w") as text_file:
        with redirect_stdout(text_file):
            for project in config.projects:
                print(project.name)

                if project.error:
                    print("Error al ejecutar el plugin " + ", ".join(
                        project.error_plugins) + " en el proyecto: " + project.name)

                for plugin, result in project.reports.items():
                    print(result.formatted_report)

    # Guarda la ubicación del último informe en la config
    config.save_config(result_report_path=result_json_filepath)


main()
