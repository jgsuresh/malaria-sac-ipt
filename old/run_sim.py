from emodpy.bamboo import get_model_files
from emodpy.emod_task import EMODTask
from emodpy.utils import EradicationBambooBuilds
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform

import manifest
import params

from idmtools.entities.experiment import Experiment
from interventions import build_campaign_with_standard_events
from setup_sim import build_project_config
from sweeps import update_sim_random_seed

platform = Platform("SLURM")

print("Creating EMODTask (from files)...")


# Run setup:
archetype = "Southern"





def build_demographics():
    import emod_api.demographics.Demographics as Demographics
    demo = Demographics.from_file(manifest.demographics_file_path[archetype])
    return demo


def create_and_submit_experiment():

    task = EMODTask.from_default2(
        config_path="config.json",
        eradication_path=manifest.eradication_path,
        campaign_builder=build_campaign_with_standard_events,
        schema_path=manifest.schema_file,
        param_custom_cb=build_project_config,
        ep4_custom_cb=None,
        demog_builder=build_demographics,
        plugin_report=None # custom reports
    )

    # Create simulation sweep with builder
    builder = SimulationBuilder()
    builder.add_sweep_definition(update_sim_random_seed, range(3))
    # builder.add_sweep_definition()

    # to run a single sim without sweep: https://docs.idmod.org/projects/idmtools/en/latest/cookbook/experiments.html

    # create experiment from builder
    print( f"Prompting for COMPS creds if necessary..." )
    experiment = Experiment.from_builder(builder, task, name=params.exp_name)

    #other_assets = AssetCollection.from_id(pl.run())
    #experiment.assets.add_assets(other_assets)

    # The last step is to call run() on the ExperimentManager to run the simulations.
    experiment.run(wait_until_done=True, platform=platform)



    # Check result
    if not experiment.succeeded:
        print(f"Experiment {experiment.uid} failed.\n")
        exit()

    print(f"Experiment {experiment.uid} succeeded.")



if __name__ == "__main__":



    # TBD: user should be allowed to specify (override default) erad_path and input_path from command line
    plan = EradicationBambooBuilds.MALARIA_LINUX
    # plan = EradicationBambooBuilds.MALARIA_WIN
    print("Retrieving Eradication and schema.json from Bamboo...")
    get_model_files(plan, manifest)
    print("...done.")
    create_and_submit_experiment()
