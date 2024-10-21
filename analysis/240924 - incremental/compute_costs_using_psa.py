import numpy as np
import pandas as pd

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

def compute_cost_ranges(df):
    # Add cost columns:
    df["cost_IPTsc_overhead_low"] = 0
    df["cost_IPTsc_overhead_high"] = 0
    df["cost_IPTsc_consumables"] = 0
    df["cost_IPTsc_drugs"] = 0
    df["cost_IPTsc_RDTs"] = 0

    # ####################
    # School-based IPTsc #
    # ####################

    df_school = df.loc[df["delivery_mode"]=="school"]
    IPT = df_school["screen_type"]=="IPT"
    IST = df_school["screen_type"]=="IST"

    # Commodity costs:
    df_school.loc[IST, "cost_IPTsc_RDTs"] = df_school.loc[IST, "iptsc_rdts_used"] * cost_dict["RDT"]
    df_school["cost_IPTsc_drugs"] = df_school["iptsc_drugs_used_school"] * df_school["drug_type"].map(cost_dict)
    df_school["cost_IPTsc_consumables"] = df_school["cost_IPTsc_RDTs"] + df_school["cost_IPTsc_drugs"]

    # overhead costs.
    # Low = $0.20 per child per YEAR.
    # (Assume that number per YEAR is calculated as average number seen in each campaign)
    cost_schoolbased_overhead_low_per_child_per_year = 0.27 # Brooker et al. 2008, adjusted to 2022: $0.2*294.4/215.3

    df_school["num_school_campaigns"] = 0
    df_school.loc[df_school["campaign_timing"]=="term", "num_school_campaigns"] = 3*2 # 3 terms per year for each archetype
    # Number of campaigns for monthly school-based campaigns is different based on archetype's school calendar
    df_school.loc[df_school["campaign_timing"] == "month", "num_school_campaigns"] = df_school["archetype"].map({"Southern": 12, "Central": 11, "Sahel": 9}) * 2

    df_school["num_schoolchildren_reached_per_year"] = 0
    df_school.loc[IPT, "num_schoolchildren_reached_per_year"] = df_school.loc[IPT, "iptsc_drugs_used_school"]/df_school.loc[IPT, "num_school_campaigns"]
    df_school.loc[IST, "num_schoolchildren_reached_per_year"] = df_school.loc[IST, "iptsc_rdts_used"] /df_school.loc[IST, "num_school_campaigns"]

    df_school["cost_IPTsc_overhead_low"] = df_school["num_schoolchildren_reached_per_year"] * 2 * cost_schoolbased_overhead_low_per_child_per_year


    # High = $0.74 per child per CAMPAIGN
    cost_schoolbased_overhead_high_per_child_per_campaign = 0.74
    df_school["cost_IPTsc_overhead_high"] = 0
    df_school.loc[IPT, "cost_IPTsc_overhead_high"] = df_school.loc[IPT, "iptsc_drugs_used_school"] * cost_schoolbased_overhead_high_per_child_per_campaign
    df_school.loc[IST, "cost_IPTsc_overhead_high"] = df_school.loc[IST, "iptsc_rdts_used"] * cost_schoolbased_overhead_high_per_child_per_campaign


    df.loc[df["delivery_mode"]=="school"] = df_school

    # # ####################################
    # # Mass-campaign IPTsc (extended SMC) #
    # # ####################################
    df_esmc = df.loc[np.in1d(df["delivery_mode"], ["smc_u10", "smc_u15"])]

    # Commodity costs:
    df_esmc["cost_IPTsc_drugs"] = (df_esmc["received_smc_5-10"] + df_esmc["received_smc_10-15"]) * df_esmc["drug_type"].map(cost_dict)
    df_esmc["cost_IPTsc_consumables"] = df_esmc["cost_IPTsc_drugs"]

    # overhead costs.
    df_esmc["cost_IPTsc_overhead_low"] = 0

    pessimistic_SMC_overhead_per_person_per_season = cost_dict["SMC_per_person_per_season_high"] - 4*cost_dict["SPAQ"]
    num_SAC_receiving_SMC_per_season = ((df["received_smc_5-10"] + df["received_smc_10-15"])/4)/2  # 4 rounds per year, 2 years in sim
    df_esmc["cost_IPTsc_overhead_high"] = num_SAC_receiving_SMC_per_season * pessimistic_SMC_overhead_per_person_per_season * 2

    df.loc[np.in1d(df["delivery_mode"], ["smc_u10", "smc_u15"])] = df_esmc

    # Summary:
    df["cost_IPTsc_low"] = df["cost_IPTsc_consumables"] + df["cost_IPTsc_overhead_low"]
    df["cost_IPTsc_high"] = df["cost_IPTsc_consumables"] + df["cost_IPTsc_overhead_high"]
    df["cost_IPTsc_mean"] = (df["cost_IPTsc_low"] + df["cost_IPTsc_high"])/2.


    # Non-IPTsc costs
    num_u5_receiving_SMC_per_season = (df["received_smc_u5"]/4)/2
    df["cost_SMC_u5_low"] = num_u5_receiving_SMC_per_season * cost_dict["SMC_per_person_per_season_low"] * 2
    df["cost_SMC_u5_high"] = num_u5_receiving_SMC_per_season * cost_dict["SMC_per_person_per_season_high"] * 2
    df["cost_SMC_u5_mean"] = (df["cost_SMC_u5_low"]+df["cost_SMC_u5_high"])/2.

    df["cost_facility_low"] = df["cases_treated"] * (cost_dict["facility_treatment_low"] + cost_dict["RDT"] + cost_dict["AL"])
    df["cost_facility_high"] = df["cases_treated"] * (cost_dict["facility_treatment_high"] + cost_dict["RDT"] + cost_dict["AL"])
    # df["cost_facility"] = df["cases_treated"] * (cost_dict["facility_treatment_mean"] + cost_dict["RDT"] + cost_dict["AL"])
    df["cost_severe"] = df["severe_cases_treated"] * cost_dict["severe"]
    df["cost_ITNs"] = df["itn_coverage"].apply(lambda x: 3500 if x==0.7 else 4500) * cost_dict["ITN"]
    df["cost_ivermectin"] = df["received_ivermectin"] * cost_dict["Ivermectin"]
    df["cost_primaquine"] = df["received_primaquine"] * cost_dict["Primaquine"]


    # Summary
    df["cost_low"] = df["cost_IPTsc_low"] + df["cost_facility_low"] + df["cost_severe"] + \
                      df["cost_ITNs"] + df["cost_SMC_u5_low"] + df["cost_ivermectin"] + df["cost_primaquine"]

    df["cost_high"] = df["cost_IPTsc_high"] + df["cost_facility_high"] + df["cost_severe"] + \
                      df["cost_ITNs"] + df["cost_SMC_u5_high"] + df["cost_ivermectin"] + df["cost_primaquine"]

    df["cost_mean"] = (df["cost_low"] + df["cost_high"])/2.

if __name__ == "__main__":
    df = pd.read_csv("sim_data_raw.csv")

    compute_cost_ranges(df)
    df.to_csv("sim_data_raw_with_cost_ranges.csv", index=False)

    # pass
    # df.to_csv("sim_data_full_with_costs.csv", index=False)