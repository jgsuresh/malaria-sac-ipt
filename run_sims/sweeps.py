import os
from functools import partial

import numpy as np
import pandas as pd
from COMPS.Data import SimulationFile

from run_sims import manifest
from run_sims.build_campaign import build_burnin_campaign, build_scenario_campaign
from run_sims.build_config import set_archetype_ento
from run_sims.other import build_demographics_from_file
from run_sims.reports import add_burnin_reports


def set_run_number(simulation, value):
    simulation.task.config.parameters.Run_Number = value
    return {"Run_Number": value}


# Put everything archetype-specific in here, to facilitate sweeps over archetypes
def set_archetype_specifics(simulation, archetype, is_burnin=False):
    # Things each archetype has: demographics file, entomology, historical interventions
    build_demographics = partial(build_demographics_from_file, archetype=archetype)
    # simulation.task.create_demog_from_callback(build_demographics)

    if archetype == "Southern":
        simulation.task.config.parameters.Demographics_Filenames = ["demo_southern.json"]
    elif archetype == "Sahel":
        simulation.task.config.parameters.Demographics_Filenames = ["demo_sahel.json"]
    elif archetype == "Central":
        simulation.task.config.parameters.Demographics_Filenames = ["demo_central.json"]
    else:
        raise NotImplementedError

    # If running a burnin, add archetype-specific historical interventions
    if is_burnin:
        build_campaign_partial = partial(build_burnin_campaign, archetype=archetype, start_year=1970)
        simulation.task.create_campaign_from_callback(build_campaign_partial)

        add_burnin_reports(simulation.task, archetype=archetype)


def master_sweep_for_core_scenarios(simulation, values, baseline_transmission_metric):
    archetype = values[0]
    transmission_level = values[1]
    scenario_number = values[2]

    # Get info about burnins
    df = pd.read_csv(os.path.join(manifest.additional_csv_folder, "burnins.csv"))
    if baseline_transmission_metric == "eir":
        sub_df = df[np.logical_and(df["archetype"] == archetype,
                                   df["burnin_approx_aeir"] == transmission_level)].reset_index(drop=True)
    elif baseline_transmission_metric == "pfpr":
        sub_df = df[np.logical_and(df["archetype"] == archetype,
                                   df["burnin_approx_pfpr_2-10"] == transmission_level)].reset_index(drop=True)

    burnin_outpath = sub_df["outpath"].iloc[0]
    habitat_scale = sub_df["habitat_scale"].iloc[0]

    # Set up serialization drawing from burnins
    simulation.task.config.parameters.Serialized_Population_Reading_Type = "READ"
    simulation.task.config.parameters.Serialized_Population_Path = os.path.join(burnin_outpath, "output/")
    simulation.task.config.parameters.Serialized_Population_Filenames = ["state-18250.dtk"]

    # Set up archetype-specific demographics file, entomology, and campaign (also uses scenario number)
    set_archetype_specifics(simulation, archetype, is_burnin=False)
    set_archetype_ento(simulation.task.config, archetype=archetype, habitat_scale=habitat_scale)

    #Build campaign for specific scenario
    build_campaign_without_args = partial(build_scenario_campaign, archetype=archetype, scenario_number=scenario_number)
    # build_campaign_without_args = partial(build_test_campaign, archetype=archetype, scenario_number=scenario_number)
    simulation.task.create_campaign_from_callback(build_campaign_without_args)

    return {"archetype": archetype,
            "baseline_transmission_metric": baseline_transmission_metric,
            "transmission_level": transmission_level,
            "scenario_number": scenario_number}



def archetype_and_habitat_sweep_for_burnins(simulation, values):
    archetype = values[0]
    habitat_scale = values[1]

    set_archetype_specifics(simulation, archetype, is_burnin=True)
    set_archetype_ento(simulation.task.config, archetype=archetype, habitat_scale=habitat_scale)

    return {"archetype": archetype, "habitat_scale": habitat_scale}

