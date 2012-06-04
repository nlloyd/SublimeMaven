import sublime, sublime_plugin
import os
import string
from utils import ui
from utils.mvn import pom
reload(ui)
reload(pom)

'''
ImportMavenProjectsCommand: creates a *.sublime-project file with folders added for each pom.xml path found starting at a root directory.
File is created as a new view and must be then saved if deemed suitable.
'''
class ImportMavenProjectsCommand(sublime_plugin.WindowCommand):

    def run(self, paths):
        settings = sublime.load_settings('Preferences.sublime-settings')
        long_project_names = settings.get('long_project_names', False)

        if len(paths) == 0 and self.window.active_view().file_name():
            active_file = self.window.active_view().file_name()
            if os.path.isfile(active_file):
                paths = [os.path.dirname(active_file)]
            else:
                # pretty sure you can't edit a dir in this editor, but just in case...
                paths = [active_file]

        _, project_file_name = os.path.split(paths[0])
        project_file_name = project_file_name + '.sublime-project'

        thread = pom.PomProjectGeneratorThread(paths[0], project_file_name, self.window, long_project_names)
        thread.start()
        ui.ThreadProgress(thread, 'Generating %s' % project_file_name,
            'Finished generating %s' % project_file_name)
