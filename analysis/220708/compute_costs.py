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
    "facility_treatment": 9.67,
    "SMC_per_person_per_season": 5.15,
    "IPTsc_CHW_per_person": 0.74,
    "ITN": 2.48}

def compute_costs(df_input):
    df_scenarios = pd.read_csv("../../run_sims/Assets/scenario_master_list.csv")
    df = pd.merge(df_input, df_scenarios, how="left", on="scenario_number")

    df["IPTsc_drug_unit_cost"] = 0
    df["IPTsc_drug_unit_cost"][df["drug_type"]=="ASAQ"] = cost_dict["ASAQ"]
    df["IPTsc_drug_unit_cost"][df["drug_type"]=="SPAQ"] = cost_dict["SPAQ"]
    df["IPTsc_drug_unit_cost"][df["drug_type"]=="DP"] = cost_dict["DP"]
    df["IPTsc_drug_unit_cost"][df["drug_type"]=="None"] = 0

    # IPTsc overhead costs.
    # Low = $0.20 per child per YEAR
    df["IPTsc_overhead_cost_low"] = 0
    df["IPTsc_overhead_cost_low"][df["screen_type"]!="IPT"] = df["iptsc_drugs_used"]/2 * 0.2
    df["IPTsc_overhead_cost_low"][df["screen_type"]!="IST"] = df["iptsc_rdts_used"]/2 * 0.2
    # High = $0.74 per child per CAMPAIGN
    df["num_IPTsc_campaigns"] = 0
    df["num_IPTsc_campaigns"][df["interval"]=="term"] = 3*2
    df["num_IPTsc_campaigns"][df["interval"]=="month"] = 12*2





if __name__=="__main__":
    df = pd.read_csv("sim_data_full_220708.csv")
    compute_costs(df)