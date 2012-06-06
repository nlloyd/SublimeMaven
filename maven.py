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
from utils.mvn import pom
reload(pom)

settings = sublime.load_settings('Preferences.sublime-settings')
m2_home = settings.get('m2_home', None)

'''
MavenCommand: executes Apache Maven on the command line.
Will only be visible if the path argument given is part of a maven project (pom.xml in the current or a parent directory).
'''
class MavenCommand(sublime_plugin.WindowCommand):
    pomDir = None
    cmd = None
    last_run_goals = ['clean','install']
    env = {}

    def run(self, paths, goals):
        self.window.active_view().erase_status('_mvn')
        if m2_home:
            self.env['M2_HOME'] = m2_home
        # on windows: use mvn.bat
        if os.name == 'nt':
            self.cmd = ['mvn.bat']
        else:
            self.cmd = ['mvn']
        # add /usr/local/bin to the path (for some reason not present through sublime)
        if os.name == 'posix':
            self.env['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/local/bin'
        if len(paths) == 0 and self.window.active_view().file_name():
            paths = [self.window.active_view().file_name()]
        self.pomDir = pom.find_nearest_pom(paths[0])
        if not self.pomDir:
            self.window.active_view().set_status('_mvn', 'No pom.xml found for path ' + paths[0])
            return
        if len(goals) == 0:
            self.window.show_input_panel('mvn',' '.join(self.last_run_goals),self.on_done,None,None)
        else:
            self.last_run_goals = goals
            self.on_done(' '.join(self.last_run_goals))

    def on_done(self, text):
        self.last_run_goals = text.split(' ')
        # self.cmd += [u'-B']
        self.cmd += self.last_run_goals
        self.window.run_command("exec",
            {
                "cmd":self.cmd,
                'working_dir':self.pomDir,
                'file_regex':'^\\[ERROR\\] ([^:]+):\\[([0-9]+),([0-9]+)\\] (.*)',
                'env': self.env
            })

    def is_enabled(self, paths, goals):
        if len(paths) == 0 and self.window.active_view().file_name():
            paths = [self.window.active_view().file_name()]
        return (len(paths) == 1) and (pom.find_nearest_pom(paths[0]) != None)
