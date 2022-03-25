import os.path

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

sns.set_context("talk")

from jsuresh_helpers.analyzers.create_sim_map import get_sim_map
from jsuresh_helpers.burnins.run_ssmt_sharon_hack import run_burnin_endpoint_ssmt
from jsuresh_helpers.binning_and_smoothing import fit_lowess_spline


# Mostly copied from jsuresh-idm-helpers/jsuresh-helpers/burnins/burnins.py
# NOTE this file is mostly deprecated, and the functionality now copied to the notebooks in burnin_selection/

# Assume burnin experiment may have multiple archetypes in same sweep.
def find_representative_of_burnin_sweep(experiment_id):
    run_burnin_endpoint_ssmt(experiment_id)
    survey_burnin_sweep(experiment_id)


def _add_smoothed_values(df_burnin, columns_of_interest):
    df_burnin.sort_values(by=["archetype", "Run_Number"], inplace=True, ignore_index=True)

    df_list = []
    for i, sdf in df_burnin.groupby("archetype"):
        for c in columns_of_interest:
            x = sdf["habitat_scale"]
            y = sdf[c]
            xs, ys = fit_lowess_spline(x, y, frac=0.3)

            # Find any negative values and replace them with mean of actual burnin:
            needs_correction = ys < 0
            corrected = np.mean(y[needs_correction])
            ys[needs_correction] = corrected

            sdf[c + "_SMOOTHED"] = ys

            df_list.append(sdf)

    new_df = pd.concat(df_list, ignore_index=True)
    return new_df



def _plot_data(df_burnin, min_dist_df, columns_of_interest):
    # Plot burnins:
    plt.close('all')
    plt.figure(figsize=(10, 10), dpi=300)

    for i, sdf in df_burnin.groupby("archetype"):
        archetype = i[0]
        x = sdf["habitat_scale"]


        i = 1
        for c in columns_of_interest:
            y = df_burnin[c]
            ys = df_burnin[c + "_SMOOTHED"]

            plt.subplot(3, 2, i)
            plt.scatter(x, y, zorder=0)
            plt.plot(x, ys, c="C1", zorder=1)

            x_selected = min_dist_df["habitat_scale"]
            y_selected = min_dist_df[c]
            plt.scatter(x_selected, y_selected, marker='*', zorder=2)

            plt.ylabel(c)
            plt.xlabel("habitat_scale")

            i += 1

        plt.tight_layout()
        # plt.show()
        plt.savefig(f"burnin_endpoints_{archetype}.png")



def _find_most_representative_burnins(df_burnin, columns_of_interest):
    df_list = []
    for i, sdf in df_burnin.groupby("archetype"):
        archetype = i[0]
        for c in columns_of_interest:
            y = sdf[c]
            ys = sdf[c + "_SMOOTHED"]

            # distance
            d = np.abs(y-ys)**2/ys**2
            sdf[c+ "_DISTANCE"] = d

        for i in range(len(columns_of_interest)):
            if i == 0:
                sdf["TOTAL_DISTANCE"] = sdf[columns_of_interest[i] + "_DISTANCE"]
            else:
                sdf["TOTAL_DISTANCE"] = sdf["TOTAL_DISTANCE"] + sdf[columns_of_interest[i] + "_DISTANCE"]


        # Loop over dataframe (bad?) and find smallest distance burnin for each value of the transmission tag
        dict_list = []
        for i, ssdf in df_burnin.groupby("habitat_scale"):
            min_dist_row_as_dict = dict(sdf.loc[sdf["TOTAL_DISTANCE"].idxmin()])
            dict_list.append(min_dist_row_as_dict.copy())

        min_dist_df = pd.DataFrame(dict_list)
        min_dist_df["archetype"] = archetype

        df_list.append(min_dist_df)

    min_dist_full_df = pd.concat(df_list, ignore_index=True)

    return min_dist_full_df


def _add_outpath_to_df(min_dist_df, experiment_id):
    # create sim map, and merge
    sim_map = get_sim_map(experiment_id)
    df_return = pd.merge(min_dist_df, sim_map[["sim_id", "outpath"]], how="left", on="sim_id")
    return df_return


def survey_burnin_sweep(experiment_id):
    # Output diagnostics of a sweep of burnins.
    # Use when you want to see how the burnins are sweeping across outputs like cases/EIR/immunity, and
    # identify most "representative" burnins for each transmission intensity level
    #
    # Pseudocode:
    # - Get endpoints from last few years of sims
    # - Calculate distance of each burnin from the "middle", as defined by input agg
    # - Save figures showing this information.


    if os.path.isfile("burnin_map.csv"):
        df_burnin = pd.read_csv("burnin_map.csv")
    else:
        print("Need burnin_map.csv")
        #fixme Run analyzer that outputs this:
        # run_analyzer_as_ssmt(experiment_id=experiment_id, analyzers=[SimEndpoint], analyzer_args=[{"save_file": "test.csv"}])

    columns_of_interest = ["aeir",
                           "annual_cases_per_1000",
                           "annual_rdt_prev",
                           "pfemp_frac",
                           "annual_reported_cases_per_1000"]

    df_burnin = _add_smoothed_values(df_burnin)
    min_dist_df = _find_most_representative_burnins(df_burnin)
    _plot_data(df_burnin, min_dist_df)

    # Finally, create CSV with output directory of most representative burnin for each transmission tag
    # df_save = _add_outpath_to_df(min_dist_df)
    # df_save = df_save[[transmission_tag, "outpath"]]
    df_final = _add_outpath_to_df(min_dist_df)
    smoothed_columns_of_interest = [x+"_SMOOTHED" for x in columns_of_interest]
    df_save = df_final[["habitat_scale", "outpath"] + smoothed_columns_of_interest]

    df_save.to_csv("burnin_outpaths.csv", index=False)



if __name__=="__main__":
    survey_burnin_sweep(experiment_id="9a81e628-2aa6-ec11-a9f5-9440c9be2c51")