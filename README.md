# SublimeMaven

Sublime Text 3 Plugin providing integration with the Apache Maven build and project management tool.

## Features

- Maven command execution via side bar menu, context menu, and command palette (available commands configurable, see below)
- Sublime project file creation from a directory hierarchy with multiple pom files
- SublimeJava plugin integration: classpath generation for SublimeJava autocomplete plugin (classpath containing all unique dependencies across all maven projects in the selected directory hierarchy)

  
## User Configuration

Although not always necessary, for cases where M2_HOME is not available to sublime (Sublime not started via command-line on linux/macosx) one must specify in a user settings file named "Maven.sublime-settings" the m2_home property as shown below:

<pre><code>
{
    "maven_env_vars": {
      "m2_home": "/usr/local/maven"
    }
}
</code></pre>

This section of The "Maven.sublime-settings" file can support any environment variable you wish to override or provide to the launched mavne subprocess, such as MAVEN_OPTS or JAVA_HOME.

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
  