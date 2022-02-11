from emodpy import emod_task

from run_sims import manifest

import emod_api.demographics.Demographics as Demographics

def build_demographics_from_file(archetype):
    if archetype == "Central":
        file_path = manifest.demographics_file_path_central
    elif archetype == "Coastal Western":
        file_path = manifest.demographics_file_path_coastal_western
    elif archetype == "Eastern":
        file_path = manifest.demographics_file_path_eastern
    elif archetype == "Sahel":
        file_path = manifest.demographics_file_path_sahel
    elif archetype == "Southern" or archetype == "Magude":
        file_path = manifest.demographics_file_path_southern
    else:
        raise NotImplementedError

    demo = Demographics.from_file(file_path)
    return demo

def include_post_processing(task):
    task = emod_task.add_ep4_from_path(task, manifest.ep4_path)
    return task