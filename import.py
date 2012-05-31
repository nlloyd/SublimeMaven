import sublime, sublime_plugin
import os
import json
import threading
import xml.sax

'''
Borrowed from Package Control plugin.
'''
class ThreadProgress():
    def __init__(self, thread, message, success_message):
        self.thread = thread
        self.message = message
        self.success_message = success_message
        self.addend = 1
        self.size = 8
        sublime.set_timeout(lambda: self.run(0), 100)

    def run(self, i):
        if not self.thread.is_alive():
            if hasattr(self.thread, 'result') and not self.thread.result:
                sublime.status_message('')
                return
            sublime.status_message(self.success_message)
            return

        before = i % self.size
        after = (self.size - 1) - before
        sublime.status_message('%s [%s=%s]' % \
            (self.message, ' ' * before, ' ' * after))
        if not after:
            self.addend = -1
        if not before:
            self.addend = 1
        i += self.addend
        sublime.set_timeout(lambda: self.run(i), 100)

class PomHandler(xml.sax.ContentHandler):
    elements = []
    groupId = None
    artifactId = None

    def get_project_name(self):
        return '%s:%s:PROJECT' % (self.groupId, self.artifactId)

    def startElement(self, name, attrs):
        self.elements.append(name)

    def characters(self, content):
        if len(self.elements) == 2:
            if self.elements[-1] == 'groupId':
                self.groupId = content
            if self.elements[-1] == 'artifactId':
                self.artifactId = content

    def endElement(self, name):
        self.elements.pop()

'''
PomProjectGeneratorThread: walks a directory tree, searching for all
pom.xml files and generating a project config view result from the findings
'''
class PomProjectGeneratorThread(threading.Thread):
    def __init__(self, target_path, project_file_name, window):
        self.target_path = target_path
        self.window = window
        self.project_file_name = project_file_name
        threading.Thread.__init__(self)

    def run(self):
        self.result = None
        pom_paths = []
        os.path.walk(self.target_path, self.find_pom_paths, pom_paths)

        self.result = { "folders": pom_paths }

        for project_entry in self.result['folders']:
            project_entry['name'] = self.gen_project_name(os.path.join(project_entry['path'], 'pom.xml'))

        sublime.set_timeout(lambda: self.publish_config_view(), 100)

    def gen_project_name(self, pom_path):
        parser = xml.sax.make_parser()
        pom_data = PomHandler()
        parser.setContentHandler(pom_data)
        pom_file = open(pom_path, 'r')
        parser.parse(pom_file)
        pom_file.close()
        return pom_data.get_project_name()

    '''
    An os.path.walk() visit function that expects as an arg an empty list.  
    Folder paths are added to the pom_path list
    when a pom.xml file is found (hidden paths and 'target' dirs skipped).
    '''
    def find_pom_paths(self, pom_paths, dirname, names):
        # print project_config
        # print 'dirname=' + dirname
        if 'pom.xml' in names:
            pom_paths.append({ "path": dirname })
        tmpnames = names[:]
        for name in tmpnames:
            # skip hiddens
            if name[0] == '.' or name == 'target':
                names.remove(name)

    def publish_config_view(self):
        project_view = self.window.new_file()
        project_edit = project_view.begin_edit()
        project_view.insert(project_edit, 0, json.dumps(self.result, indent = 4))
        project_view.end_edit(project_edit)
        project_view.set_name(self.project_file_name)

'''
ImportMavenProjectsCommand: creates a *.sublime-project file with folders added for each pom.xml path found starting at a root directory.
File is created as a new view and must be then saved if deemed suitable.
'''
class ImportMavenProjectsCommand(sublime_plugin.WindowCommand):

    def run(self, paths):
        active_file = self.window.active_view().file_name()
        if len(paths) == 0 and active_file:
            if os.path.isfile(active_file):
                paths = [os.path.dirname(active_file)]
            else:
                # pretty sure you can't edit a dir in this editor, but just in case...
                paths = [active_file]

        _, project_file_name = os.path.split(paths[0])
        project_file_name = project_file_name + '.sublime-project'

        thread = PomProjectGeneratorThread(paths[0], project_file_name, self.window)
        thread.start()
        ThreadProgress(thread, 'Generating %s' % project_file_name,
            'Finished generating %s' % project_file_name)
