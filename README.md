# SublimeMaven

Sublime Text 2 Plugin providing integration with the Apache Maven build and project management tool.

## Features

- Maven command execution via side bar menu, context menu, and command palette (available commands configurable, see below)


## User Configuration

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