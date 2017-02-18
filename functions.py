# -*- encoding: utf-8 -*-

import sublime
import os.path

def get_settings():
    return sublime.load_settings('MarkdownCodeRunner.sublime-settings')

def get_build_system_for(scope=None, file_name=False):
    """A simple functions to get every build system for the matching selector"""

    if isinstance(file_name, bool):
        build_systems = sublime.find_resources('*.sublime-build')
    else:
        build_systems = file_name

    for file in build_systems:
        build_system = sublime.decode_value(sublime.load_resource(file))
        build_system.setdefault('name', os.path.splitext(os.path.basename(file))[0])
        selector = build_system.get('selector', None)
        if not selector or scope is None or sublime.score_selector(scope, selector):
            if file_name is True:
                yield file
            else:
                yield build_system
