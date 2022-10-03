import numpy as np
import pandas as pd
from idmtools.entities import IAnalyzer
from copy import copy

from idmtools.analysis.platform_anaylsis import PlatformAnalysis
from idmtools.core.platform_factory import Platform
from idmtools.entities import IAnalyzer
from idmtools_platform_comps.utils.download.download import DownloadWorkItem


def run_analyzer_as_ssmt(experiment_id,
                         analyzers,
                         analyzer_args,
                         analysis_name="SSMT analysis"):
    platform = Platform("SLURM")
    # platform = Platform("Belegost")
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




class SimEndpoint(IAnalyzer):
    def __init__(self,
                 experiment_id=None,
                 window_size=3*365,
                 only_keep_tags=None,
                 rdt_channel_as_hrp2=True
                 ):


        filenames = ['output/InsetChart.json', 'output/ReportEventCounter.json', 'output/MalariaSummaryReport.json']
        # filenames = ['output/InsetChart.json', 'output/ReportEventCounter.json', 'output/MalariaSummaryReport_AnnualAverage.json']

        super().__init__(filenames=filenames)

        self.experiment_id = experiment_id
        self.window_size = window_size
        self.only_keep_tags = only_keep_tags
        self.rdt_channel_as_hrp2 = rdt_channel_as_hrp2


    def map(self, data, simulation):
        sim_dict = {}

        # INSET
        inset_dict = data[self.filenames[0]]

        aeir = np.sum(inset_dict["Channels"]["Daily EIR"]["Data"][-self.window_size:])*365/self.window_size
        if self.rdt_channel_as_hrp2:
            annual_rdt_prev = np.mean(inset_dict["Channels"]["PfHRP2 Prevalence"]["Data"][-self.window_size:])
        else:
            annual_rdt_prev = np.mean(inset_dict["Channels"]["Blood Smear Parasite Prevalence"]["Data"][-self.window_size:])
        pfemp_frac = np.mean(inset_dict["Channels"]["Variant Fraction-PfEMP1 Major"]["Data"][-self.window_size:])
        pop = np.mean(inset_dict["Channels"]["Statistical Population"]["Data"][-self.window_size:])
        annual_cases_per_1000 = np.sum(inset_dict["Channels"]["New Clinical Cases"]["Data"][-self.window_size:])*365/self.window_size * 1000/pop

        sim_dict["aeir"] = aeir
        sim_dict["annual_cases_per_1000"] = annual_cases_per_1000
        sim_dict["annual_rdt_prev"] = annual_rdt_prev
        sim_dict["pfemp_frac"] = pfemp_frac

        # COUNTER
        counter_dict = data[self.filenames[1]]
        if "Received_Treatment" in counter_dict["Channels"]:
            annual_reported_cases_per_1000 = np.sum(counter_dict["Channels"]["Received_Treatment"]["Data"][-self.window_size:])*365/self.window_size * 1000/pop
            sim_dict["annual_reported_cases_per_1000"] = annual_reported_cases_per_1000

        # SUMMARY
        summary_dict = data[self.filenames[2]]
        sim_dict["pfpr_2-10"] = np.median([summary_dict['DataByTime']['PfPR_2to10'][-1],
                                           summary_dict['DataByTime']['PfPR_2to10'][-2],
                                           summary_dict['DataByTime']['PfPR_2to10'][-3]])

        # Prepare the sim data for returning
        sim_data = pd.DataFrame(sim_dict, index=[0])

        sim_data["sim_id"] = simulation.id
        if self.only_keep_tags is None:
            for tag in simulation.tags:
                sim_data[tag] = simulation.tags[tag]
        else:
            for tag in simulation.tags:
                if tag in self.only_keep_tags:
                    sim_data[tag] = simulation.tags[tag]

        return sim_data


    def combine(self, all_data):
        data_list = []
        for sim in all_data.keys():
            data_list.append(all_data[sim])

        if len(data_list) == 1:
            return data_list[0]

        return pd.concat(data_list, ignore_index=True).reset_index(drop=True)


    def reduce(self, all_data):
        sim_data_full = self.combine(all_data)
        sim_data_full.to_csv(f"burnin_endpoint_{self.experiment_id}.csv", index=False)
        return sim_data_full



if __name__ == "__main__":
    # experiment_id = "1a3f024e-9aab-ec11-a9f6-9440c9be2c51" # central - low eir
    # experiment_id = "b7e98361-9eb6-ec11-a9f6-9440c9be2c51" # central
    # experiment_id = "3d0554ac-2439-ed11-a9fc-b88303911bc1" # central - high pfpr
    # experiment_id = "d5d9cc48-9fb6-ec11-a9f6-9440c9be2c51" # sahel
    # experiment_id = "2842c80b-3439-ed11-a9fc-b88303911bc1" # sahel - low pfpr
    # experiment_id = "77cf7d50-9fb6-ec11-a9f6-9440c9be2c51" # southern
    # experiment_id = "8e46e3ff-e339-ed11-a9fc-b88303911bc1" # southern - high pfpr

    # experiment_id = "ae162b7e-1f8f-eb11-a2ce-c4346bcb1550" # southern - old
    experiment_id = "0dd75eef-9e3a-ed11-a9fc-b88303911bc1" # deep burnin rerun/sweep


    run_analyzer_as_ssmt(experiment_id=experiment_id,
                         analyzers=[SimEndpoint],
                         analyzer_args=[{"experiment_id": experiment_id}])
    # run_analyzer_locally(experiment_id, [DownloadData], analyzer_args=[{}])
