import os

import numpy as np
import pandas as pd
from emod_api.interventions.common import change_individual_property
from emodpy_malaria.interventions.adherentdrug import adherent_drug
from emodpy_malaria.interventions.drug_campaign import add_drug_campaign
from emodpy_malaria.interventions.ivermectin import add_triggered_ivermectin
from emodpy_malaria.interventions.usage_dependent_bednet import add_scheduled_usage_dependent_bednet, add_triggered_usage_dependent_bednet

from jsuresh_helpers.interventions.healthseeking import add_hs_by_age_and_severity
from jsuresh_helpers.interventions.importations import import_infections_through_outbreak
from jsuresh_helpers.relative_time import month_times
from jsuresh_helpers.running_emodpy import build_standard_campaign_object
from run_sims import manifest

default_bednet_age_usage = {'youth_cov': 0.65,
                            'youth_min_age': 5,
                            'youth_max_age': 20}

default_itn_discard_rates = {
    "Expiration_Period_Distribution": "DUAL_EXPONENTIAL_DISTRIBUTION",
    "Expiration_Period_Mean_1": 260,
    "Expiration_Period_Mean_2": 2106,
    "Expiration_Period_Proportion_1": 0.6
}

flat_annual_itn_discard_rates = {
    "Expiration_Period_Distribution": "CONSTANT_DISTRIBUTION",
    "Expiration_Period_Constant": 365
}

very_low_discard_rates = {
    "Expiration_Period_Distribution": "EXPONENTIAL_DISTRIBUTION",
    "Expiration_Period_Exponential": 2500
}

discard_config = {
    "default": default_itn_discard_rates,
    "flat_annual": flat_annual_itn_discard_rates,
    "very_low": very_low_discard_rates
}

archetype_list = ["Southern", "Central", "Sahel"]


sahel_seasonal_itn_use = [
    0.84,
    0.71,
    0.74,
    0.55,
    0.56,
    0.62,
    0.85,
    0.94,
    0.98,
    1,
    0.97,
    0.94
]


central_seasonal_itn_use = [
    0.82,
    0.82,
    0.82,
    0.82,
    0.82,
    0.82,
    0.82,
    0.82,
    0.82,
    0.82,
    0.82,
    0.82
]


archetype_seasonal_usage = {
    "Southern": {'min_cov': 0.5, 'max_day': 60},
    "Sahel": {"Times": month_times, "Values": sahel_seasonal_itn_use},
    "Central": {"Times": month_times, "Values": central_seasonal_itn_use},
}

smc_days_in_year = np.array([206, 237, 267, 298])


def add_bednets_for_population_and_births(campaign,
                                          coverage,
                                          start_day=1,
                                          seasonal_dependence=None,
                                          discard_config_type="default",
                                          age_dependence=default_bednet_age_usage,
                                          include_birthnets=True,
                                          birthnet_listening_duration=-1):

    if seasonal_dependence is None:
        seasonal_dependence = {}

    # regular_bednets_event
    add_scheduled_usage_dependent_bednet(campaign=campaign,
                                         start_day=start_day,
                                         demographic_coverage=coverage,
                                         age_dependence=age_dependence,
                                         seasonal_dependence=seasonal_dependence,
                                         discard_config=discard_config[discard_config_type],
                                         killing_initial_effect=0.6, #explicitly putting in killing/blocking even though these are defaults, in case UDBednet defaults change down the road
                                         killing_box_duration=0,
                                         killing_decay_time_constant=1460.,
                                         blocking_initial_effect=0.9,
                                         blocking_box_duration=0,
                                         blocking_decay_time_constant=730.)

    if include_birthnets:
        # birth_bednets_event
        add_triggered_usage_dependent_bednet(campaign=campaign,
                                             trigger_condition_list=["Births"],
                                             start_day=start_day,
                                             demographic_coverage=coverage,
                                             age_dependence=age_dependence,
                                             seasonal_dependence=seasonal_dependence,
                                             discard_config=discard_config[discard_config_type],
                                             listening_duration=birthnet_listening_duration,
                                             killing_initial_effect=0.6,
                                             # explicitly putting in killing/blocking even though these are defaults, in case UDBednet defaults change down the road
                                             killing_box_duration=0,
                                             killing_decay_time_constant=1460.,
                                             blocking_initial_effect=0.9,
                                             blocking_box_duration=0,
                                             blocking_decay_time_constant=730.)



def add_burnin_historical_bednets(campaign, archetype="Southern", start_year=1970, usage_fudge_factor=0.7):
    # at certain times, add bednets with different coverages
    # these bednet distributions are each for 1 year, then expire (not normal expiration)
    # fudge factor reduces effective coverage to account for flat usage, rather than normal expiration

    # open CSV
    if archetype == "Southern":
        df = pd.read_csv(os.path.join(manifest.additional_csv_folder, "southern_historical_itn.csv"))
    else:
        df = pd.read_csv(os.path.join(manifest.additional_csv_folder, "ssa_historical_itn.csv"))

    for index, row in df.iterrows():
        # Assume 50 year burnin, so 2000 is year 30
        campaign_start_day = int((row["year"]-start_year)*365) + 1

        add_bednets_for_population_and_births(campaign=campaign,
                                              coverage=row["cov_all"]*usage_fudge_factor,
                                              start_day=campaign_start_day,
                                              seasonal_dependence=archetype_seasonal_usage[archetype],
                                              discard_config_type="flat_annual",
                                              include_birthnets=True,
                                              birthnet_listening_duration=365)


def add_burnin_historical_healthseeking(campaign, archetype="Southern", start_year=1970):
    # at certain times, add HS campaign events with different coverages
    # these campign events are each for 1 year, then expire (not normal expiration)\

    # open CSV
    if archetype == "Southern":
        df = pd.read_csv(os.path.join(manifest.additional_csv_folder, "southern_historical_hs.csv"))
    else:
        df = pd.read_csv(os.path.join(manifest.additional_csv_folder, "ssa_historical_hs.csv"))

    for index, row in df.iterrows():
        # Assume 50 year burnin, so 2000 is year 30
        campaign_start_day = int((row["year"]-start_year)*365)

        add_hs_by_age_and_severity(campaign,
                                   u5_hs_rate=row["cov_newclin_youth"],
                                   start_day=campaign_start_day,
                                   duration=365)


def adherent_drug_config(campaign,
                         drug_code,
                         adherence=0.8):
    if drug_code == "SPAQ" or drug_code == "spaq":
        doses = [["SulfadoxinePyrimethamine_Annie",'Amodiaquine_Annie'],
                 ['Amodiaquine_Annie'],
                 ['Amodiaquine_Annie']]
        starting_adherence = 1
        #fixme Before was 0.87 for "sp_resist_day1_multiply", but this means 13% of kids receiving never take anything

    elif drug_code == "DP" or drug_code == "dp":
        doses = [["DHA", "Piperaquine"],
                 ["DHA", "Piperaquine"],
                 ["DHA", "Piperaquine"],
                 ]
        starting_adherence = 1

    else:
        raise NotImplementedError

    adherence_values = [starting_adherence, adherence, adherence]

    return adherent_drug(campaign=campaign,
                         doses=doses,
                         dose_interval=1,
                         non_adherence_options=['Stop'],
                         non_adherence_distribution=[1],
                         adherence_values=adherence_values
                         )

def school_adherent_drug_config(campaign, drug_code):
    return adherent_drug_config(campaign, drug_code=drug_code, adherence=1.0)

def smc_adherent_drug_config(campaign, drug_code):
    return adherent_drug_config(campaign, drug_code=drug_code, adherence=0.8)

def add_u5_smc(campaign, coverage, start_days):
    add_drug_campaign(campaign=campaign,
                      campaign_type='SMC',
                      start_days=start_days,
                      coverage=coverage,
                      target_group={'agemin': 0.25, 'agemax': 5},
                      adherent_drug_configs=[smc_adherent_drug_config(campaign=campaign, drug_code="spaq")],
                      receiving_drugs_event_name='Received_SMC_U5'
                      )

def add_extended_smc(campaign, coverage, start_days, drug_code, age_range):
    if age_range == "u10":
        target_group = {'agemin': 5, 'agemax': 10}
        event_name = 'Received_SMC_5-10'
    elif age_range == "u15":
        target_group = {'agemin': 5, 'agemax': 15}
        event_name = 'Received_SMC_5-15'
    else:
        raise NotImplementedError

    add_drug_campaign(campaign=campaign,
                      campaign_type='SMC',
                      start_days=start_days,
                      coverage=coverage,
                      target_group=target_group,
                      adherent_drug_configs=[smc_adherent_drug_config(campaign=campaign, drug_code=drug_code)],
                      receiving_drugs_event_name=event_name
                      )


def add_burnin_historical_smc(campaign, start_year=1970):
    u5_cov_dict = {2016: 0.4,
                   2017: 0.45,
                   2018: 0.5,
                   2019: 0.55,
                   2020: 0.6}

    for year in [2016,2017,2018,2019,2020]:
        u5_cov = u5_cov_dict[year]
        dtk_start_days = (year-start_year)*365 + smc_days_in_year

        add_u5_smc(campaign, coverage=u5_cov, start_days=dtk_start_days)


def add_primaquine(campaign):
    add_drug_campaign(campaign,
                      'MDA',
                      drug_code="PMQ",
                      start_days=[2], # Since code subtracts this by 1, and sim start date in config is 1
                      trigger_condition_list=['Received_Campaign_Drugs'],
                      receiving_drugs_event_name='Received_Primaquine'
                      )


def add_burnin_historical_interventions(campaign, archetype, start_year=1970):
    add_burnin_historical_healthseeking(campaign, archetype, start_year=start_year)
    add_burnin_historical_bednets(campaign, archetype, start_year=start_year)
    if archetype == "Sahel":
        add_burnin_historical_smc(campaign, start_year=start_year)
    add_custom_events(campaign)


def build_burnin_campaign(archetype, start_year=1970):
    campaign = build_standard_campaign_object(manifest=manifest)
    add_burnin_historical_interventions(campaign, archetype, start_year=start_year)
    constant_annual_importation(campaign, total_importations_per_year=25)
    return campaign


def add_custom_events(campaign):
    # Add to custom events (used to do this by directly editing config.parameters.Custom_Individual_Events
    campaign.get_send_trigger("Received_Treatment", old=True)
    campaign.get_send_trigger("Received_Test", old=True)
    campaign.get_send_trigger("Received_Campaign_Drugs", old=True)
    campaign.get_send_trigger("Received_SMC_U5", old=True)
    campaign.get_send_trigger("Received_SMC_5-10", old=True)
    campaign.get_send_trigger("Received_SMC_5-15", old=True)
    campaign.get_send_trigger("Received_Primaquine", old=True)
    campaign.get_send_trigger("Received_Ivermectin", old=True)
    campaign.get_send_trigger("Bednet_Got_New_One", old=True)
    campaign.get_send_trigger("Bednet_Using", old=True)
    campaign.get_send_trigger("Bednet_Discarded", old=True)


def build_scenario_campaign(archetype, scenario_number):
    campaign = build_standard_campaign_object(manifest=manifest)
    add_scenario_specific_interventions(campaign, scenario_number=scenario_number, archetype=archetype)
    constant_annual_importation(campaign, total_importations_per_year=25)
    add_custom_events(campaign)
    return campaign


def add_scenario_specific_itns(campaign, itn_coverage, archetype):
    age_dependence = default_bednet_age_usage

    if archetype == "Sahel":
        start_day = 175  # ITN distribution right before rainy season
    else:
        start_day = 1

    add_bednets_for_population_and_births(campaign,
                                          coverage=itn_coverage,
                                          start_day=start_day,
                                          seasonal_dependence=archetype_seasonal_usage[archetype],
                                          discard_config_type="default",
                                          age_dependence=age_dependence)


def add_scenario_specific_healthseeking(cb, hs_rate):
    add_hs_by_age_and_severity(cb, u5_hs_rate=hs_rate)


def add_scenario_specific_iptsc(campaign,
                                scenario_dict,
                                archetype,
                                receiving_drugs_event_name="Received_Campaign_Drugs"):
    if scenario_dict["delivery_mode"] == "school":
        if scenario_dict["screen_type"] == "IPT":
            dtk_campaign_type = "MDA"
        elif scenario_dict["screen_type"] == "IST":
            dtk_campaign_type = "MSAT"
        else:
            raise NotImplementedError

        drug_config = school_adherent_drug_config(campaign, drug_code=scenario_dict["drug_type"])

        # timing:
        timings_df = pd.read_csv(os.path.join(manifest.additional_csv_folder, "ipt_schedule.csv"))
        timings_df = timings_df[np.logical_and(timings_df["archetype"]==archetype,
                                               timings_df["interval"]==scenario_dict["interval"])].reset_index(drop=True)
        campaign_days = np.array(timings_df["day"])

        add_drug_campaign(campaign,
                          campaign_type=dtk_campaign_type,
                          adherent_drug_configs=drug_config,
                          start_days=list(campaign_days),
                          repetitions=-1,
                          tsteps_btwn_repetitions=365,
                          coverage=scenario_dict["within_school_coverage"],
                          ind_property_restrictions=[{"SchoolStatus": "AttendsSchool"}],
                          diagnostic_type='PF_HRP2',
                          diagnostic_threshold=5,
                          receiving_drugs_event_name=receiving_drugs_event_name)

    elif scenario_dict["delivery_mode"] in ["smc_u10", "smc_u15"]:
        for year in [0,1]:
            dtk_start_days = year*365 + smc_days_in_year

            add_extended_smc(campaign,
                             coverage=scenario_dict["smc_coverage"],
                             start_days=dtk_start_days,
                             drug_code=scenario_dict["drug_type"],
                             age_range=scenario_dict["delivery_mode"])


def add_scenario_specific_interventions(campaign, archetype, scenario_number):
    # open scenario df and get this number
    scenario_df = pd.read_csv(os.path.join(manifest.additional_csv_folder, "scenario_master_list.csv"))
    scenario_dict = scenario_df[np.logical_and(scenario_df["archetype"] == archetype,
                                               scenario_df["scenario_number"] == scenario_number)].to_dict("records")[0]



    # Baseline interventions
    add_hs_by_age_and_severity(campaign, u5_hs_rate=scenario_dict["hs_rate"])

    add_scenario_specific_itns(campaign,
                               itn_coverage=scenario_dict["itn_coverage"],
                               archetype=archetype)

    if scenario_dict["smc_on"]:
        for year in [0, 1]:
            dtk_start_days = year * 365 + smc_days_in_year
            add_u5_smc(campaign, coverage=scenario_dict["smc_coverage"], start_days=dtk_start_days)

    if scenario_dict["iptsc_on"]:
        if scenario_dict["delivery_mode"] == "school":
            set_school_children_ips(campaign=campaign,
                                    sac_in_school_fraction=(1 - scenario_dict["out_of_school_rate"]))

        add_scenario_specific_iptsc(campaign, scenario_dict, archetype)

        if scenario_dict["ivermectin"]:
            add_triggered_ivermectin(campaign,
                                     trigger_condition_list=["Received_Campaign_Drugs"],
                                     killing_box_duration=7)

        if scenario_dict["primaquine"]:
            add_primaquine(campaign)

    return scenario_dict



def set_school_children_ips_for_complex_age_dist(campaign, sac_in_school_fraction=0.9, number_of_years=2):
    df_age_dependence = pd.read_csv(os.path.join(manifest.additional_csv_folder, "primary_school_attendance_by_age.csv"))

    # Initial setup
    for i,row in df_age_dependence.iterrows():
        age = row["age"]
        age_min = age
        age_max = age+1
        if age == 6:
            age_min = 5.5

        change_individual_property(campaign,
                                   target_property_name="SchoolStatus",
                                   target_property_value="AttendsSchool",
                                   target_age_min=float(age_min), # float because of https://github.com/InstituteforDiseaseModeling/emod-api/issues/501
                                   target_age_max=float(age_max), # float because of https://github.com/InstituteforDiseaseModeling/emod-api/issues/501
                                   coverage=sac_in_school_fraction*row["relative_attendance"],
                                   max_duration=1,
                                   start_day=1)


    #fixme The following could probably be done more elegantly with change_individual_property_at_age

    # Each September 1st, add in new kids and remove old ones:
    school_start_day_list = [244 + 365*i for i in range(number_of_years)]

    for school_start_day in school_start_day_list:

        ages = np.array(df_age_dependence["age"])
        relative_attendances = np.array(df_age_dependence["relative_attendance"])

        # For kids entering
        change_individual_property(campaign,
                                   target_property_name="SchoolStatus",
                                   target_property_value="AttendsSchool",
                                   target_age_min=float(5.5), # float because of https://github.com/InstituteforDiseaseModeling/emod-api/issues/501
                                   target_age_max=float(7), # float because of https://github.com/InstituteforDiseaseModeling/emod-api/issues/501
                                   coverage=sac_in_school_fraction*relative_attendances[0],
                                   ip_restrictions=[{"SchoolStatus": "DoesNotAttendSchool"}],
                                   max_duration=1,
                                   start_day=school_start_day)

        # For kids leaving
        change_individual_property(campaign,
                                   target_property_name="SchoolStatus",
                                   target_property_value="DoesNotAttendSchool",
                                   target_age_min=float(18), # float because of https://github.com/InstituteforDiseaseModeling/emod-api/issues/501
                                   target_age_max=float(19), # float because of https://github.com/InstituteforDiseaseModeling/emod-api/issues/501
                                   coverage=1,
                                   max_duration=1,
                                   start_day=school_start_day)

        # For kids changing grades
        for i in range(len(ages)):
            age = ages[i]

            if 6 < age < 18:
                prev_age_attendance = relative_attendances[i-1]
                current_age_attendance = relative_attendances[i]
                loss_in_relative_attendance = (prev_age_attendance-current_age_attendance)/prev_age_attendance


                if loss_in_relative_attendance > 0:
                    change_individual_property(campaign,
                                               target_property_name="SchoolStatus",
                                               target_property_value="DoesNotAttendSchool",
                                               target_age_min=float(age), # float because of https://github.com/InstituteforDiseaseModeling/emod-api/issues/501
                                               target_age_max=float(age+1), # float because of https://github.com/InstituteforDiseaseModeling/emod-api/issues/501
                                               coverage=loss_in_relative_attendance,
                                               ip_restrictions=[{"SchoolStatus": "AttendsSchool"}],
                                               max_duration=1,
                                               start_day=school_start_day)



def set_school_children_ips(campaign, sac_in_school_fraction=0.9, age_dependence="complex"):
    def _simple_age_ips(agemin, agemax):
        # Initial setup
        change_individual_property(campaign,
                                   target_property_name="SchoolStatus",
                                   target_property_value="AttendsSchool",
                                   target_age_min=agemin,
                                   target_age_max=agemax,
                                   coverage=sac_in_school_fraction,
                                   max_duration=1,
                                   start_day=1)

        # Each September 1st, add in new kids and remove old ones:
        for school_start_day in [244, 365+244]:
            change_individual_property(campaign,
                                       target_property_name="SchoolStatus",
                                       target_property_value="AttendsSchool",
                                       target_age_min=agemin,
                                       target_age_max=agemin+1.5,
                                       coverage=sac_in_school_fraction,
                                       ip_restrictions=[{"SchoolStatus": "DoesNotAttendSchool"}],
                                       max_duration=1,
                                       start_day=school_start_day)

            change_individual_property(campaign,
                                       target_property_name="SchoolStatus",
                                       target_property_value="DoesNotAttendSchool",
                                       target_age_min=agemax,
                                       target_age_max=agemax + 1,
                                       coverage=1,
                                       max_duration=1,
                                       start_day=school_start_day)

    if age_dependence == "simple":
        _simple_age_ips(5.5, 15)
    elif age_dependence == "complex":
        set_school_children_ips_for_complex_age_dist(campaign, sac_in_school_fraction=sac_in_school_fraction)




def constant_annual_importation(campaign, total_importations_per_year):
    days_between_importations = int(np.round(365/total_importations_per_year))

    import_infections_through_outbreak(campaign,
                                       days_between_outbreaks=days_between_importations,
                                       start_day=1,
                                       num_infections=1)

    return campaign
