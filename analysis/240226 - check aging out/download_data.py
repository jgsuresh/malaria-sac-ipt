from copy import copy

import pandas as pd
from idmtools.analysis.platform_anaylsis import PlatformAnalysis
from idmtools.core.platform_factory import Platform
from idmtools.entities import IAnalyzer
from idmtools_platform_comps.utils.download.download import DownloadWorkItem


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


class DownloadSummaryData(IAnalyzer):
    def __init__(self, exp_id=None):
        filenames = ["output/MalariaSummaryReport.json"]
        super().__init__(filenames=filenames)
        self.exp_id = exp_id

    def map(self, data, simulation):
        sim_data = pd.DataFrame(
            {"annual_clinical_incidence_by_age": data[self.filenames[0]]["DataByTimeAndAgeBins"]["Annual Clinical Incidence by Age Bin"][17],
             "age": list(range(120))})

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
        return pd.concat(data_list).reset_index(drop=True)

    def reduce(self, all_data):
        sim_data_full = self.combine(all_data)
        sim_data_full.sort_values(by=["archetype",
                                      "iptsc_on",
                                      "baseline_transmission_metric",
                                      "transmission_level",
                                      "Run_Number"], ignore_index=True, inplace=True)
        sim_data_full.to_csv(f"sim_data_{self.exp_id}.csv", index=False)
        return sim_data_full


if __name__ == "__main__":
    experiment_id = "dfc5a1e8-e0d1-ee11-aa11-b88303911bc1"

    run_analyzer_as_ssmt(experiment_id=experiment_id,
                         analyzers=[DownloadSummaryData],
                         analyzer_args=[{"exp_id": experiment_id}])