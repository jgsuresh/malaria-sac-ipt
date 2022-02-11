import itertools
import pathlib
from functools import partial

import numpy as np
from emodpy.bamboo import get_model_files
from emodpy.emod_task import EMODTask
from emodpy.utils import EradicationBambooBuilds
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment

from run_sims import manifest
from run_sims.build_config import set_full_config
from run_sims.other import build_demographics_from_file, include_post_processing
from run_sims.reports import add_burnin_reports
from run_sims.sweeps import set_run_number, archetype_and_habitat_sweep, archetype_and_habitat_sweep_for_burnins


def create_and_submit_experiment():
    # ========================================================
    experiment_name = "test_sim"

    # parameters to sweep over:
    archetypes = ["Eastern", "Southern"]
    larval_habitat_scales = np.array([8.9,9.0])
    number_of_seeds = 1

    # platform = Platform("Calculon", num_cores=1, node_group="idm_abcd", priority="Lowest")
    platform = Platform("Calculon", num_cores=1, node_group="idm_48cores", priority="Highest")

    # =========================================================

    build_config = partial(set_full_config, is_burnin=True)
    # build_demographics = partial(build_demographics_from_file, archetype=archetype)

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

    add_burnin_reports(task, include_inset=True)


    # Create simulation sweep with builder
    builder = SimulationBuilder()
    builder.add_sweep_definition(archetype_and_habitat_sweep_for_burnins, list(itertools.product(archetypes, larval_habitat_scales)))
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
    print("Retrieving Eradication and schema.json packaged with emod-malaria...")
    import emod_malaria.bootstrap as emod_malaria_bootstrap
    emod_malaria_bootstrap.setup(pathlib.Path(manifest.eradication_path).parent)
    print("...done.")


    create_and_submit_experiment()
