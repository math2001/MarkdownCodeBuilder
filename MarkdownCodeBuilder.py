# -*- encoding: utf-8 -*-

import sublime
import sublime_plugin
import tempfile

from .functions import *

MARKDOWN_CODE_BUILDER_FILE = os.path.join(tempfile.gettempdir(), 'MarkdownCodeBuilder')

class MarkdownCodeBuilderCommand(sublime_plugin.TextCommand):

    def _get_executable(self, scope):
        """Needs to be dynamic"""
        settings = get_settings()
        if 'source.python' in scope:
            return settings.get('python_executable', 'python')
        elif 'source.php' in scope:
            return settings.get('php_executable', 'php')
        elif 'source.js' in scope:
            return settings.get('javascript_executable', 'node')

    def _build(self, index):
        if index == -1:
            return
        kwargs = self.build_systems[index]
        variables = self.window.extract_variables()
        variables['file'] = MARKDOWN_CODE_BUILDER_FILE
        if 'shell_cmd' in kwargs:
            kwargs['shell_cmd'] = sublime.expand_variables(kwargs['shell_cmd'], variables)
        if 'cmd' in kwargs:
            kwargs['cmd'] = [sublime.expand_variables(cmd, variables) for cmd in kwargs['cmd']]
        kwargs.pop('selector', None)
        kwargs.pop('variants', None)
        kwargs.pop('name', None)
        self.window.run_command('exec', kwargs)

    def on_navigate(self, href):
        v = self.view
        phantom_index, scope, executable = href.split('-', 2)
        phantom_region = self.phantom_set.phantoms[int(phantom_index)].region
        for region in v.find_by_selector('markup.raw.block.markdown'):
            if not region.contains(phantom_region):
                continue
            with open(MARKDOWN_CODE_BUILDER_FILE, 'w') as fp:
                fp.write('\n'.join(v.substr(region).splitlines()[1:-1]))
            self.build_systems = list(get_build_system_for(scope))
            if len(self.build_systems) == 1:
                self._build(0)
            else:
                self.window.show_quick_panel([item['name'] for item in self.build_systems],
                                             self._build)
            return

    def render_action(self):
        v = self.view
        self.phantom_set = sublime.PhantomSet(v, 'markdown_code_runner')
        code_blocks = v.find_by_selector('markup.raw.block.markdown')
        phantoms = []
        i = 0
        for code_block in code_blocks:
            point = v.full_line(code_block.begin()).end()
            scope = v.scope_name(point)
            scope = ' '.join(filter(lambda bit: not bit.endswith('.markdown'), scope.split(' ')))
            executable = self._get_executable(scope)
            if not executable:
                continue
            phantoms.append(sublime.Phantom(sublime.Region(code_block.end() - 1),
                                            '<a href="{}-{}-{}">Build</a>'.format(i, scope,
                                                                                  executable),
                                            sublime.LAYOUT_INLINE,
                                            self.on_navigate))
            i += 1
        self.phantom_set.update(phantoms)

    def run(self, edit, action, *args, **kwargs):
        view = self.view
        self.window = view.window()
        try:
            function = getattr(self, action + '_action')
        except AttributeError:
            return sublime.error_message("MarkdownCodeBuilder: "
                                         "Couldn't find the action '{}'".format(action))
        function(*args, **kwargs)


# class MarkdownCodeBuilderListener(sublime_plugin.ViewEventListener):

#     @classmethod
#     def is_applicable(cls, settings):
#         return 'markdown' in settings.get('syntax')

#     def on_load(self):
#         self.view.run_command('markdown_code_runner', {'action': 'render'})
