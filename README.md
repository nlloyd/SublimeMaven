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