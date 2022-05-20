from copy import copy

import numpy as np
import pandas as pd
from idmtools.analysis.platform_anaylsis import PlatformAnalysis
from idmtools.core.platform_factory import Platform
from idmtools.entities import IAnalyzer
from idmtools_platform_comps.utils.download.download import DownloadWorkItem

# from jsuresh_helpers.analyzers.run_analyzer import run_analyzer_locally

def run_analyzer_as_ssmt(experiment_id,
                         analyzers,
                         analyzer_args,
                         analysis_name="SSMT analysis"):
    platform = Platform("SLURM")
    analysis = PlatformAnalysis(
        platform=platform,
        experiment_ids=[experiment_id],
        analyzers=analyzers,
        analyzers_args=analyzer_args,
        analysis_name=analysis_name,
    )
    analysis.analyze(check_status=True)
    wi = analysis.get_work_item()
    print(wi)

    # Download the actual output (code snippet from Clinton 1/3/22)
    dl_wi = DownloadWorkItem(related_work_items=[wi.id],
                             file_patterns=["*.csv"],
                             delete_after_download=False,
                             extract_after_download=True,
                             verbose=True)
    dl_wi.run(wait_on_done=True, platform=platform)


class DownloadData(IAnalyzer):
    def __init__(self):
        filenames = ["output/InsetChart.json"]
        super().__init__(filenames=filenames)

    def filter(self, simulation):
        if int(simulation.tags["scenario_number"]) in [13,22,30]:
            return True
        else:
            return False

    def map(self, data, simulation):

        sim_data = pd.DataFrame({
            "true_prev": np.array(data[self.filenames[0]]["Channels"]["True Prevalence"]["Data"]),
            "rdt_prev": np.array(data[self.filenames[0]]["Channels"]["PfHRP2 Prevalence"]["Data"]),
            "new_cases": np.array(data[self.filenames[0]]["Channels"]["New Clinical Cases"]["Data"])
        })

        sim_data["days"] = np.arange(len(sim_data))

        # Add sim metadata
        # sim_data["sim_id"] = simulation.id
        for tag in simulation.tags:
            if tag == "task_type":
                pass
            elif tag == "scenario_number":
                sim_data[tag] = int(simulation.tags[tag])
            else:
                sim_data[tag] = simulation.tags[tag]

        return sim_data

    def combine(self, all_data):
        data_list = []
        for sim in all_data.keys():
            data_list.append(all_data[sim])

        return pd.concat(data_list).reset_index(drop=True)

    def reduce(self, all_data):
        sim_data_full = self.combine(all_data)
        sim_data_full.sort_values(by=["archetype", "baseline_eir", "scenario_number", "Run_Number"], ignore_index=True, inplace=True)
        sim_data_full.to_csv("sim_data.csv", index=False)
        return sim_data_full


if __name__ == "__main__":
    # experiment_id = "1bf26942-aecc-ec11-a9f8-b88303911bc1"
    experiment_id = "e17e6275-aecc-ec11-a9f8-b88303911bc1"
    run_analyzer_as_ssmt(experiment_id=experiment_id,
                         analyzers=[DownloadData],
                         analyzer_args=[{}])
    # run_analyzer_locally(experiment_id, [DownloadData], analyzer_args=[{}])
