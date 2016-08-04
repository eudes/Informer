from plugins import BasePlugin


class InvalidPluginConfigError(BaseException):
    pass


def get_subclasses(cls):
    """
    Obtiene una lista de las subclases finales (sin herencia propia) que heredan de la clase pasada
    """

    found_subclasses = []
    if cls.__subclasses__():
        for subclass in cls.__subclasses__():
            found_subclasses.extend(get_subclasses(subclass))
    else:
        found_subclasses.append(cls)
    return found_subclasses


class PluginManager:
    """
    Carga y mantiene un mapa de los plugins disponibles
    """

    supported_plugins = {}

    def __init__(self):
        self.register_plugins()

    def register_plugins(self):
        """
        Añade los plugins hijos de BasePlugin al mapa
        """
        for cls in get_subclasses(BasePlugin):
            self.supported_plugins[cls.__name__.lower()] = cls

    def get_plugin(self, plugin_name):
        """
        Devuelve la clase solicitada si existe en el mapa,
        si no, lanza InvalidPluginConfigError
        """
        plugin_name = plugin_name.lower()
        try:
            self.supported_plugins[plugin_name]
        except KeyError:
            raise InvalidPluginConfigError
        return self.supported_plugins[plugin_name]
