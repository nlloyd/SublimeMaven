import sublime, sublime_plugin
import os

'''
Recursive call to find (and return) the nearest path in the current
tree (searching up the path tree) to a pom.xml file.
Returns None if we hit the root without hitting a pom.xml file.
'''
def find_nearest_pom(path):
    cur_path = None
    if os.path.isdir(path):
        cur_path = path
    else:
        cur_path = os.path.dirname(path)

    if os.path.isfile(os.path.join(cur_path, 'pom.xml')):
        return cur_path
    else:
        parent,child = os.path.split(cur_path)
        if len(child) == 0:
            return None
        else:
            return find_nearest_pom(parent)

'''
MavenCommand: executes Apache Maven on the command line.
Will only be visible if the path argument given is part of a maven project (pom.xml in the current or a parent directory).
'''
class MavenCommand(sublime_plugin.WindowCommand):
    pomDir = None
    cmd = None
    last_run_goals = ['clean','install']

    def run(self, paths, goals):
        self.window.active_view().erase_status('_mvn')
        # on windows: use mvn.bat
        if os.name == 'nt':
            self.cmd = ['mvn.bat']
        else:
            self.cmd = ['mvn']
        if len(paths) == 0 and self.window.active_view().file_name():
            paths = [self.window.active_view().file_name()]
        self.pomDir = find_nearest_pom(paths[0])
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
        self.cmd += [u'-B']
        self.cmd += self.last_run_goals
        self.window.run_command("exec",
            {
                "cmd":self.cmd,
                'working_dir':self.pomDir,
                'file_regex':'^\\[ERROR\\] ([^:]+):\\[([0-9]+),([0-9]+)\\] (.*)'
            })

    def is_enabled(self, paths, goals):
        if len(paths) == 0 and self.window.active_view().file_name():
            paths = [self.window.active_view().file_name()]
        return (len(paths) == 1) and (find_nearest_pom(paths[0]) != None)
