from copy import copy

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
    def __init__(self, exp_id=None):
        filenames = ["output/full_sim_data.json", "output/endpoint_data.json"]
        super().__init__(filenames=filenames)
        self.exp_id = exp_id

    def map(self, data, simulation):
        sim_data = copy(data[self.filenames[0]])
        sim_data.update(data[self.filenames[1]])

        # Add sim metadata
        sim_data["sim_id"] = simulation.id
        for tag in simulation.tags:
            if tag == "task_type":
                pass
            else:
                sim_data[tag] = simulation.tags[tag]

        return sim_data

    def combine(self, all_data):
        data_list = list(all_data.values())
        return pd.DataFrame(data_list)#.reset_index(drop=True)

    def reduce(self, all_data):
        sim_data_full = self.combine(all_data)
        sim_data_full.sort_values(by=["archetype",
                                      "scenario_number",
                                      "baseline_transmission_metric",
                                      "transmission_level",
                                      "Run_Number"], ignore_index=True, inplace=True)
        sim_data_full.to_csv(f"sim_data_{self.exp_id}.csv", index=False)
        return sim_data_full


if __name__ == "__main__":
    # experiment_id = "98932d94-bf3d-ed11-a9fc-b88303911bc1" #Sahel - by pfpr (updated ITN timing)
    experiment_id = "219c1f57-7e3f-ed11-a9fc-b88303911bc1" #Sahel - extra scenarios - by pfpr
    # experiment_id = "c85adb8e-873b-ed11-a9fc-b88303911bc1" #Southern and Central - by pfpr
    # experiment_id = "e330e3fd-a83e-ed11-a9fc-b88303911bc1" #Southern and Central - extra scenarios - by pfpr

    # experiment_id = "b47f29f2-c13d-ed11-a9fc-b88303911bc1" #Sahel - by eir
    # experiment_id = "b2759556-853b-ed11-a9fc-b88303911bc1" #Southern and Central - by eir
    run_analyzer_as_ssmt(experiment_id=experiment_id,
                         analyzers=[DownloadData],
                         analyzer_args=[{"exp_id": experiment_id}])
    # run_analyzer_locally(experiment_id, [DownloadData], analyzer_args=[{}])
