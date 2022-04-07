import itertools
import pathlib
from functools import partial

import numpy as np
from emodpy.emod_task import EMODTask
from emodpy.utils import EradicationBambooBuilds
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment

from run_sims import manifest
from run_sims.build_config import set_full_config
from run_sims.other import include_post_processing
from run_sims.sweeps import set_run_number, archetype_and_habitat_sweep_for_burnins


def create_and_submit_experiment():
    # ========================================================
    experiment_name = "IPTsc burnins_Central"

    # parameters to sweep over:
    # archetypes = ["Sahel", "Central", "Southern"]
    # larval_habitat_scales = np.array([8.0,8.1,8.2,8.3,8.4,8.5,8.6,8.7,8.8,8.9,9.0,9.1,9.2,9.3,9.4,9.5,9.6,9.7])
    # larval_habitat_scales = np.array([7.0,7.1,7.2,7.3,7.4,7.5,7.6,7.7,7.8,7.9])

    # archetypes = ["Sahel"]
    # larval_habitat_scales = np.array([8.33,8.67, 9.08, 9.55, 10.1]) #Sahel - targeting aEIR of 1,3,10,30,100
    # archetypes = ["Southern"]
    # larval_habitat_scales = np.array([7.73,8.08,8.47,8.93,9.47]) #Southern - targeting aEIR of 1,3,10,30,100
    archetypes = ["Central"]
    larval_habitat_scales = np.array([7.44,7.58,8.01,8.45,8.98]) #Central - targeting aEIR of 1,3,10,30,100
    number_of_seeds = 1

    # platform = Platform("Calculon", num_cores=1, node_group="idm_abcd", priority="Normal")
    platform = Platform("Calculon", num_cores=1, node_group="idm_48cores", priority="Highest")

    # =========================================================

    build_config = partial(set_full_config, is_burnin=True)

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
