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

import os
import sys
import threading
import functools
import re
import subprocess
import sublime
import sublime_plugin

__file__ = os.path.normpath(os.path.abspath(__file__))
__path__ = os.path.dirname(__file__)
# if we are sublime text 2, include libs dir on the path
sublime_version = int(sublime.version())
if (sublime_version >= 2000) and (sublime_version < 3000):
    libs_path = os.path.join(__path__, 'libs')
    if libs_path not in sys.path:
        sys.path.insert(0, libs_path)

try:
    from Maven.utils.mvn import pom
except ImportError:
    from SublimeMaven.utils.mvn import pom
# reload(pom)

settings = None


def plugin_loaded():
    """
    Called when the plugin is loaded and the API is ready to be used.
    """
    global settings
    settings = sublime.load_settings('Maven.sublime-settings')


def get_setting(name, default=None):
   v = settings.get(name)
   if v == None:
      try:
         return sublime.active_window().active_view().settings().get(name, default)
      except AttributeError:
         # No view defined.
         return default
   else:
      return v


file_regex_pattern = '^\[ERROR\] ([A-Z]?[:]?[^\[]+):\[([0-9]+),([0-9]+)\] (.*)'
nt_bad_file_regex_pattern = '^\[ERROR\] ([A-Z]{0}[:]{0}[^\:]+\.java)(.*)$'
# pattern matching windows file path WITHOUT drive letter
# nt_bad_file_regex_pattern = re.compile('(.*\n\[ERROR\] )([A-Z]{0}[:]{0}[^\:]+\.java)(.*)')

'''
Adapted from Default/exec.py with specific modifications
for the mvn process.
'''
class MavenProcessListener(object):
    def on_data(self, proc, data):
        pass

    def on_finished(self, proc):
        pass

'''
Encapsulates subprocess.Popen, forwarding stdout to a supplied
MavenProcessListener (on a separate thread)
'''
class AsyncMavenProcess(object):
    def __init__(self, listener, goals_and_such):

        self.listener = listener
        self.killed = False

        # Hide the console window on Windows
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        m2_settings = get_setting('m2_settings')
        maven_env_vars = get_setting('maven_env_vars')

        env = {}
        if maven_env_vars:
            for env_var, value in maven_env_vars.items():
                env[env_var.upper()] = value

        # add /usr/local/bin to the path (for some reason not present through sublime)
        if os.name == 'posix':
            env['PATH'] = os.environ['PATH'] + os.pathsep + '/usr/local/bin'

        m2_home = None
        if 'M2_HOME' in env:
            env['PATH'] += os.pathsep + env['M2_HOME']
            m2_home = env['M2_HOME']

        proc_env = os.environ.copy()
        proc_env.update(env)
        for k, v in proc_env.items():
            proc_env[k] = os.path.expandvars(v)

        # on windows: use mvn.bat
        maven_cmd = None
        if os.name == 'nt':
            maven_cmd = ['mvn.bat']
        else:
            maven_cmd = ['mvn']

        if m2_home:
            maven_cmd[0] = m2_home + '/bin/' + maven_cmd[0]

        cmd_list = maven_cmd[:]

        if m2_settings:
            cmd_list += ["-s"]
            cmd_list += [m2_settings]
        cmd_list += goals_and_such
        self.proc = subprocess.Popen(cmd_list, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, startupinfo=startupinfo, env=proc_env, shell=False)

        if self.proc.stdout:
            threading.Thread(target=self.read_stdout).start()
            # thread.start_new_thread(self.read_stdout, ())

        if self.proc.stderr:
            threading.Thread(target=self.read_stderr).start()
            # thread.start_new_thread(self.read_stderr, ())

    def kill(self):
        if not self.killed:
            self.killed = True
            if sys.platform == "win32":
                # terminate would not kill process opened by the shell cmd.exe, it will only kill
                # cmd.exe leaving the child running
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.Popen("taskkill /PID " + str(self.proc.pid), startupinfo=startupinfo)
            else:
                self.proc.terminate()
            self.listener = None

    def poll(self):
        return self.proc.poll() == None

    def read_stdout(self):
        while True:
            data = os.read(self.proc.stdout.fileno(), 2**15)

            if len(data) > 0:
                if self.listener:
                    self.listener.on_data(self, data)
            else:
                self.proc.stdout.close()
                if self.listener:
                    self.listener.on_finished(self)
                break

    def read_stderr(self):
        while True:
            data = os.read(self.proc.stderr.fileno(), 2**15)

            if len(data) > 0:
                if self.listener:
                    self.listener.on_data(self, data)
            else:
                self.proc.stderr.close()
                break

'''
MavenCommand: executes Apache Maven on the command line.
Will only be visible if the path argument given is part of a maven project (pom.xml in the current or a parent directory).
'''
class MavenCommand(sublime_plugin.WindowCommand, MavenProcessListener):
    pomDir = None
    cmd = None
    last_run_goals = ['clean','install']
    env = {}
    proc = None
    quiet = False

    def run(self, paths, goals, props=None, kill=False):
        if self.window.active_view():
            self.window.active_view().erase_status('_mvn')

        if kill:
            if self.proc:
                self.proc.kill()
                self.proc = None
                self.append_string(None, "[Cancelled]")
            return

        if len(paths) == 0 and self.window.active_view().file_name():
            paths = [self.window.active_view().file_name()]
        self.pomDir = pom.find_nearest_pom(paths[0])
        if not self.pomDir:
            self.window.active_view().set_status('_mvn', 'No pom.xml found for path ' + paths[0])
            return

        if not hasattr(self, 'output_view'):
            # Try not to call create_output_panel until the regexes are assigned
            self.output_view = self.window.create_output_panel("mvn_exec")

        self.output_view.settings().set("result_file_regex", file_regex_pattern)
        self.output_view.settings().set("result_base_dir", self.pomDir)
        self.output_view.settings().set("word_wrap", False)
        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("scroll_past_end", False)

        # Call create_output_panel a second time after assigning the above
        # settings, so that it'll be picked up as a result buffer
        self.window.create_output_panel("mvn_exec")

        # now lets show the thing
        self.window.run_command("show_panel", {"panel": "output.mvn_exec"})

        if len(goals) == 0:
            self.window.show_input_panel('mvn',' '.join(self.last_run_goals), self.on_done, None, None)
        else:
            self.last_run_goals = goals
            if props:
                self.last_run_goals += [ self.replace_class(prop) for prop in props ]
            self.on_done(' '.join(self.last_run_goals))


    def replace_class(self, str):
        if str.count('$CLASS') == 0:
            return str

        main_class = self.get_current_java_class()
        if main_class is None:
            err_msg = 'Current view is not a valid Java class'
            sublime.error_message(err_msg)
            raise Exception(err_msg)

        return str.replace('$CLASS', main_class)


    def on_done(self, text):
        self.window.run_command("show_panel", {"panel": "output.mvn_exec"})

        if self.pomDir:
            os.chdir(self.pomDir)

        self.last_run_goals = ' '.join(text.split()).split()

        err_type = OSError
        if os.name == "nt":
            err_type = WindowsError

        try:
            self.proc = AsyncMavenProcess(self, self.last_run_goals)
        except err_type as e:
            self.append_string(None, str(e) + "\n")
            if not self.quiet:
                self.append_string(None, "[Finished]")


    def is_enabled(self, paths, goals, props = None, kill = False):
        if len(paths) == 0 and self.window.active_view().file_name():
            paths = [self.window.active_view().file_name()]
        return ((len(paths) == 1) and (pom.find_nearest_pom(paths[0]) != None)) or kill


    def append_data(self, proc, data):
        if proc != self.proc:
            # a second call to exec has been made before the first one
            # finished, ignore it instead of intermingling the output.
            if proc:
                proc.kill()
            return

        try:
            str = data.decode("utf-8")
        except:
            print(data)
            str = "[Decode error - output not utf-8]"
            proc = None

        # Normalize newlines, Sublime Text always uses a single \n separator
        # in memory.
        str = str.replace('\r\n', '\n').replace('\r', '\n')

        # because for some reason on win boxes maven strips the drive letters from the path
        # ... or maybe its just if you have cygwin installed...
        # if os.name == "nt":
        #     drive_letter = self.pomDir[0]
        #     str = nt_bad_file_regex_pattern.sub(r'\1%s:\2\3' % drive_letter, str)

        self.output_view.set_read_only(False)
        self.output_view.run_command('append', {'characters': str, 'force': True, 'scroll_to_end': True})
        self.output_view.set_read_only(True)

        self.output_view.show(self.output_view.size())


    def append_string(self, proc, str):
        self.append_data(proc, str.encode('utf-8'))


    def delayed_output_follow():
        self.output_view.show(self.output_view.size())


    def print_last_str():
        print((self.last_str))


    def finish(self, proc):
        self.append_string(proc, "[Finished]")
        if proc != self.proc:
            return

        self.output_view.show(self.output_view.size())

        errs = self.output_view.find_all_results()
        if len(errs) == 0:
            sublime.status_message("Build finished")
        else:
            sublime.status_message(("Build finished with %d errors") % len(errs))

    def on_data(self, proc, data):
        sublime.set_timeout(functools.partial(self.append_data, proc, data), 0)

    def on_finished(self, proc):
        sublime.set_timeout(functools.partial(self.finish, proc), 0)

    def get_current_java_class(self):
        view = sublime.active_window().active_view()
        data = view.substr(sublime.Region(0, view.size()))

        this_class = re.search("public[ \t]*class[ \t]*(\w+)", data)

        if this_class is not None:
            this_class = this_class.group(1)

            this_package = re.search("[ \t]*package (.*);", data)
            if this_package is not None:
                this_class = this_package.group(1)+"."+this_class

        return this_class
