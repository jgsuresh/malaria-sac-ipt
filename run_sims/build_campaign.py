import os

import numpy as np
import pandas as pd
from emodpy_malaria.interventions.drug_campaign import add_drug_campaign
from emodpy_malaria.interventions.udbednet import UDBednet

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

archetype_list = ["Southern", "Central", "Eastern", "Coastal Western", "Sahel"]


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

coastal_western_seasonal_itn_use = [
    1,
    0.76,
    0.64,
    0.65,
    0.55,
    0.79,
    0.83,
    0.97,
    0.89,
    0.92,
    0.89,
    0.97
]

eastern_seasonal_itn_use = [
    0.88,
    0.71,
    0.83,
    1,
    0.86,
    0.85,
    0.81,
    0.75,
    0.75,
    0.5,
    0.94,
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
    "Coastal Western": {"Times": month_times, "Values": coastal_western_seasonal_itn_use},
    "Central": {"Times": month_times, "Values": central_seasonal_itn_use},
    "Eastern": {"Times": month_times, "Values": eastern_seasonal_itn_use},
    "Magude": {'min_cov': 0.58, 'max_day': 40},
}

smc_days_in_year = np.array([206,237,267,298])


def add_bednets_for_population_and_births(campaign,
                                          coverage,
                                          start_day=1,
                                          seasonal_dependence=None,
                                          discard_config_type="default",
                                          age_dependence=default_bednet_age_usage):

    if seasonal_dependence is None:
        seasonal_dependence = {}

    regular_bednets_event = UDBednet(camp=campaign,
                                     start_day=start_day,
                                     coverage=coverage,
                                     age_dependence=age_dependence,
                                     seasonal_dependence=seasonal_dependence,
                                     discard_config=discard_config[discard_config_type],
                                     killing_eff=0.6, #explicitly putting in killing/blocking even though these are defaults, in case UDBednet defaults change down the road
                                     killing_constant_duration=0,
                                     killing_decay_rate=1 / 1460.,
                                     blocking_eff=0.9,
                                     blocking_constant_duration=0,
                                     blocking_decay_rate=1/730.)
    campaign.add(regular_bednets_event)

    birth_bednets_event = UDBednet(camp=campaign,
                                   triggers=["Births"],
                                   start_day=start_day,
                                   coverage=coverage,
                                   age_dependence=age_dependence,
                                   seasonal_dependence=seasonal_dependence,
                                   discard_config=discard_config[discard_config_type],
                                   killing_eff=0.6, #explicitly putting in killing/blocking even though these are defaults, in case UDBednet defaults change down the road
                                   killing_constant_duration=0,
                                   killing_decay_rate=1 / 1460.,
                                   blocking_eff=0.9,
                                   blocking_constant_duration=0,
                                   blocking_decay_rate=1/730.)
    campaign.add(birth_bednets_event)



def add_burnin_historical_bednets(campaign, archetype="Southern", start_year=1970):
    # at certain times, add bednets with different coverages
    # these bednet distributions are each for 1 year, then expire (not normal expiration)

    # open CSV
    if archetype == "Southern":
        df = pd.read_csv(os.path.join(manifest.historical_interventions_csv_folder, "southern_historical_itn.csv"))
    else:
        df = pd.read_csv(os.path.join(manifest.historical_interventions_csv_folder, "ssa_historical_itn.csv"))

    for index, row in df.iterrows():
        # Assume 50 year burnin, so 2000 is year 30
        campaign_start_day = int((row["year"]-start_year)*365)

        add_bednets_for_population_and_births(campaign=campaign,
                                              coverage=row["cov_all"],
                                              start_day=campaign_start_day,
                                              seasonal_dependence=archetype_seasonal_usage[archetype],
                                              discard_config_type="flat_annual")


def add_burnin_historical_healthseeking(campaign, archetype="Southern", start_year=1970):
    # at certain times, add HS campaign events with different coverages
    # these campign events are each for 1 year, then expire (not normal expiration)\

    # open CSV
    if archetype == "Southern":
        df = pd.read_csv(os.path.join(manifest.historical_interventions_csv_folder, "southern_historical_hs.csv"))
    else:
        df = pd.read_csv(os.path.join(manifest.historical_interventions_csv_folder, "ssa_historical_hs.csv"))

    for index, row in df.iterrows():
        # Assume 50 year burnin, so 2000 is year 30
        campaign_start_day = int((row["year"]-start_year)*365)

        add_hs_by_age_and_severity(campaign,
                                   u5_hs_rate=row["cov_newclin_youth"],
                                   start_day=campaign_start_day,
                                   duration=365)




#fixme SMC adherent drug not implemented yet in emodpy (2/7/22)
# def smc_adherent_configuration(cb, adherence, sp_resist_day1_multiply):
#     # Copied from HBHI setup
#     smc_adherent_config = configure_adherent_drug(cb, doses = [["Sulfadoxine", "Pyrimethamine",'Amodiaquine'],
#                                                                ['Amodiaquine'],
#                                                                ['Amodiaquine']],
#                                                   dose_interval=1,
#                                                   non_adherence_options=['Stop'],
#                                                   non_adherence_distribution=[1],
#                                                   adherence_config={
#                                                       "class": "WaningEffectMapCount",
#                                                       "Initial_Effect": 1,
#                                                       "Durability_Map": {
#                                                           "Times": [
#                                                               1.0,
#                                                               2.0,
#                                                               3.0
#                                                           ],
#                                                           "Values": [
#                                                               sp_resist_day1_multiply,  # for day 1
#                                                               adherence,  # day 2
#                                                               adherence  # day 3
#                                                           ]
#                                                       }
#                                                   }
#                                                   )
#     return smc_adherent_config


# def add_smc(cb, u5_coverage, start_days, age_range="default"):
#     # Copied from HBHI setup
#     default_adherence = 0.8
#     default_sp_resist_day1_multiply = 0.87
#     adherent_drug_configs = smc_adherent_configuration(cb=cb,
#                                                        adherence=default_adherence,
#                                                        sp_resist_day1_multiply=default_sp_resist_day1_multiply)
#
#     if age_range == "default":
#         add_drug_campaign(cb,
#                           'SMC',
#                           start_days=start_days,
#                           coverage=u5_coverage,
#                           target_group={'agemin': 0.25, 'agemax': 5},
#                           adherent_drug_configs=[adherent_drug_configs],
#                           receiving_drugs_event_name='Received_SMC'
#                           )
#
#         o5_coverage = (0.2/0.9)*u5_coverage
#         add_drug_campaign(cb,
#                           'SMC',
#                           start_days=start_days,
#                           coverage=o5_coverage,
#                           target_group={'agemin': 5, 'agemax': 10},
#                           adherent_drug_configs=[adherent_drug_configs],
#                           receiving_drugs_event_name='Received_SMC'
#                           )
#
#     elif age_range == "u10":
#         add_drug_campaign(cb,
#                           'SMC',
#                           start_days=start_days,
#                           coverage=u5_coverage,
#                           target_group={'agemin': 0.25, 'agemax': 10},
#                           adherent_drug_configs=[adherent_drug_configs],
#                           receiving_drugs_event_name='Received_SMC'
#                           )
#
#     elif age_range == "u15":
#         add_drug_campaign(cb,
#                           'SMC',
#                           start_days=start_days,
#                           coverage=u5_coverage,
#                           target_group={'agemin': 0.25, 'agemax': 15},
#                           adherent_drug_configs=[adherent_drug_configs],
#                           receiving_drugs_event_name='Received_SMC'
#                           )



# def add_burnin_historical_smc(cb, start_year=1970):
#     # CB suggestion: 2016 at 70% and increase 5% every year to 2020 and then hold at 90%
#     u5_cov_dict = {2016: 0.70,
#                 2017: 0.75,
#                 2018: 0.80,
#                 2019: 0.85,
#                 2020: 0.9}
#
#     for year in [2016,2017,2018,2019,2020]:
#         u5_cov = u5_cov_dict[year]
#         dtk_start_days = (year-start_year)*365 + smc_days_in_year
#
#         add_smc(cb, u5_coverage=u5_cov, start_days=dtk_start_days)


#fixme Ideally, wait for Svetlana's quality-of-life updates for an add_ivermectin function, instead of having to do it this way:
# campaign.add(ivermectin.Ivermectin(schema_path_container=campaign,...
# def add_ivermec(cb):
#     add_ivermectin(cb,
#                    box_duration="WEEK",
#                    start_days=[1], #Listening for drug delivery in other methods, then give this drug
#                    # ind_property_restrictions=[{"SchoolStatus": "AttendsSchool"}], # unnecessary, as already listening for who gets IPTsc
#                    trigger_condition_list=['Received_Campaign_Drugs', 'Received_RCD_Drugs'])


def add_primaquine(campaign):
    add_drug_campaign(campaign,
                      'MDA',
                      drug_code="PMQ",
                      start_days=[1],
                      trigger_condition_list=['Received_Campaign_Drugs', 'Received_RCD_Drugs'],
                      receiving_drugs_event_name='Received_Primaquine'
                      )


def add_burnin_historical_interventions(campaign, archetype):
    add_burnin_historical_healthseeking(campaign, archetype)
    add_burnin_historical_bednets(campaign, archetype)
    if archetype == "Sahel":
        raise NotImplementedError
        # add_burnin_historical_smc(cb)


def build_burnin_campaign(archetype):
    campaign = build_standard_campaign_object(manifest=manifest)
    add_burnin_historical_interventions(campaign, archetype)
    return campaign


def build_nonburnin_campaign(archetype):
    campaign = build_standard_campaign_object(manifest=manifest)
    raise NotImplementedError #fixme



def add_scenario_specific_itns(campaign, itn_coverage_level, archetype):
    if itn_coverage_level == "default":
        dtk_coverage = 0.7
        age_dependence = default_bednet_age_usage
    elif itn_coverage_level == "high":
        dtk_coverage = 0.9
        age_dependence = default_bednet_age_usage
    elif itn_coverage_level == "high_and_no_age_dependence":
        dtk_coverage = 0.9
        age_dependence = None

    else:
        print(itn_coverage_level)
        raise NotImplementedError

    add_bednets_for_population_and_births(campaign,
                                          dtk_coverage,
                                          seasonal_dependence=archetype_seasonal_usage[archetype],
                                          discard_config_type="default",
                                          age_dependence=age_dependence)


def add_scenario_specific_healthseeking(cb, hs_rate):
    if hs_rate == "default":
        u5_hs_rate = 0.8
    elif hs_rate == "low":
        u5_hs_rate = 0.6
    else:
        raise NotImplementedError

    add_hs_by_age_and_severity(cb, u5_hs_rate)



def add_scenario_specific_ipt(campaign, scenario_dict, archetype, receiving_drugs_event_name="Received_Campaign_Drugs"):
    # scenario dict has drug_type,screen_type,interval,school_coverage
    if scenario_dict["screen_type"] == "IPT":
        dtk_campaign_type = "MDA"
    elif scenario_dict["screen_type"] == "IST":
        dtk_campaign_type = "MSAT"
    else:
        raise NotImplementedError

    drug_code = scenario_dict["drug_type"]
    if drug_code == "SPAQ":
        drug_code = "SPA"
    if drug_code == "ASAQ":
        drug_code = "ASA"

    # timing:
    timings_df = pd.read_csv("ipt_schedule.csv")
    timings_df = timings_df[np.logical_and(timings_df["archetype"]==archetype,
                                           timings_df["interval"]==scenario_dict["interval"])].reset_index(drop=True)
    campaign_days = np.array(timings_df["day"])

    # Assuming that we do the same thing for 2 years:
    campaign_days = np.append(campaign_days, campaign_days+365)

    add_drug_campaign(campaign,
                      campaign_type=dtk_campaign_type,
                      drug_code=drug_code,
                      start_days=list(campaign_days),
                      coverage=scenario_dict["within_school_coverage"],
                      ind_property_restrictions=[{"SchoolStatus": "AttendsSchool"}],
                      diagnostic_type='BLOOD_SMEAR_PARASITES',
                      diagnostic_threshold=0,
                      receiving_drugs_event_name=receiving_drugs_event_name)



# def add_scenario_specific_smc(cb, age_range="default"):
#     # Both years get 2 years of 90% coverage SMC
#     for year in [0,1]:
#         dtk_start_days = year*365 + smc_days_in_year
#
#         if age_range in ["default", "u10", "u15"]:
#             add_smc(cb, u5_coverage=0.9, start_days=dtk_start_days, age_range=age_range)
#         elif age_range == "u10_with_DP":
#             add_drug_campaign(cb,
#                               campaign_type="MDA",
#                               drug_code="DP",
#                               start_days=list(dtk_start_days),
#                               coverage=0.9,
#                               target_group={'agemin': 0.25, 'agemax': 10},
#                               receiving_drugs_event_name="Received_SMC")
#         elif age_range == "u15_with_DP":
#             add_drug_campaign(cb,
#                               campaign_type="MDA",
#                               drug_code="DP",
#                               start_days=list(dtk_start_days),
#                               coverage=0.9,
#                               target_group={'agemin': 0.25, 'agemax': 15},
#                               receiving_drugs_event_name="Received_SMC")



def add_scenario_specific_interventions(cb, scenario_number, archetype="Southern"):
    # open scenario df and get this number
    scenario_df = pd.read_csv("scenario_master_list.csv")
    scenario_dict = scenario_df[np.logical_and(scenario_df["archetype"]==archetype,
                                               scenario_df["scenario_number"]==scenario_number)].to_dict("records")[0]

    set_school_children_ips(cb,
                            sac_in_school_fraction=(1-scenario_dict["out_of_school_rate"]),
                            age_dependence="complex",
                            target_age_range=scenario_dict["target_age_range"])

    add_scenario_specific_itns(cb, scenario_dict["itn_coverage"], archetype=archetype)
    add_scenario_specific_healthseeking(cb, scenario_dict["hs_rate"])

    if scenario_dict["interval"] != "None":
        add_scenario_specific_ipt(cb, scenario_dict, archetype)

    if scenario_dict["smc_on"]:
        raise NotImplementedError
        # add_scenario_specific_smc(cb, age_range=scenario_dict["smc_age_range"])

    if scenario_dict["ivermectin"]:
        raise NotImplementedError
        # add_ivermec(cb)

    if scenario_dict["primaquine"]:
        add_primaquine(cb)

    return scenario_dict


#fixme Need change_individual_property code.  Waiting on Jonathan 2/9/22
# def set_school_children_ips_for_complex_age_dist(cb, sac_in_school_fraction=0.9, number_of_years=2):
#     df_age_dependence = pd.read_csv("primary_school_attendance_by_age.csv")
#
#     # Initial setup
#     for i,row in df_age_dependence.iterrows():
#         age = row["age"]
#         age_min = age
#         age_max = age+1
#         if age == 6:
#             age_min = 5.5
#
#         change_individual_property(cb,
#                                    target_property_name="SchoolStatus",
#                                    target_property_value="AttendsSchool",
#                                    target_group={"agemin": age_min, "agemax": age_max},
#                                    coverage=sac_in_school_fraction*row["relative_attendance"],
#                                    max_duration=1,
#                                    start_day=1)
#
#
#     # Each September 1st, add in new kids and remove old ones:
#     school_start_day_list = [244 + 365*i for i in range(number_of_years)]
#
#     for school_start_day in school_start_day_list:
#
#         ages = np.array(df_age_dependence["age"])
#         relative_attendances = np.array(df_age_dependence["relative_attendance"])
#
#         # For kids entering
#         change_individual_property(cb,
#                                    target_property_name="SchoolStatus",
#                                    target_property_value="AttendsSchool",
#                                    target_group={"agemin": 5.5, "agemax": 7},
#                                    coverage=sac_in_school_fraction*relative_attendances[0],
#                                    ind_property_restrictions=[{"SchoolStatus": "DoesNotAttendSchool"}],
#                                    max_duration=1,
#                                    start_day=school_start_day)
#
#         # For kids leaving
#         change_individual_property(cb,
#                                    target_property_name="SchoolStatus",
#                                    target_property_value="DoesNotAttendSchool",
#                                    target_group={"agemin": 18, "agemax": 19},
#                                    coverage=1,
#                                    max_duration=1,
#                                    start_day=school_start_day)
#
#         # For kids changing grades
#         for i in range(len(ages)):
#             age = ages[i]
#
#             if 6 < age < 18:
#                 prev_age_attendance = relative_attendances[i-1]
#                 current_age_attendance = relative_attendances[i]
#                 loss_in_relative_attendance = (prev_age_attendance-current_age_attendance)/prev_age_attendance
#
#                 if loss_in_relative_attendance > 0:
#                     change_individual_property(cb,
#                                                target_property_name="SchoolStatus",
#                                                target_property_value="DoesNotAttendSchool",
#                                                target_group={"agemin": age, "agemax": age+1},
#                                                coverage=loss_in_relative_attendance,
#                                                ind_property_restrictions=[{"SchoolStatus": "AttendsSchool"}],
#                                                max_duration=1,
#                                                start_day=school_start_day)
#
#
#
# def set_school_children_ips(cb, sac_in_school_fraction=0.9, age_dependence="simple", target_age_range="default"):
#     def _simple_age_ips(agemin, agemax):
#         # Initial setup
#         change_individual_property(cb,
#                                    target_property_name="SchoolStatus",
#                                    target_property_value="AttendsSchool",
#                                    target_group={"agemin": agemin, "agemax": agemax},
#                                    coverage=sac_in_school_fraction,
#                                    max_duration=1,
#                                    start_day=1)
#
#         # Each September 1st, add in new kids and remove old ones:
#         for school_start_day in [244, 365+244]:
#             change_individual_property(cb,
#                                        target_property_name="SchoolStatus",
#                                        target_property_value="AttendsSchool",
#                                        target_group={"agemin": agemin, "agemax": agemin+1.5},
#                                        coverage=sac_in_school_fraction,
#                                        ind_property_restrictions=[{"SchoolStatus": "DoesNotAttendSchool"}],
#                                        max_duration=1,
#                                        start_day=school_start_day)
#
#             change_individual_property(cb,
#                                        target_property_name="SchoolStatus",
#                                        target_property_value="DoesNotAttendSchool",
#                                        target_group={"agemin": agemax, "agemax": agemax+1},
#                                        coverage=1,
#                                        max_duration=1,
#                                        start_day=school_start_day)
#
#     if target_age_range == "default":
#         if age_dependence == "simple":
#             _simple_age_ips(5.5, 15)
#         elif age_dependence == "complex":
#             set_school_children_ips_for_complex_age_dist(cb, sac_in_school_fraction=sac_in_school_fraction)
#
#     elif target_age_range == "u5":
#         _simple_age_ips(0.25,5)
#     elif target_age_range == "u16":
#         _simple_age_ips(0.25,15)




#fixme use new jsuresh-helpers function import_infections_through_outbreak


def seasonal_daily_importations(campaign, total_importations_per_year, archetype="Southern"):
    if archetype == "Southern":
        seasonal_spline = pd.read_csv("southern_new_infection_spline.csv")
        spline_sum = np.sum(seasonal_spline["new_infections"])
        rescale_factor = total_importations_per_year/spline_sum

        for d in np.arange(365):
            import_infections_through_outbreak(campaign,
                                               days_between_outbreaks=365,
                                               start_day=d,
                                               num_infections=rescale_factor*seasonal_spline["new_infections"].iloc[d])

        return {"total_importations_per_year": total_importations_per_year}

    else:
        raise NotImplementedError