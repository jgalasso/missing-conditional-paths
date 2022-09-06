# -*- coding: utf-8 -*-

import re
import json
from pydriller import Repository
from tqdm import tqdm

def dedentation(line_list):

    l = line_list

    # remove empty lines
    x = re.search("^\s*\s$", l[0])
    while x is not None:
        l = l[1:]
        x = re.search("^\s*\s$", l[0])
    while l[0] == '':
        l = l[1:]

    # indentation can use spaces or tabulations
    indent = re.search("^\s*", l[0]).group()
    no_indent = []

    # remove extra indent
    for line in l:
        if line.startswith(indent):
            no_indent.append(line[len(indent):])
        elif line == "":
            no_indent.append("")
        else:
            print('[!dedent] Fragment was not in a single block')
            return no_indent, True

    return no_indent, False



config = open("./config.json", "r")
config = config.read()
#print(config)

# json file to python dict
config = json.loads(config)


for project in config['projects']:

    # retrieve the name of the project
    # corresponding to the name of the user + ' - ' + name of the repo
    l = project['url'].split('/')
    project_name = l[-2] + '-' + l[-1]

    print('Handling project ' + project_name)
    print('-----------------------------------')
    id = 0

    try:

        # visit all commits of the project
        for commit in Repository(project['url'] + '.git',
                                        only_in_branch=project['branch'],
                                        only_no_merge=True,
                                        only_modifications_with_file_types=['.py']).traverse_commits():

            try:
                # we first examine each file modified by the commit
                for file in commit.modified_files:
    
                    # we examine only the files verifying the following constraints:
                    # 1) the source code must exist before the commit
                    # i.e., the commit must not create the file
                    # 2) the commit must change at least one method in the file
                    # 3) the source code must exist after the commit
                    # i.e., the commit must not delete the file
                    # 4) the file must be a python file
                    # the previous line " only_modifications_with_file_types=['.py'] "
                    # does not always work
                    if (not file.source_code_before == None and
                        len(file.changed_methods) >= 1 and
                        not file.source_code == None and
                        file.filename[-3:] == '.py'):
    
                        # we then examine each modified method in these files
                        for changed_method in file.changed_methods:
    
    
                            # we first retrieve the method before the commit changes were applied
                            # the variable changed_method contains the method after the changes were applied
                            # methods_before contains a list of the methods before the commit
                            # but we don't know which method before corresponds to changed_method
                            # thus, we retrieve every methods before having the same name as changed_method
                            # if there is exactly one method having the same name, perfect
                            # otherwise, we continue with the next changed method
                            methods_before = []
                            for m in file.methods_before:
                                if m.long_name == changed_method.long_name:
                                    methods_before.append(m)
                            if not len(methods_before) == 1:
                                continue
                            else:
                                method_before = methods_before[0]
    
    
                            # first, we verify that no lines were deleted in the method
                            start_before = method_before.start_line
                            end_before = method_before.end_line
                            has_deleted = False
                            for deleted_line in file.diff_parsed["deleted"]:
                                if (deleted_line[0] <= end_before and
                                    deleted_line[0] >= start_before and
                                    not deleted_line[1] == ''):
                                    has_deleted = True
                                    break
                            if has_deleted:
                                continue
    
    
                            # then, we verify that the added lines are in an existing method
                            # (i.e., the added lines do not define the method)
                            # and that at least one added line contains the keyword "if"
                            start = changed_method.start_line
                            end = changed_method.end_line
                            def_method = "def " + changed_method.name
                            is_defined = False
                            add_if = False
                            for added_line in file.diff_parsed["added"]:
                                if added_line[0] <= end and added_line[0] >= start:
                                    if (def_method in added_line[1]):
                                        is_defined = True
                                    if ('if' in added_line[1]):
                                        add_if = True
                            if is_defined:
                                #print('Method definition', tag='discard', tag_color='yellow', color='black')
                                continue
                            if not add_if:
                                #print('No if keyword', tag='discard', tag_color='yellow', color='black')
                                continue
    
    
                            # we retrieve the lines corresponding to the 2 versions of the method
                            code_after = file.source_code.splitlines()
                            code_method_after = code_after[changed_method.start_line - 1 : changed_method.end_line]
                            code_before = file.source_code_before.splitlines()
                            code_method_before = code_before[method_before.start_line - 1 : method_before.end_line]
    
    
                            #print('> Potential fragment: ' + project['url'] + "/commit/" + commit.hash)
    
    
                            # we now collect the list of added lines' number
                            # in the method of interest
                            added_lines = set()
                            for added_line in file.diff_parsed["added"]:
                                if ((added_line[0] >= changed_method.start_line) and
                                    (added_line[0] <= changed_method.end_line)):
                                    added_lines.add(added_line[0])
    
    
                            # we are only interested in added fragments of consecutive lines
                            # so we verify if the added lines of code are consecutives
                            added_lines = list(added_lines)
                            added_lines.sort()
                            consec = True
                            for index in range(1, len(added_lines)):
                                prev_index = index - 1
                                if not added_lines[index] == (added_lines[prev_index] + 1):
                                    consec = False
                                    break
                            if not consec:
                                #print('[!discarded] Fragment has no consecutive lines')
                                continue
    
    
                            # now we are almost sure that the added fragment is a conditional path
    
                            # we modify the numbers of the added lines
                            # so it corresponds to the lines of the methods, and not the file
                            added_lines_renumbered = []
                            for l in added_lines:
                                added_lines_renumbered.append(l - changed_method.start_line + 1)
    
    
                            # we extract the added fragment
                            fragment = code_method_after[added_lines_renumbered[0]-1:added_lines_renumbered[-1]]
    
                            # we remove the extra indentation of the added fragment
                            # sometimes, added fragments are consecutive lines
                            # but do not correspond to a single block
                            # e.g., it is an if statement plus some lines after
                            # in these cases, dedentation returns an issue
                            # and we do not retain this fragment
                            fragment_dedent, fragment_dedent_issue = dedentation(fragment)
                            if  fragment_dedent_issue:
                                #print('[!discarded] Issue when handling fragment indentation')
                                continue
    
    
                            # remove fragments that do not begin by an if
                            if not (fragment_dedent[0].startswith('if') or fragment_dedent[0].startswith('elif')):
                                #print('[!discarded] Fragment first line is not an if')
                                continue
    
    
                            # we also dedent the 2 versions of the method
                            cma_dedent, dedent_issue_after = dedentation(code_method_after)
                            cmb_dedent, dedent_issue_before = dedentation(code_method_before)
                            if  dedent_issue_after or dedent_issue_before:
                                #print('[!discarded] Issue when handling method indentation')
                                continue
    
    
                            #print(project_name + '-' + str(id), tag='stored', tag_color='green', color='white')
                            #print('[stored] ' + project_name + '-' + str(id))
    
                            # Write the files
    
                            with open(config['directory_before'] + project_name + '-' + str(id) + '_before.py', 'w') as file_object:
                                file_object.write('\n'.join(map(str, cmb_dedent)))
                            file_object.close()
    
                            with open(config['directory_after'] + project_name + '-' + str(id) + '_after.py', 'w') as file_object:
                                file_object.write('\n'.join(map(str, cma_dedent)))
                            file_object.close()
    
                            with open(config['directory_fragments'] + project_name + '-' + str(id) + '_fragment.py', 'w') as file_object:
                                file_object.write('\n'.join(map(str, fragment_dedent)))
                            file_object.close()
    
                            csv = project['url'] + "/commit/" + commit.hash + ";"
                            csv += m.name + ';'
                            csv += project_name + '-' + str(id) + ';'
                            for p in added_lines_renumbered:
                                csv += str(p) + " "
                            csv += ";\n"
    
                            with open(config['output_csv'], 'a') as file_csv:
                                file_csv.write(csv)
                            file_csv.close()
    
                            id += 1
            except Exception as e:
                print(e)                      
    except Exception as e:
        print(e)
