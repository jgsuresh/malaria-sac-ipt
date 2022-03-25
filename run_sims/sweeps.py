import os
from functools import partial

from COMPS.Data import SimulationFile
from idmtools.core.platform_factory import Platform

from run_sims import manifest
from run_sims.build_campaign import add_burnin_historical_interventions, build_burnin_campaign
from run_sims.build_config import set_archetype_ento
from run_sims.other import build_demographics_from_file
from run_sims.reports import add_burnin_reports


def set_run_number(simulation, value):
    simulation.task.config.parameters.Run_Number = value
    return {"Run_Number": value}


def dummy_sweep_for_campaign_viz(simulation, value):
    comps_sim = simulation.get_platform_object()
    # comps_sim = simulation.get_platform_object(platform=value)
    # comps_sim = simulation.get_platform_object(platform=Platform("MalariaSandbox", num_cores=1, node_group="emod_abcd", priority="Highest"))
    index_contents = "https://comps.idmod.org/asset/download/LAIz4q2vjSfCzYX2BYorh2jiEhao4tmiYQP1gKm1uI0_/UmVzZXJ2ZWRGb3JGdXR1cmVVc2U_/XFxJQVpDVkZJTDAxLklETUhQQy5BWlJcSURNXEhvbWVcYnJlc3NsZXJcb3V0cHV0XGRmY1w5MzJcZmI2XGRmYzkzMmZiLTZjNzktZWMxMS1hOWYyLTk0NDBjOWJlMmM1MVxpbnRlcnZlbnRpb25zLmh0bWw_/interventions.html"
    comps_sim.add_file(simulationfile=SimulationFile(os.path.join(manifest.additional_csv_folder, "index.html"), "input"),
                       data=bytes(index_contents, "utf-8"))
    comps_sim.save()
    return {"includes_campaign_visualizer": True}


# Put everything archetype-specific in here, to facilitate sweeps over archetypes
def set_archetype_specifics(simulation, archetype, is_burnin=False):
    # Things each archetype has: demographics file, entomology, historical interventions
    build_demographics = partial(build_demographics_from_file, archetype=archetype)
    simulation.task.create_demog_from_callback(build_demographics)


    if archetype == "Southern" or archetype == "Magude":
        simulation.task.config.parameters.Demographics_Filenames = ["demo_southern.json"]
    elif archetype == "Sahel":
        simulation.task.config.parameters.Demographics_Filenames = ["demo_sahel.json"]
    elif archetype == "Central":
        simulation.task.config.parameters.Demographics_Filenames = ["demo_central.json"]
    elif archetype == "Eastern":
        simulation.task.config.parameters.Demographics_Filenames = ["demo_eastern.json"]
    elif archetype == "Coastal Western":
        simulation.task.config.parameters.Demographics_Filenames = ["demo_coastal_western.json"]
    else:
        raise NotImplementedError

    # If running a burnin, add archetype-specific historical interventions
    if is_burnin:
        build_campaign_partial = partial(build_burnin_campaign, archetype=archetype, start_year=1970)
        simulation.task.create_campaign_from_callback(build_campaign_partial)

        add_burnin_reports(simulation.task, archetype=archetype)




def archetype_and_habitat_sweep(simulation, values, is_burnin):
    archetype = values[0]
    habitat_scale = values[1]

    set_archetype_specifics(simulation, archetype, is_burnin=is_burnin)
    set_archetype_ento(simulation.task.config, archetype=archetype, habitat_scale=habitat_scale)

    return {"archetype": archetype, "habitat_scale": habitat_scale}


def archetype_and_habitat_sweep_for_burnins(simulation, values):
    return archetype_and_habitat_sweep(simulation, values, is_burnin=True)


# def archetype_and_habitat_sweep_for_nonburnins(simulation, values):
#     return partial(archetype_and_habitat_sweep, simulation=simulation, values=values, is_burnin=False)
