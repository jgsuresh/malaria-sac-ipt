import itertools
import pathlib
from functools import partial

from emodpy.emod_task import EMODTask
from emodpy.utils import EradicationBambooBuilds
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment

from run_sims import manifest
from run_sims.build_config import set_full_config
from run_sims.other import include_post_processing
from run_sims.reports import add_testing_reports, add_scenario_reports
from run_sims.sweeps import set_run_number, master_sweep_for_core_scenarios, master_sweep_for_smc_drug_param_test


def create_and_submit_experiment():
    # ========================================================
    experiment_name = "IPTsc - ASAQ comparison"

    # parameters to sweep over:
    archetypes = ["Southern"]
    baseline_eirs = [1,3,10,30,100]
    # AQ:
    # 1: old AQ (Kamal)
    # 2: AQ_for_AS_combo (Kamal)
    # 3: Erin AQ
    # 4: Annie AQ - similar to #2 but not identical
    # AQ_configs = [1,2,3,4]
    number_of_seeds = 25

    platform = Platform("Calculon", num_cores=1, node_group="idm_abcd", priority="Normal")
    # platform = Platform("Calculon", num_cores=1, node_group="idm_48cores", priority="Highest")

    # =========================================================

    build_config = partial(set_full_config, is_burnin=False)

    print("Creating EMODTask (from files)...")
    task = EMODTask.from_default2(
        config_path="config.json",
        eradication_path=manifest.eradication_path,
        campaign_builder=None,
        schema_path=manifest.schema_file,
        param_custom_cb=build_config,
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

    sweep_values = list(itertools.product(baseline_eirs, AQ_configs))
    builder.add_sweep_definition(master_sweep_for_smc_drug_param_test, sweep_values)

    builder.add_sweep_definition(set_run_number, range(number_of_seeds))

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
