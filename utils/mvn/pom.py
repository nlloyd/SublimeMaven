import sublime
import os
import json
import threading
import xml.sax
import string
import subprocess
import re
from StringIO import StringIO

non_cp_mvn_output_pattern = re.compile('^\[[A-Z]+\] ')

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
Use 'mvn -N dependency:build-classpath' to generate the classpath for the specified pom file
'''
class MvnClasspathGrabbingThread(threading.Thread):
    def __init__(self, pom_path):
        self.pom_path = pom_path
        self.classpath = set()
        threading.Thread.__init__(self)

    def run(self):
        curdir = os.getcwd()
        os.chdir(self.pom_path)
        mvn = None
        if os.name == 'nt':
            mvn = 'mvn.bat'
        else:
            mvn = 'mvn'
        # Hide the console window on Windows
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        mvn_proc = subprocess.Popen([mvn,'-N','dependency:build-classpath'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, universal_newlines=True)
        mvn_output, mvn_err = mvn_proc.communicate()
        # print mvn_output
        os.chdir(curdir)
        cp_line = None
        for line in StringIO(mvn_output):
            not_cp_line = non_cp_mvn_output_pattern.match(line)
            if not not_cp_line:
                cp_line = line
                break
        # print '%s -- %s' % (pom_path, cp_line)
        if cp_line:
            jars = cp_line.split(os.pathsep)
            for jar in jars:
                self.classpath.add(jar.strip())
        else:
            print 'WARNING: no classpath found for pom file in path %s' % self.pom_path


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
        self.merged_classpath = set()
        threading.Thread.__init__(self)

    def run(self):
        self.result = None
        pom_paths = []
        os.path.walk(self.target_path, self.find_pom_paths, pom_paths)

        self.result = { "folders": pom_paths }

        cp_threads = []
        max_cp_thread_count = 4

        for project_entry in self.result['folders']:
            # generate project name
            project_entry['name'] = self.gen_project_name(os.path.join(project_entry['path'], 'pom.xml'))
            project_entry['folder_exclude_patterns'] = ['target']
            # grab classpath entries
            cp_thread = MvnClasspathGrabbingThread(project_entry['path'])
            cp_threads.append(cp_thread)
            # print 'starting cp thread for %s' % project_entry['path']
            cp_thread.start()
            # add pom_path/target/classes to classpath
            self.merged_classpath.add(os.path.join(project_entry['path'], 'target', 'classes'))
            # make sure we dont overdo it with active thread count
            if len(cp_threads) == max_cp_thread_count:
                for cp_thread in cp_threads:
                    # print 'waiting on cp_thread'
                    cp_thread.join()
                    # print cp_thread.classpath
                    self.merged_classpath.update(cp_thread.classpath)
                del cp_threads[:]

        # print len(cp_threads)
        for cp_thread in cp_threads:
            # print 'waiting on cp_thread'
            cp_thread.join()
            # print cp_thread.classpath
            self.merged_classpath.update(cp_thread.classpath)

        self.result['settings'] = { 'sublimejava_classpath': list(self.merged_classpath) }

        # print self.merged_classpath
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
