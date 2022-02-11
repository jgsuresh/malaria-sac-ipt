from functools import partial

from run_sims.build_campaign import add_burnin_historical_interventions, build_burnin_campaign
from run_sims.build_config import set_archetype_ento
from run_sims.other import build_demographics_from_file


def set_run_number(simulation, value):
    simulation.task.config.parameters.Run_Number = value
    return {"Run_Number": value}


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
        build_campaign_partial = partial(build_burnin_campaign, archetype=archetype)
        simulation.task.create_campaign_from_callback(build_campaign_partial)



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
