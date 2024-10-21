import os
from functools import partial

import numpy as np
import pandas as pd
from emodpy_malaria.interventions.drug_campaign import add_drug_campaign

from jsuresh_helpers.interventions.healthseeking import add_hs_by_age_and_severity
from jsuresh_helpers.running_emodpy import build_standard_campaign_object
from run_sims import manifest
from run_sims.build_campaign import add_bednets_for_population_and_births, add_custom_events, \
    add_scenario_specific_itns, add_u5_smc, archetype_seasonal_usage, build_scenario_campaign, \
    constant_annual_importation, default_bednet_age_usage, school_adherent_drug_config, set_school_children_ips, \
    set_school_children_ips_for_complex_age_dist, smc_days_in_year
from run_sims.build_config import set_archetype_ento, set_full_config
from run_sims.sweeps import set_archetype_specifics


simulation_duration_years = 20
def build_config_long_term_immunity(config):
    set_full_config(config, is_burnin=False)
    config.parameters.Simulation_Duration = simulation_duration_years * 365
    return config
def add_repeated_itn_campaigns(campaign, itn_coverage, archetype):
    age_dependence = default_bednet_age_usage

    if archetype == "Sahel":
        start_day = 175  # ITN distribution right before rainy season
    else:
        start_day = 1

    # repeat every 3 years
    for year in range(simulation_duration_years):
        if year % 3 == 0:
            dtk_start_day = year * 365 + start_day
            add_bednets_for_population_and_births(campaign,
                                                  coverage=itn_coverage,
                                                  start_day=dtk_start_day,
                                                  seasonal_dependence=archetype_seasonal_usage[archetype],
                                                  discard_config_type="default",
                                                  age_dependence=age_dependence,
                                                  include_birthnets=True,
                                                  birthnet_listening_duration=3*365)
def build_long_term_immunity_scenario_campaign(archetype, iptsc_on):
    campaign = build_standard_campaign_object(manifest=manifest)
    hs_rate = 0.6
    itn_coverage = 0.7
    smc_coverage = 0.6
    out_of_school_rate = 0.2
    iptsc_drug_type = "DP"
    campaign_timing = "term"

    # Baseline interventions
    add_hs_by_age_and_severity(campaign, u5_hs_rate=hs_rate)

    add_repeated_itn_campaigns(campaign,
                               itn_coverage=itn_coverage,
                               archetype=archetype)

    if archetype == "Sahel":
        for year in range(simulation_duration_years):
            dtk_start_days = year * 365 + smc_days_in_year
            add_u5_smc(campaign, coverage=smc_coverage, start_days=dtk_start_days)

    if iptsc_on:
        set_school_children_ips_for_complex_age_dist(campaign=campaign,
                                                     sac_in_school_fraction=(1 - out_of_school_rate),
                                                     number_of_years=simulation_duration_years)


        drug_config = school_adherent_drug_config(campaign, drug_code=iptsc_drug_type)

        # timing:
        timings_df = pd.read_csv(os.path.join(manifest.additional_csv_folder, "ipt_schedule.csv"))
        timings_df = timings_df[np.logical_and(timings_df["archetype"]==archetype,
                                               timings_df["interval"]==campaign_timing)].reset_index(drop=True)
        campaign_days = np.array(timings_df["day"])

        add_drug_campaign(campaign,
                          campaign_type="MDA",
                          adherent_drug_configs=[drug_config],
                          start_days=list(campaign_days),
                          repetitions=-1,
                          tsteps_btwn_repetitions=365,
                          coverage=0.9, # Assume 90% of school-going children receive intervention
                          ind_property_restrictions=[{"SchoolStatus": "AttendsSchool"}],
                          receiving_drugs_event_name="Received_Campaign_Drugs")

    constant_annual_importation(campaign, total_importations_per_year=25)
    add_custom_events(campaign)
    return campaign

def master_sweep_for_long_term_immunity_scenarios(simulation, values):
    archetype = values[0]
    transmission_level = values[1]
    iptsc_on = values[2]

    # Get info about burnins
    df = pd.read_csv(os.path.join(manifest.additional_csv_folder, "burnins.csv"))
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
    build_campaign_without_args = partial(build_long_term_immunity_scenario_campaign, archetype=archetype, iptsc_on=iptsc_on)
    simulation.task.create_campaign_from_callback(build_campaign_without_args)

    return {"archetype": archetype,
            "baseline_transmission_metric": "pfpr",
            "transmission_level": transmission_level,
            "iptsc_on": iptsc_on}