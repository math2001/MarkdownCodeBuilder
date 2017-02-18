# -*- encoding: utf-8 -*-

import sublime
import sublime_plugin
import tempfile

from .functions import *

MARKDOWN_CODE_BUILDER_FILE = os.path.join(tempfile.gettempdir(), 'MarkdownCodeBuilder')
STYLE = """\
html {
  margin: 0;
  padding: 0;
}

#MarkdownCodeBuilder {
  background-color: var(--background);
  color: var(--foreground);
  margin: 0;
  padding: 0;
}

#MarkdownCodeBuilder a {
  text-decoration: none;
  color: var(--background);
}

.label {
  border-radius: 3px;
  color: var(--background);
  background-color: var(--foreground);
  padding: 0 5px;
}
"""
HTML = """\
<body id="MarkdownCodeBuilder" class="miniui">
<style>
{css}
</style>
{link}
</body>
"""

class MarkdownCodeBuilderCommand(sublime_plugin.TextCommand):

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

    def build(self, href):
        view = self.view

        phantom_index, fresh, self.build_systems = href.split('-', 2)
        phantom_index = int(phantom_index)
        phantom_region = self.phantom_set.phantoms[phantom_index].region
        fresh = fresh == 'fresh'
        self.build_systems = self.build_systems.split('??')

        content = []
        for i, region in enumerate(view.find_by_selector('markup.raw.block.markdown')):
            if not ((region.contains(phantom_region)
                    or (fresh is False and region.begin() < phantom_region.begin()))
                    and (self._get_build_systems_from_region(view, region) == self.build_systems)):
                continue
            content.append('\n'.join(view.substr(region).splitlines()[1:-1]))

        with open(MARKDOWN_CODE_BUILDER_FILE, 'w') as fp:
            fp.write('\n'.join(content))

        self.build_systems = list(get_build_system_for(file_name=self.build_systems))

        if len(self.build_systems) == 1:
            self._build(0)
        else:
            self.window.show_quick_panel([item['name'] for item in self.build_systems],
                                         self._build)

        return
        phantom_index, scope, executable, fresh = href.split('-', 3)
        for i, region in enumerate(v.find_by_selector('markup.raw.block.markdown')):
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

    def _get_build_systems_from_region(self, v, code_block):
        point = v.full_line(code_block.begin()).end()
        scope = ' '.join(filter(lambda bit: not bit.endswith('.markdown'),
                                v.scope_name(point).split(' ')))
        return list(get_build_system_for(scope, file_name=True))

    def render_action(self):
        v = self.view
        self.phantom_set = sublime.PhantomSet(v, 'markdown_code_runner')
        code_blocks = v.find_by_selector('markup.raw.block.markdown')
        phantoms = []
        link = '<span class="label"><a href="{0}-fresh-{1}">►</a> ' \
               '<a href="{0}-continuation-{1}">➤</a></span>'

        for i, code_block in enumerate(code_blocks):

            build_systems = self._get_build_systems_from_region(v, code_block)

            phantoms.append(sublime.Phantom(
                sublime.Region(code_block.end() - 1),
                HTML.format(link=link.format(i, '??'.join(build_systems)), css=STYLE),
                sublime.LAYOUT_INLINE,
                self.build
            ))
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
