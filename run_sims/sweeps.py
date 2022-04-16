import os
from functools import partial

import numpy as np
import pandas as pd
from COMPS.Data import SimulationFile
from idmtools.core.platform_factory import Platform

from run_sims import manifest
from run_sims.build_campaign import add_burnin_historical_interventions, build_burnin_campaign, build_scenario_campaign, \
    build_test_campaign
from run_sims.build_config import set_archetype_ento
from run_sims.other import build_demographics_from_file
from run_sims.reports import add_burnin_reports, add_scenario_reports


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


def master_sweep_for_core_scenarios(simulation, values):
    archetype = values[0]
    baseline_eir = values[1]
    scenario_number = values[2]

    # Get info about burnins
    df = pd.read_csv(os.path.join(manifest.additional_csv_folder, "burnins.csv"))
    sub_df = df[np.logical_and(df["archetype"]==archetype,
                               df["baseline_eir"]==baseline_eir)].reset_index(drop=True)
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

    return {"archetype": archetype, "baseline_eir": baseline_eir, "scenario_number": scenario_number}


def archetype_and_habitat_sweep_for_burnins(simulation, values):
    archetype = values[0]
    habitat_scale = values[1]

    set_archetype_specifics(simulation, archetype, is_burnin=True)
    set_archetype_ento(simulation.task.config, archetype=archetype, habitat_scale=habitat_scale)

    return {"archetype": archetype, "habitat_scale": habitat_scale}


def core_scenarios_sweep(simulation, scenario_number):
    # open scenario df and get this number
    scenario_df = pd.read_csv(os.path.join(manifest.additional_csv_folder, "scenario_master_list.csv"))
    scenario_dict = scenario_df[np.logical_and(scenario_df["archetype"]==archetype,
                                               scenario_df["scenario_number"]==scenario_number)].to_dict("records")[0]
    #
    # set_school_children_ips(cb,
    #                         sac_in_school_fraction=(1-scenario_dict["out_of_school_rate"]),
    #                         age_dependence="complex",
    #                         target_age_range=scenario_dict["target_age_range"])
    #
    # add_scenario_specific_itns(cb, scenario_dict["itn_coverage"], archetype=archetype)
    # add_scenario_specific_healthseeking(cb, scenario_dict["hs_rate"])
    #
    # if scenario_dict["interval"] != "None":
    #     add_scenario_specific_ipt(cb, scenario_dict, archetype)
    #
    # if scenario_dict["smc_on"]:
    #     add_scenario_specific_smc(cb, age_range=scenario_dict["smc_age_range"])
    #
    # if scenario_dict["ivermectin"]:
    #     add_ivermec(cb)
    #
    # if scenario_dict["primaquine"]:
    #     add_primaquine(cb)
    #
    # return scenario_dict
