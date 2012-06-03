import sublime
import os
import json
import threading
import xml.sax
import string

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

class PomHandler(xml.sax.ContentHandler):
    elements = []
    groupId = None
    artifactId = None

    def get_project_name(self, long_name = False):
        if not long_name:
            groupid_bits = self.groupId.split('.')
            new_groupid = []
            for bit in groupid_bits:
                new_groupid.append(bit[0])
            self.groupId = string.join(new_groupid, '.')
        return '%s:%s:PROJECT' % (self.groupId, self.artifactId)

    def startElement(self, name, attrs):
        self.elements.append(name)

    def characters(self, content):
        # grab parent groupId first as child groupId defaults to parent if not present
        if len(self.elements) == 3:
            if self.elements[-1] == 'groupId':
                self.groupId = content
        elif len(self.elements) == 2:
            if self.elements[-1] == 'groupId':
                self.groupId = content
            elif self.elements[-1] == 'artifactId':
                self.artifactId = content

    def endElement(self, name):
        self.elements.pop()

'''
PomProjectGeneratorThread: walks a directory tree, searching for all
pom.xml files and generating a project config view result from the findings
'''
class PomProjectGeneratorThread(threading.Thread):
    def __init__(self, target_path, project_file_name, window, long_project_names = False):
        self.target_path = target_path
        self.window = window
        self.project_file_name = project_file_name
        self.long_project_names = long_project_names
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
