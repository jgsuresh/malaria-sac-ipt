import itertools
import pathlib
from functools import partial

from emodpy.emod_task import EMODTask
from emodpy.utils import EradicationBambooBuilds
from emodpy_malaria.malaria_config import set_team_defaults
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment

from run_sims import manifest
from run_sims.build_config import set_full_config
from run_sims.other import include_post_processing
from run_sims.reports import add_testing_reports, add_scenario_reports
from run_sims.sweeps import set_run_number, master_sweep_for_core_scenarios


def create_and_submit_experiment():
    # ========================================================
    experiment_name = "ITN test"

    platform = Platform("Calculon", num_cores=1, node_group="idm_48cores", priority="Highest")

    def _build_config(config):
        config.parameters.Simulation_Type = "MALARIA_SIM"
        set_team_defaults(config, manifest)
        config.parameters.Simulation_Duration = 2 * 365
        return config

    print("Creating EMODTask (from files)...")
    task = EMODTask.from_default2(
        config_path="config.json",
        eradication_path=manifest.eradication_path,
        campaign_builder=None,
        schema_path=manifest.schema_file,
        param_custom_cb=_build_config,
        demog_builder=None,
        ep4_custom_cb=include_post_processing
    )

    print("Adding asset dir...")
    task.common_assets.add_directory(assets_directory=manifest.assets_input_dir)
    task.set_sif(manifest.sif)
    # add_testing_reports(task)
    add_scenario_reports(task)

    # Create simulation sweep with builder
    builder = SimulationBuilder()

    builder.add_sweep_definition(set_run_number, range(start_seed, number_of_seeds+start_seed))

    # create experiment from builder
    print("Prompting for COMPS creds if necessary...")
    experiment = Experiment.from_builder(builder, task, name=experiment_name)
    experiment.run(wait_until_done=True, platform=platform)

    # Check result
    if not experiment.succeeded:
        print(f"Experiment {experiment.uid} failed.\n")
        exit()

    print(f"Experiment {experiment.uid} succeeded.")



if __name__ == "__main__":
    plan = EradicationBambooBuilds.MALARIA_LINUX

    # Download latest Eradication
    # print("Retrieving Eradication and schema.json packaged with emod-malaria...")
    # import emod_malaria.bootstrap as emod_malaria_bootstrap
    # emod_malaria_bootstrap.setup(pathlib.Path(manifest.eradication_path).parent)
    # print("...done.")

    create_and_submit_experiment()
