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
from run_sims.sweeps import set_run_number, master_sweep_for_core_scenarios


def create_and_submit_experiment():
    # ========================================================
    # experiment_name = "IPTsc core scenarios - Sahel - by eir - new ITN timing"
    # experiment_name = "IPTsc core scenarios - Southern and Central - by pfpr2"
    # experiment_name = "IPTsc core scenarios - TEST - events"
    # experiment_name = "IPTsc transmission-targeting - Southern and Central - pfpr"
    experiment_name = "IPTsc transmission-targeting - Sahel - pfpr"

    # parameters to sweep over:
    # archetypes = ["Sahel", "Central", "Southern"]
    archetypes = ["Sahel"]
    # archetypes = ["Southern", "Central"]
    # transmission_selection_type = "eir"
    # transmission_levels = [1,3,10,30,100]
    transmission_selection_type = "pfpr"
    transmission_levels = [0.01,0.05,0.1,0.2,0.3,0.4]

    # core_scenario_numbers = list(range(64)) # All scenarios for Sahel (more than other archetypes b/c of SMC)
    # core_scenario_numbers = list(range(56)) # All scenarios for Central and Southern
    # core_scenario_numbers = [56,57,58,59,60,61] # extra scenarios for Cent/South
    core_scenario_numbers = [64,65,66,67,68,69] # extra scenarios for Sahel

    number_of_seeds = 10
    # smc_drug_configs = ["default", "annie", "erin"]
    smc_drug_configs = ["annie"]

    platform = Platform("Calculon", num_cores=1, node_group="idm_abcd", priority="AboveNormal")
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

    scenario_sweep = partial(master_sweep_for_core_scenarios, baseline_transmission_metric=transmission_selection_type)
    sweep_values = list(itertools.product(archetypes, transmission_levels, core_scenario_numbers, smc_drug_configs))
    builder.add_sweep_definition(scenario_sweep, sweep_values)

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
