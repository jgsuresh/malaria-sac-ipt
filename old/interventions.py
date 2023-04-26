# Put functions relating to interventions here

import pandas as pd
import numpy as np

import emod_api.campaign as campaign
from emodpy_malaria.interventions.add_treatment_seeking import add_health_seeking

import manifest
from emodpy_malaria.interventions.drug_campaign import add_drug_campaign
from emodpy_malaria.interventions.udbednet import UDBednet
from jsuresh_helpers.relative_time import month_times

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
                                          age_dependence=default_bednet_age_usage,
                                          killing_initial=0.6,
                                          killing_decay_constant=1460,
                                          blocking_initial=0.9,
                                          blocking_decay_constant=730):


    regular_bednet_distribution = UDBednet(campaign,
                                           coverage=coverage,
                                           start_day=start_day,
                                           seasonal_dependence=seasonal_dependence,
                                           discard_config=discard_config[discard_config_type],
                                           age_dependence=age_dependence,
                                           killing_eff=killing_initial,
                                           killing_decay_rate=1./killing_decay_constant,
                                           blocking_eff=blocking_initial,
                                           blocking_decay_rate=1./blocking_decay_constant)


    birth_triggered_bednet_distribution = UDBednet(campaign,
                                                   coverage=coverage,
                                                   start_day=start_day,
                                                   seasonal_dependence=seasonal_dependence,
                                                   discard_config=discard_config[discard_config_type],
                                                   age_dependence=age_dependence,
                                                   killing_eff=killing_initial,
                                                   killing_decay_rate=1./killing_decay_constant,
                                                   blocking_eff=blocking_initial,
                                                   blocking_decay_rate=1./blocking_decay_constant,
                                                   triggers=["Birth"])

    campaign.add(regular_bednet_distribution)
    campaign.add(birth_triggered_bednet_distribution)



def burnin_historical_bednets(campaign, archetype="Southern", start_year=1970, usage_fudge_factor=1):
    # at certain times, add bednets with different coverages
    # these bednet distributions are each for 1 year, then expire (not normal expiration)
    # fudge factor reduces effective coverage to account for flat usage, rather than normal expiration


    # open CSV
    if archetype == "Southern":
        df = pd.read_csv("southern_historical_itn.csv")
    else:
        df = pd.read_csv("ssa_historical_itn.csv")

    for index, row in df.iterrows():
        # Assume 50 year burnin, so 2000 is year 30
        campaign_start_day = int((row["year"]-start_year)*365)

        add_bednets_for_population_and_births(campaign,
                                              coverage=row["cov_all"]*usage_fudge_factor,
                                              start_day=campaign_start_day,
                                              seasonal_dependence=archetype_seasonal_usage[archetype],
                                              discard_config_type="flat_annual")




def add_simple_hs(campaign, u5_hs_rate, o5_hs_rate=-1, start_day=1):
    if o5_hs_rate == -1:
        o5_hs_rate = u5_hs_rate * 0.5

    target_list = [{'trigger': 'NewClinicalCase',
                    'coverage': u5_hs_rate,
                    'agemin': 0,
                    'agemax': 5,
                    'seek': 1,
                    'rate': 0.3},
                   {'trigger': 'NewClinicalCase',
                    'coverage': o5_hs_rate,
                    'agemin': 5,
                    'agemax': 100,
                    'seek': 1,
                    'rate': 0.3},
                   {'trigger': 'NewSevereCase',
                    'coverage': 0.9,
                    'agemin': 0,
                    'agemax': 5,
                    'seek': 1,
                    'rate': 0.5},
                   {'trigger': 'NewSevereCase',
                    'coverage': 0.8,
                    'agemin': 5,
                    'agemax': 100,
                    'seek': 1,
                    'rate': 0.5}]

    hs_event = add_health_seeking(campaign,
                                  start_day=start_day,
                                  targets=target_list,
                                  drug=['Artemether', 'Lumefantrine'])

    campaign.add(hs_event)

def smc_adherent_configuration(cb, adherence, sp_resist_day1_multiply):
    # Copied from HBHI setup
    smc_adherent_config = configure_adherent_drug(cb, doses = [["Sulfadoxine", "Pyrimethamine",'Amodiaquine'],
                                                               ['Amodiaquine'],
                                                               ['Amodiaquine']],
                                                  dose_interval=1,
                                                  non_adherence_options=['Stop'],
                                                  non_adherence_distribution=[1],
                                                  adherence_config={
                                                      "class": "WaningEffectMapCount",
                                                      "Initial_Effect": 1,
                                                      "Durability_Map": {
                                                          "Times": [
                                                              1.0,
                                                              2.0,
                                                              3.0
                                                          ],
                                                          "Values": [
                                                              sp_resist_day1_multiply,  # for day 1
                                                              adherence,  # day 2
                                                              adherence  # day 3
                                                          ]
                                                      }
                                                  }
                                                  )
    return smc_adherent_config



def burnin_historical_healthseeking(archetype):
    # at certain times, add HS campaign events with different coverages
    # these campign events are each for 1 year, then expire (not normal expiration)
    # make sure there are birth triggered nets too
    # note: new bednets immediately expire old ones if someone still has an old net
    pass

def add_scenario_specific_healthseeking(scenario_number):
    pass

def burnin_historical_interventions(archetype):
    burnin_historical_bednets(archetype)
    burnin_historical_healthseeking(archetype)

def add_scenario_specific_interventions(campaign, scenario_number):
    add_scenario_specific_itns(campaign, scenario_number)
    add_scenario_specific_healthseeking(campaign, scenario_number)
    add_scenario_specific_ipt(campaign, scenario_number)

def add_scenario_specific_ipt(campaign, scenario_number):
    pass



#fixme create CSV of all intervention scenarios.  each row is a different intervention time.  Then these functions
# will read this CSV, filter to the specified scenario number, then go line by line and add interventions to campaign
def add_drug_interventions(campaign):
    mda_event = add_drug_campaign(campaign,
                                  campaign_type='MDA',
                                  drug_code='DP',
                                  start_days=[50],
                                  coverage=0.5)

    msat_event = add_drug_campaign(campaign,
                                   campaign_type='MSAT',
                                   drug_code='AL',
                                   diagnostic_type='BLOOD_SMEAR_PARASITES',
                                   diagnostic_threshold=0,
                                   start_days=[75],
                                   coverage=0.8)

    campaign.add(mda_event)
    campaign.add(msat_event)
    # campaign.add(healthseeking_event)



def add_simple_hs(campaign,
                  u5_hs_rate,
                  nodeIDs=None):
    o5_hs_rate = u5_hs_rate * 0.5

    def create_target_list(u5_hs_rate, o5_hs_rate):
        return [{'trigger': 'NewClinicalCase',
                 'coverage': u5_hs_rate,
                 'agemin': 0,
                 'agemax': 5,
                 'seek': 1,
                 'rate': 0.3},
                {'trigger': 'NewClinicalCase',
                 'coverage': o5_hs_rate,
                 'agemin': 5,
                 'agemax': 100,
                 'seek': 1,
                 'rate': 0.3},
                {'trigger': 'NewSevereCase',
                 'coverage': 0.9,
                 'agemin': 0,
                 'agemax': 5,
                 'seek': 1,
                 'rate': 0.5},
                {'trigger': 'NewSevereCase',
                 'coverage': 0.8,
                 'agemin': 5,
                 'agemax': 100,
                 'seek': 1,
                 'rate': 0.5}]

    hs_event = add_health_seeking(campaign,
                                  nodeIDs=nodeIDs,
                                  start_day=1,
                                  targets=create_target_list(u5_hs_rate, o5_hs_rate),
                                  drug=['Artemether', 'Lumefantrine'])

    campaign.add_event(hs_event)


# def change_working_men_ips(campaign):
#     # Initialize everyone as being at home:
#     change_individual_property(campaign,
#                                target_property_name="TravelerStatus",
#                                target_property_value="NotTraveler",
#                                start_day=0)
#
#     # Initial setup:
#     young = {'agemin': 10, 'agemax': 15}
#     medium = {'agemin': 15.01, 'agemax': 65}
#     old = {'agemin': 65.01, 'agemax': 70}
#
#     change_individual_property(campaign,
#                                target_property_name="TravelerStatus",
#                                target_property_value="IsTraveler",
#                                target_group=young,
#                                start_day=1,
#                                daily_prob=0.15,
#                                max_duration=1
#                                )
#
#     change_individual_property(campaign,
#                                target_property_name="TravelerStatus",
#                                target_property_value="IsTraveler",
#                                target_group=medium,
#                                start_day=1,
#                                daily_prob=0.3,
#                                max_duration=1
#                                )
#
#     change_individual_property(campaign,
#                                target_property_name="TravelerStatus",
#                                target_property_value="IsTraveler",
#                                target_group=old,
#                                start_day=1,
#                                daily_prob=0.2,
#                                max_duration=1
#                                )


def add_standard_interventions(campaign):
    # change school children ips #fixme Waiting on implementation from Jonathan
    pass




# def add_nonintervention_campaign_events(campaign):
#     change_working_men_ips(campaign)

def build_campaign(scenario_number=-1):
    # Campaign object is built simply by importing
    campaign.set_schema(manifest.schema_file)

    add_standard_interventions(campaign)
    add_scenario_specific_interventions(campaign, scenario_number)


def build_campaign_with_standard_events():
    # Campaign object is built simply by importing
    campaign.schema_path = manifest.schema_file

    # add_standard_interventions(campaign)
    # add_nonintervention_campaign_events(campaign)

    return campaign
