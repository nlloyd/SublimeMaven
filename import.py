# All of SublimeMaven is licensed under the MIT license.

#   Copyright (c) 2012 Nick Lloyd

#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:

#   The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.

#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#   THE SOFTWARE.

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
    long_project_names = None
    project_per_pom = None

    def run(self, paths):
        settings = sublime.load_settings('Preferences.sublime-settings')
        self.long_project_names = settings.get('long_project_names', None)
        self.project_per_pom = settings.get('project_per_pom', None)

        if len(paths) == 0 and self.window.active_view().file_name():
            active_file = self.window.active_view().file_name()
            if os.path.isfile(active_file):
                paths = [os.path.dirname(active_file)]
            else:
                # pretty sure you can't edit a dir in this editor, but just in case...
                paths = [active_file]

        self.target_path = paths[0]
        if self.long_project_names == None:
            self.window.show_quick_panel(['Short project names (default)', 'Long project names'], self.set_long_project_names)
        elif self.project_per_pom == None:
            self.window.show_quick_panel(['One large project file (default)', 'Project per pom.xml'], self.set_project_per_pom)
        else:
            self.run_project_generator()

    def set_long_project_names(self, idx):
        # short project names are the default
        if idx == 0:
            self.long_project_names = False
        elif idx == 1:
            self.long_project_names = True
        else:
            return
        if self.project_per_pom == None:
            self.window.show_quick_panel(['One large project file (default)', 'Project per pom.xml'], self.set_project_per_pom)
        else:
            self.run_project_generator()

    def set_project_per_pom(self, idx):
        # one project file per pom file, default is false
        if idx == 0:
            self.project_per_pom = False
        elif idx == 1:
            self.project_per_pom = True
        else:
            return
        self.run_project_generator()


    def run_project_generator(self):
        thread = pom.PomProjectGeneratorThread(self.target_path, self.window, self.long_project_names, self.project_per_pom)
        thread.start()
        progress_str = 'Generating project configuration file'
        finished_str = 'Finished generating project configuration file'
        if self.project_per_pom:
            progress_str = progress_str + 's'
            finished_str = finished_str + 's'
        ui.ThreadProgress(thread, progress_str, finished_str)
