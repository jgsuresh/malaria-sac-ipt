import os
import pandas as pd
# import numpy as np

def application(output_folder="output"):
    print("starting dtk post process!")
    df = pd.DataFrame({"a": [1,2], "b": [3,4]})
    df.to_csv(os.path.join(output_folder, "test.csv"))
    # df = pd.read_csv(os.path.join(output_folder, "ReportEventRecorder_MTAT.csv"))
    #
    # symptomatic = df[np.logical_and(df["Infected"]==1, df["HasClinicalSymptoms"]=="T")].reset_index(drop=True)
    # asymptomatic = df[np.logical_and(df["Infected"]==1, df["HasClinicalSymptoms"]=="F")].reset_index(drop=True)
    #
    # sim_data = {
    #     "total_symptomatic_days": len(symptomatic),
    #     "total_asymptomatic_days": len(asymptomatic),
    #     "total_symptomatic_infectiousness": np.sum(symptomatic["Infectiousness"]),
    #     "total_asymptomatic_infectiousness": np.sum(asymptomatic["Infectiousness"])
    # }
    #
    # sim_data["proportion_time_asymptomatic"] = df["total_asymptomatic_days"]/(df["total_asymptomatic_days"] + df["total_symptomatic_days"])
    # sim_data["proportion_infectiousness_asymptomatic"] = df["total_asymptomatic_infectiousness"]/(df["total_asymptomatic_infectiousness"] + df["total_symptomatic_infectiousness"])
    #
    # save_df = pd.DataFrame(sim_data, index=[0])
    # save_df.to_csv("test.csv", index=False)

# with open(os.path,join(output_folder, "ReportEventRecorder_MTAT.csv"), 'r')

if __name__ == "__main__":
    application(output_folder="output")