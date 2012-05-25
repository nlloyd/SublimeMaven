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
    	cur_path,cur_file = os.path.split(path)

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

	def run(self, paths, goals):
		# on windows: use mvn.bat
		if os.name == 'nt':
			self.cmd = ['mvn.bat']
		else:
			self.cmd = ['mvn']
		self.pomDir = find_nearest_pom(paths[0])
		print self.pomDir
		if len(goals) == 0:
			self.window.show_input_panel('mvn','clean install',self.on_done,None,None)
		else:
			self.on_done(' '.join(goals))

	def on_done(self, text):
		self.cmd += [u'-B']
		self.cmd += text.split(' ')
		print self.cmd
		print self.pomDir
		self.window.run_command("exec",
			{
				"cmd":self.cmd,
				'working_dir':self.pomDir,
				'file_regex':'^\\[ERROR\\] ([^:]+):\\[([0-9]+),([0-9]+)\\] (.*)'
			})

	def is_visible(self, paths, goals):
		return (len(paths) == 1) and (find_nearest_pom(paths[0]) != None)
