import sublime
import os
import json

# write the configuration dependent 'Side Bar', 'Context', and 'Command pallet'
# using user-specified command lists, or defaults if none found
settings = sublime.load_settings('Preferences.sublime-settings')
maven_cmd_entry_list = settings.get('maven_menu_commands', 
    [
        { "caption": "Maven: Run install", "command": "maven", "args": {"paths": [], "goals": ["install"]} },
        { "caption": "Maven: Run clean install", "command": "maven", "args": {"paths": [], "goals": ["clean", "install"]} },
        { "caption": "Maven: Run ...", "command": "maven", "args": {"paths": [], "goals": []} }
    ])

has_custom_run = False
for menu_entry in maven_cmd_entry_list:
    if len(menu_entry['args']['goals']) == 0:
        has_custom_run = True

if not has_custom_run:
    maven_cmd_entry_list.append({ "caption": "Maven: Run ...", "command": "maven", "args": {"paths": [], "goals": []} })

commands_str = json.dumps(maven_cmd_entry_list, indent = 4)

for menu_entry in maven_cmd_entry_list:
    menu_entry['caption'] = menu_entry['caption'].replace('Maven: ', '', 1)

maven_cmd_entry_list.append({ "caption": "-" })
maven_cmd_entry_list.append({ 
        "caption": "Generate Project from all POMs in Path", 
        "command": "import_maven_projects",
        "args": { "paths": [] }
    })

menu_cmd_list = [
        { "caption": "-" },
        {
        "caption": "Maven",
        "children": maven_cmd_entry_list
        }
    ]

menu_cmd_list_str = json.dumps(menu_cmd_list, indent = 4)

maven_packages_path = os.getcwd()
maven_config = open(os.path.join(maven_packages_path, "Context.sublime-menu"), "w+")
maven_config.write(menu_cmd_list_str)
maven_config.flush()
maven_config.close()
maven_config = open(os.path.join(maven_packages_path, "Side Bar.sublime-menu"), "w+")
maven_config.write(menu_cmd_list_str)
maven_config.flush()
maven_config.close()
maven_config = open(os.path.join(maven_packages_path, "Generated.sublime-commands"), "w+")
maven_config.write(commands_str)
maven_config.flush()
maven_config.close()
