import numpy as np
import pandas as pd

# Reimplementing Marita's code but in Python

cost_dict = {
    "ASAQ": 0.50,
    "SPAQ": 0.35,
    "DP": 2.14,
    "AL": 0.69,
    "Ivermectin": 0.091,
    "Primaquine": 0.13,
    "RDT": 0.48,
    "severe": 61.,
    # "facility_treatment": 10.87, # Gilmartin 2021, shifted to 2022: 8.86 * 294.4/240.007 #fixme
    "facility_treatment_mean": 7.05,
    "facility_treatment_low": 7.05-3.70,
    "facility_treatment_high": 7.05+3.70,
    "SMC_per_person_per_season_mean": 6.32, # Average across countries in Gilmartin 2021: 5.15 * 294.4/240.007
    "SMC_per_person_per_season_low": 3.32, # Niger.  Gilmartin 2021.  Shifted to 2022: 2.71 * 294.4/240.007
    "SMC_per_person_per_season_high": 10.06, # Burkina Faso.  Gilmartin 2021: 8.20 * 294.4/240.007
    "IPTsc_CHW_per_person": 0.74,
    "ITN": 2.48}

def compute_costs(df):
    IPT = df["screen_type"]=="IPT"
    IST = df["screen_type"]=="IST"

    df["IPTsc_drug_unit_cost"] = 0
    df["IPTsc_drug_unit_cost"][df["drug_type"]=="ASAQ"] = cost_dict["ASAQ"]
    df["IPTsc_drug_unit_cost"][df["drug_type"]=="SPAQ"] = cost_dict["SPAQ"]
    df["IPTsc_drug_unit_cost"][df["drug_type"]=="DP"] = cost_dict["DP"]
    df["IPTsc_drug_unit_cost"][df["drug_type"]=="None"] = 0

    # IPTsc overhead costs.
    # Low = $0.20 per child per YEAR.
    # (Assume that number per YEAR is calculated as average number seen in each campaign)
    cost_IPTsc_overhead_low_per_child_per_year = 0.27 # Brooker et al. 2008, adjusted to 2022: $0.2*294.4/215.3

    df["num_IPTsc_campaigns"] = 0
    df["num_IPTsc_campaigns"][df["interval"]=="term"] = 3*2 # 3 terms per year for each archetype
    df["num_IPTsc_campaigns"][df["interval"]=="day"] = 365*2 # 3 terms per year for each archetype
    # Number of months for "monthly" different by archetype and school calendar
    df["num_IPTsc_campaigns"][np.logical_and(df["archetype"]=="Southern", df["interval"]=="month")] = 12*2
    df["num_IPTsc_campaigns"][np.logical_and(df["archetype"]=="Central", df["interval"]=="month")] = 11*2
    df["num_IPTsc_campaigns"][np.logical_and(df["archetype"]=="Sahel", df["interval"]=="month")] = 9*2

    df["num_children_reached_per_year"] = 0
    df["num_children_reached_per_year"][IPT] = df["iptsc_drugs_used"][IPT]/df["num_IPTsc_campaigns"][IPT]
    df["num_children_reached_per_year"][IST] = df["iptsc_rdts_used"][IST]/df["num_IPTsc_campaigns"][IST]

    df["IPTsc_overhead_cost_low"] = df["num_children_reached_per_year"] * 2 * cost_IPTsc_overhead_low_per_child_per_year


    # High = $0.74 per child per CAMPAIGN
    cost_IPTsc_overhead_high_per_child_per_campaign = 0.74
    df["IPTsc_overhead_cost_high"] = 0
    df["IPTsc_overhead_cost_high"][IPT] = df["iptsc_drugs_used"][IPT] * cost_IPTsc_overhead_high_per_child_per_campaign
    df["IPTsc_overhead_cost_high"][IST] = df["iptsc_rdts_used"][IST] * cost_IPTsc_overhead_high_per_child_per_campaign

    df["IPTsc_overhead_cost_mean"] = (df["IPTsc_overhead_cost_low"] + df["IPTsc_overhead_cost_high"])/2.

    df["cost_IPTsc_RDTs"] = df["iptsc_rdts_used"] * cost_dict["RDT"]
    df["cost_IPTsc_drugs"] = df["iptsc_drugs_used"] * df["IPTsc_drug_unit_cost"]
    df["cost_IPTsc_commodities"] = df["cost_IPTsc_RDTs"] + df["cost_IPTsc_drugs"]

    df["cost_facility_mean"] = df["cases_treated"] * cost_dict["facility_treatment_mean"]
    df["cost_facility_low"] = df["cases_treated"] * cost_dict["facility_treatment_low"]
    df["cost_facility_high"] = df["cases_treated"] * cost_dict["facility_treatment_high"]

    df["cost_severe"] = df["severe_cases_treated"] * cost_dict["severe"]
    df["cost_ITNs"] = df["itn_coverage"].apply(lambda x: 0.7*5000*2.48 if x=="default" else 0.9*5000*2.48)
    df["cost_ivermectin"] = df["received_ivermectin"] * cost_dict["Ivermectin"]
    df["cost_primaquine"] = df["received_primaquine"] * cost_dict["Primaquine"]

    # SMC costs
    df["num_children_receiving_SMC_annually"] = (df["received_smc"]/4)/2 # 4 rounds per year, 2 years in sim
    num_children_receiving_standard_SMC_annually = np.mean(df[np.logical_and(df["scenario_number"]==30, df["archetype"]=="Sahel")]["num_children_receiving_SMC_annually"])

    smc_on = df["num_children_receiving_SMC_annually"] > 0
    df["cost_SMC_low"] = 0
    df["cost_SMC_high"] = 0

    # Optimistic scenario: SMC cost is lowest across countries Gilmartin+21 AND added cost to scale to other children is just cost for more drug doses
    optimistic_cost_from_standard_SMC = num_children_receiving_standard_SMC_annually * 2 * cost_dict["SMC_per_person_per_season_low"]
    optimistic_cost_from_scaling_to_other_ages = (df["num_children_receiving_SMC_annually"][smc_on]-num_children_receiving_standard_SMC_annually)*cost_dict["SPAQ"]
    df["cost_SMC_low"][smc_on] = optimistic_cost_from_standard_SMC + optimistic_cost_from_scaling_to_other_ages

    # Pessimistic scenario: SMC cost is highest across countries Gilmartin+21 AND added cost to scale to other children is full cost-per-person
    pessimistic_cost_from_standard_SMC_and_scaling = df["num_children_receiving_SMC_annually"][smc_on]* 2 * cost_dict["SMC_per_person_per_season_high"]
    df["cost_SMC_high"][smc_on] = pessimistic_cost_from_standard_SMC_and_scaling

    df["cost_SMC_mean"] = (df["cost_SMC_low"] + df["cost_SMC_high"])/2.


    df["cost_mean"] = df["cost_IPTsc_commodities"] + df["cost_facility_mean"] + df["cost_severe"] + \
                      df["cost_ITNs"] + df["cost_SMC_mean"] + df["cost_ivermectin"] + df["cost_primaquine"] + \
                      df["IPTsc_overhead_cost_mean"]

    df["cost_low_IPTsc_only"] = df["cost_IPTsc_commodities"] + df["cost_facility_mean"] + df["cost_severe"] + \
                      df["cost_ITNs"] + df["cost_SMC_mean"] + df["cost_ivermectin"] + df["cost_primaquine"] + \
                      df["IPTsc_overhead_cost_low"]

    df["cost_high_IPTsc_only"] = df["cost_IPTsc_commodities"] + df["cost_facility_mean"] + df["cost_severe"] + \
                      df["cost_ITNs"] + df["cost_SMC_mean"] + df["cost_ivermectin"] + df["cost_primaquine"] + \
                      df["IPTsc_overhead_cost_high"]

    df["cost_low_SMC_only"] = df["cost_IPTsc_commodities"] + df["cost_facility_mean"] + df["cost_severe"] + \
                      df["cost_ITNs"] + df["cost_SMC_low"] + df["cost_ivermectin"] + df["cost_primaquine"] + \
                      df["IPTsc_overhead_cost_mean"]

    df["cost_high_SMC_only"] = df["cost_IPTsc_commodities"] + df["cost_facility_mean"] + df["cost_severe"] + \
                      df["cost_ITNs"] + df["cost_SMC_high"] + df["cost_ivermectin"] + df["cost_primaquine"] + \
                      df["IPTsc_overhead_cost_mean"]

    df["cost_low"] = df["cost_IPTsc_commodities"] + df["cost_facility_low"] + df["cost_severe"] + \
                      df["cost_ITNs"] + df["cost_SMC_low"] + df["cost_ivermectin"] + df["cost_primaquine"] + \
                      df["IPTsc_overhead_cost_low"]

    df["cost_high"] = df["cost_IPTsc_commodities"] + df["cost_facility_high"] + df["cost_severe"] + \
                      df["cost_ITNs"] + df["cost_SMC_high"] + df["cost_ivermectin"] + df["cost_primaquine"] + \
                      df["IPTsc_overhead_cost_high"]


if __name__=="__main__":
    df = pd.read_csv("220831/sim_data_full.csv")
    compute_costs(df)