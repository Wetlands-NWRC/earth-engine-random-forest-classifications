import os
import re
from pprint import pprint

import yaml

if __name__ == "__main__":
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    with open("./assets.txt", 'r') as file:
        lines = [i for i in file.read().strip().split("\n")][3:]

    document = {}
    key = None
    index = 0

    for line in lines:
        section_data = {"uri": None, "Name": None, "row": None, "col": None}
        if line == "":
            key = None
            index = 0
            continue
        elif line[-1] == ":":  # Key of the section
            pat = re.compile(r'\d\d\d')
            key = pat.search(line).group()
            document.update({key: {}})
        elif line != "":
            rowcol = re.compile(r'\d\d\d\d\d\d').search(line).group()
            name = os.path.split(line)[1].split(".")[0]
            row = int(rowcol[:3])
            col = int(rowcol[3:])

            # set the section data
            section_data['uri'] = line
            section_data['Name'] = name
            section_data['row'] = row
            section_data['col'] = col
            document.get(key).update({index: section_data})
            index += 1
        else:
            pass

    with open("./assets.yml", 'w') as stream:
        yaml.dump(document, stream)
