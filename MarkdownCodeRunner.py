# -*- encoding: utf-8 -*-

import sublime
import sublime_plugin

from .functions import *

class MarkdownCodeRunnerCommand(sublime_plugin.TextCommand):

    def _get_executable(self, scope):
        """Needs to be dynamic"""
        settings = get_settings()
        if 'source.python' in scope:
            return settings.get('python_executable', 'python')
        elif 'source.php' in scope:
            return settings.get('php_executable', 'php')
        elif 'source.js' in scope:
            return settings.get('javascript_executable', 'node')

    def on_navigate(self, executable):
        sublime.message_dialog("Run code with '{}'".format(executable))

    def render_action(self):
        v = self.view
        self.phantom_set = sublime.PhantomSet(v, 'markdown_code_runner')
        code_blocks = v.find_by_selector('markup.raw.block.markdown')
        phantoms = []
        for code_block in code_blocks:
            point = v.full_line(code_block.begin()).end()
            executable = self._get_executable(v.scope_name(point))
            if not executable:
                continue
            phantoms.append(sublime.Phantom(sublime.Region(code_block.end() - 1),
                                            '<a href="{}">Run</a>'.format(executable),
                                            sublime.LAYOUT_INLINE,
                                            self.on_navigate))
        self.phantom_set.update(phantoms)

    def run(self, edit, action, *args, **kwargs):
        view = self.view
        try:
            function = getattr(self, action + '_action')
        except AttributeError:
            return sublime.error_message("MarkdownCodeRunner: Couldn't find the action '{}'".format(
                                                                                            action))
        function(*args, **kwargs)


# class MarkdownCodeRunnerListener(sublime_plugin.ViewEventListener):

#     @classmethod
#     def is_applicable(cls, settings):
#         return 'markdown' in settings.get('syntax')

#     def on_load(self):
#         self.view.run_command('markdown_code_runner', {'action': 'render'})
