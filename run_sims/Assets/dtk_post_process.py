import json
import os
import numpy as np
import pandas as pd


def event_counter_as_df(filepath):
    with open(filepath,'r') as f:
        d = json.load(f)
    return d


def get_annual_incidence_of_custom_agebin_from_summary(data_summary, age_min, age_max, year_index=0, incidence_type="clinical"):
    age_bins = np.array(data_summary['Metadata']['Age Bins'])
    pop = np.array(data_summary['DataByTimeAndAgeBins']['Average Population by Age Bin'][year_index])

    if incidence_type == "clinical":
        key = 'Annual Clinical Incidence by Age Bin'
    elif incidence_type == "severe":
        key = 'Annual Severe Incidence by Age Bin'
    else:
        raise ValueError

    incidence = np.array(data_summary['DataByTimeAndAgeBins'][key][year_index])

    age_cut = np.logical_and(age_bins > age_min, age_bins <= age_max)
    return float(np.sum(pop[age_cut]*incidence[age_cut])/np.sum(pop[age_cut]))


def get_pfpr_of_custom_agebin_from_summary(data_summary, age_min, age_max, year_index=0):
    age_bins = np.array(data_summary['Metadata']['Age Bins'])
    pop = np.array(data_summary['DataByTimeAndAgeBins']['Average Population by Age Bin'][year_index])
    pfpr = np.array(data_summary['DataByTimeAndAgeBins']['PfPR by Age Bin'][year_index])

    age_cut = np.logical_and(age_bins > age_min, age_bins <= age_max)
    return float(np.sum(pop[age_cut]*pfpr[age_cut])/np.sum(pop[age_cut]))


def get_pop_of_custom_agebin_from_summary(data_summary, age_min, age_max, year_index=0):
    age_bins = np.array(data_summary['Metadata']['Age Bins'])
    pop = np.array(data_summary['DataByTimeAndAgeBins']['Average Population by Age Bin'][year_index])

    age_cut = np.logical_and(age_bins > age_min, age_bins <= age_max)
    return float(np.sum(pop[age_cut]))


def get_marita_columns_from_summary(data_summary, year_index=0):
    # Get total pop, average age of pop, avg age of clinical and severe cases
    age_bins = np.array(data_summary['Metadata']['Age Bins'])
    pop_by_age_bin = np.array(data_summary['DataByTimeAndAgeBins']['Average Population by Age Bin'][year_index])
    total_pop = np.sum(pop_by_age_bin)
    avg_age = np.sum(age_bins*pop_by_age_bin)/total_pop

    #Note: this may be pretty misleading if any age bins are especially wide
    clinical_incidence_by_age_bin = data_summary['DataByTimeAndAgeBins']['Annual Clinical Incidence by Age Bin'][year_index]
    avg_age_clinical_cases = np.sum(clinical_incidence_by_age_bin*age_bins)/np.sum(clinical_incidence_by_age_bin)

    severe_incidence_by_age_bin = data_summary['DataByTimeAndAgeBins']['Annual Severe Incidence by Age Bin'][year_index]
    avg_age_severe_cases = np.sum(severe_incidence_by_age_bin*age_bins)/np.sum(severe_incidence_by_age_bin)


    return {"avg_age": float(avg_age),
            "avg_age_clinical_cases": float(avg_age_clinical_cases),
            "avg_age_severe_cases": float(avg_age_severe_cases)}


def application(output_folder="output"):
    print("starting dtk post process!")

    # For testing: create an output file
    # df = pd.DataFrame({"a": [1,2], "b": [3,4]})
    # df.to_csv(os.path.join(output_folder, "test.csv"))

    # Save summary output data of interest.

    # Count major events:
    event_recorder_filepath = os.path.join(output_folder, "ReportEventCounter.json")
    with open(event_recorder_filepath, 'r') as f:
        d = json.load(f)

    def _return_sum(event_name):
        if event_name in d["Channels"]:
            return int(np.array(d["Channels"][event_name]["Data"]).sum())
        else:
            return 0

    full_sim_data = {
        "iptsc_rdts_used": _return_sum("Received_Test"),
        "iptsc_drugs_used": _return_sum("Received_Campaign_Drugs"),
        "cases_treated": _return_sum("Received_Treatment"),
        "severe_cases_treated": _return_sum("NewSevereCase"),
        "received_smc": _return_sum("Received_SMC")
    }

    json.dump(full_sim_data, open(os.path.join(output_folder, "full_sim_data.json"), 'w'), indent=4)

    # =========================================================================================================
    # Get summary of last year of sim, by age

    summary_report_filepath = os.path.join(output_folder, "MalariaSummaryReport.json")
    with open(summary_report_filepath, "r") as f:
        data_summary = json.load(f)
        
    year_index = 1

    endpoint_data = {
        "pfpr0_5": get_pfpr_of_custom_agebin_from_summary(data_summary,0,6,year_index=year_index),
        "pfpr2_10": get_pfpr_of_custom_agebin_from_summary(data_summary,2,11,year_index=year_index),
        "pfpr6_15": get_pfpr_of_custom_agebin_from_summary(data_summary,6,16,year_index=year_index),
        "pfpr16_500": get_pfpr_of_custom_agebin_from_summary(data_summary,16,500,year_index=year_index),
        "pfpr_all": get_pfpr_of_custom_agebin_from_summary(data_summary,0,500,year_index=year_index),

        "clinical_incidence0_5": get_annual_incidence_of_custom_agebin_from_summary(data_summary,0,6,year_index=year_index, incidence_type="clinical"),
        "clinical_incidence2_10": get_annual_incidence_of_custom_agebin_from_summary(data_summary,2,11,year_index=year_index, incidence_type="clinical"),
        "clinical_incidence6_15": get_annual_incidence_of_custom_agebin_from_summary(data_summary,6,16,year_index=year_index, incidence_type="clinical"),
        "clinical_incidence16_500": get_annual_incidence_of_custom_agebin_from_summary(data_summary,16,500,year_index=year_index, incidence_type="clinical"),
        "clinical_incidence_all": get_annual_incidence_of_custom_agebin_from_summary(data_summary,0,500,year_index=year_index, incidence_type="clinical"),

        "severe_incidence0_5": get_annual_incidence_of_custom_agebin_from_summary(data_summary,0,6,year_index=year_index, incidence_type="severe"),
        "severe_incidence2_10": get_annual_incidence_of_custom_agebin_from_summary(data_summary,2,11,year_index=year_index, incidence_type="severe"),
        "severe_incidence6_15": get_annual_incidence_of_custom_agebin_from_summary(data_summary,6,16,year_index=year_index, incidence_type="severe"),
        "severe_incidence16_500": get_annual_incidence_of_custom_agebin_from_summary(data_summary,16,500,year_index=year_index, incidence_type="severe"),
        "severe_incidence_all": get_annual_incidence_of_custom_agebin_from_summary(data_summary,0,500,year_index=year_index, incidence_type="severe"),

        "pop0_5": get_pop_of_custom_agebin_from_summary(data_summary,0,6,year_index=year_index),
        "pop2_10": get_pop_of_custom_agebin_from_summary(data_summary,2,11,year_index=year_index),
        "pop6_15": get_pop_of_custom_agebin_from_summary(data_summary,6,16,year_index=year_index),
        "pop16_500": get_pop_of_custom_agebin_from_summary(data_summary,16,500,year_index=year_index),
        "pop_all": get_pop_of_custom_agebin_from_summary(data_summary,0,500,year_index=year_index)
    }

    endpoint_data.update(get_marita_columns_from_summary(data_summary, year_index=year_index))

    json.dump(endpoint_data, open(os.path.join(output_folder, "endpoint_data.json"), 'w'), indent=4)


if __name__ == "__main__":
    application(output_folder="output")