# SPDX-License-Identifier: GPL-3.0-or-later
"""Locate only direct root/canvas children; never traverse Motif's widget tree."""
import re
import subprocess


def native_windows(observation, environment):
    canvas=observation().get('canvas_window')
    if not canvas:
        return []
    result=[]
    for parent in ('root',hex(canvas)):
        command=['xwininfo','-root' if parent=='root' else '-id']
        if parent!='root':command.append(parent)
        query=subprocess.run(command+['-children'],env=environment,capture_output=True,text=True,timeout=3)
        if query.returncode:
            return []
        for window in re.findall(r'^\s*(0x[0-9a-f]+)\s+"Theme Lab — GTK2 nativo(?:; barras de rolagem)?"',query.stdout,re.M):
            attributes=subprocess.run(['xwininfo','-id',window],env=environment,capture_output=True,text=True,timeout=3)
            if attributes.returncode==0 and 'Map State: IsViewable' in attributes.stdout:
                result.append(window)
    return list(dict.fromkeys(result))
