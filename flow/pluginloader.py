import imp
import inspect
import os

import flow.utils.commons as commons

plugin_folder = "plugins"
MainModule = "__init__"


def get_plugins():
    clazz = 'plugin_loader'
    method = 'load_plugin'

    plugins = []

    possible_plugins = os.listdir(os.path.join(os.path.dirname(__file__), plugin_folder))
    for i in possible_plugins:
        location = os.path.join(os.path.join(os.path.dirname(__file__), plugin_folder), i)
        if not os.path.isdir(location) or '__pycache__' in location:
            continue
        if not MainModule + ".py" in os.listdir(location):  # no .py file
            commons.printMSG(clazz, method, "Failed to load plugin {}.  Missing __init__ method".format(i), 'ERROR')
            continue

        module_hdl, path_name, description = imp.find_module(MainModule, [location])
        plugins.append({"name": i, "module_hdl": module_hdl, "path_name": path_name, "description": description})

        module_hdl.close()
    return plugins


def load_plugin(plugin):
    clazz = 'plugin_loader'
    method = 'load_plugin'

    current_plugin = imp.load_module(plugin['name'], plugin["module_hdl"], plugin["path_name"], plugin["description"])

    plugin_members = inspect.getmembers(current_plugin)
    plugin_methods = inspect.getmembers(current_plugin, inspect.isfunction)

    if 'run_action' not in tuple(x[0] for x in plugin_methods) or 'register_parser' not in tuple(x[0] for x in
                                                                                                 plugin_methods):
        commons.printMSG(clazz, method, "Failed to find method run_action() and/or register_parser() in plugin {"
                                        "}.".format(plugin), 'ERROR')
        exit(1)

    if 'parser' not in tuple(x[0] for x in plugin_members):
        commons.printMSG(clazz, method, "Failed to find variable 'parser' in plugin {}.".format(plugin), 'ERROR')
        exit(1)

    return current_plugin
