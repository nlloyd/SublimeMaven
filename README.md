# SublimeMaven

Sublime Text 2 Plugin providing integration with the Apache Maven build and project management tool.

## Features

- Maven command execution via side bar menu, context menu, and command palette (available commands configurable, see below)
- Sublime project file creation from a directory hierarchy with multiple pom files
- SublimeJava plugin integration: classpath generation for SublimeJava autocomplete plugin (classpath containing all unique dependencies across all maven projects in the selected directory hierarchy)


## User Configuration

Although not always necessary, for cases where M2_HOME is not available to sublime (Sublime not started via command-line on linux/macosx) one must specify in user settings the m2_home property as shown below:

<pre><code>
{
    "m2_home": "/usr/local/maven"
}
</code></pre>

The default commands available in the menus and command palette are "mvn install", "mvn clean install", and a choose-your-own mvn execution.
You can change this list to include your own custom commands (note that "Maven: Run ..." is always added to any configured list, if not found).

In your user preferences add an entry like the following with your own custom commands (and caption names).  Example follows:

<pre><code>
	"maven_menu_commands":
	[
        { "caption": "Maven: Run test", "command": "maven", "args": {"paths": [], "goals": ["test"]} },
        { "caption": "Maven: Run install", "command": "maven", "args": {"paths": [], "goals": ["install"]} },
        { "caption": "Maven: Run clean test", "command": "maven", "args": {"paths": [], "goals": ["clean", "test"]} },
        { "caption": "Maven: Run clean install", "command": "maven", "args": {"paths": [], "goals": ["clean", "install"]} }
	]
</code></pre>

For Sublime project configuration generation, the default names for each project is of the form ${shortenedGroupId}:${artifactId}:PROJECT where the ${shortenedGroupId} would be 'o.a.m.p' for a groupId 'org.apache.maven.plugin'.  Adding the following configuration will tell SublimeMaven to use the full groupId in project name generation:

<pre><code>
{
    "long_project_names": true
}
</code></pre>

## Troubleshooting

### Issue #9: Problem when generating projects from pom
The necessary python libraries for xml parsing are not supplied with the packaged python release within the Linux distribution of Sublime Text 2.  The solution to this was discovered by the <a href="https://github.com/Kindari/SublimeXdebug">SublimeXdebug plugin</a>.  Solution copy-pasted below:

To fix the xml.sax module errors in Ubuntu you might need to do the following because Ubuntu stopped shipping Python 2.6 libraries a long time ago:

  $ sudo apt-get install python2.6
  $ ln -s /usr/lib/python2.6 [Sublime Text dir]/lib/

On Ubuntu 12.04, Python 2.6 isn't available, so here's what worked for me:

- Download python2.6 files from <a href="http://packages.ubuntu.com/lucid/python2.6">Ubuntu Archives</a>
- Extract the files: dpkg-deb -x python2.6_2.6.5-1ubuntu6_i386.deb python2.6
- Copy the extracted usr/lib/python2.6 folder to {Sublime Text directory}/lib


## License

All of SublimeMaven is licensed under the MIT license.

  Copyright (c) 2012 Nick Lloyd

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.

  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
  THE SOFTWARE.
  