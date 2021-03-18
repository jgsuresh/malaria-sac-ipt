from emodpy_malaria.config import set_team_defaults, set_species, get_species_params
from emod_api.config import default_from_schema_no_validation
import emodpy_malaria.config as emodpy_malaria_config_module

from jsuresh_helpers.running_dtk import set_executable, add_params_csv_to_dtk_config_builder
from jsuresh_helpers.uncategorized import load_csv_into_dictionary
from jsuresh_helpers.windows_filesystem import get_dropbox_location

import manifest

dropbox_folder = get_dropbox_location()
input_folder = dropbox_folder + "projects/jsuresh_sim_examples/example_input_folder/"
# bin_folder = input_folder + "bin"
params_csv_filename = input_folder + "params.csv"


def set_ento(config):
    set_species(config, ["arabiensis", "funestus"])

    # Set up larval habitats:
    lhm = default_from_schema_no_validation.schema_to_config_subnode(manifest.schema_file, ["idmTypes","idmType:VectorHabitat"])
    lhm.parameters.Vector_Habitat_Type = "LINEAR_SPLINE"
    lhm.parameters.Max_Larval_Capacity = 1e9
    lhm.parameters.Capacity_Distribution_Number_Of_Years = 1
    lhm.parameters.Capacity_Distribution_Over_Time.Times = [0.0, 30.4, 60.8, 91.3, 121.7, 152.1,
                                                            182.5, 212.9, 243.3, 273.8, 304.2, 334.6]
    lhm.parameters.Capacity_Distribution_Over_Time.Values = [0.6, 0.8, 1.0, 0.9, 0.1, 0.01,
                                                             0.01, 0.01, 0.01, 0.01, 0.02, 0.05]
    # lhm.parameters.finalize()
    emodpy_malaria_config_module.get_species_params(config, "arabiensis").Larval_Habitat_Types.append(lhm.parameters)


    lhm = default_from_schema_no_validation.schema_to_config_subnode(manifest.schema_file, ["idmTypes","idmType:VectorHabitat"])
    lhm.parameters.Vector_Habitat_Type = "LINEAR_SPLINE"
    lhm.parameters.Max_Larval_Capacity = 1e9
    lhm.parameters.Capacity_Distribution_Number_Of_Years = 1
    lhm.parameters.Capacity_Distribution_Over_Time.Times = [0.0, 30.4, 60.8, 91.3, 121.7, 152.1,
                                                            182.5, 212.9, 243.3, 273.8, 304.2, 334.6]
    lhm.parameters.Capacity_Distribution_Over_Time.Values = [0.133, 0.333, 1., 0.667, 0.667, 0.667,
                                                             0.333, 0.333, 0.2, 0.133, 0.0667, 0.0667]
    # lhm.parameters.finalize()
    emodpy_malaria_config_module.get_species_params(config, "funestus").Larval_Habitat_Types.append(lhm.parameters)




    # set_species_param #fixme Asking Jonathan to make this function for me

    '''

    set_species_param(cb, 'arabiensis', 'Indoor_Feeding_Fraction', 0.5)
    set_species_param(cb, 'arabiensis', 'Adult_Life_Expectancy', 20)
    set_species_param(cb, 'arabiensis', 'Anthropophily', 0.65)
    set_species_param(cb, 'arabiensis', 'Vector_Sugar_Feeding_Frequency', "VECTOR_SUGAR_FEEDING_NONE")

    set_species_param(cb, 'funestus', "Indoor_Feeding_Fraction", 0.9)
    set_species_param(cb, 'funestus', 'Adult_Life_Expectancy', 20)
    set_species_param(cb, 'funestus', 'Anthropophily', 0.65)
    set_species_param(cb, 'funestus', 'Vector_Sugar_Feeding_Frequency', "VECTOR_SUGAR_FEEDING_NONE")
    '''


def set_log_level(config, loglevel_default="WARNING"):
    # non-schema parameters:
    config.parameters["logLevel_default"] = loglevel_default,
    config.parameters["logLevel_JsonConfigurable"] = "WARNING"
    config.parameters["Enable_Log_Throttling"] = 1

    #schema parameters:
    config.parameters.Memory_Usage_Warning_Threshold_Working_Set_MB = 50000
    config.parameters.Memory_Usage_Halting_Threshold_Working_Set_MB = 60000

    return config

def set_project_specific_params(config):
    config.parameters.Age_Initialization_Distribution_Type = "DISTRIBUTION_SIMPLE"

    config.parameters.Climate_Model = "CLIMATE_CONSTANT"
    # config.parameters.Air_Temperature_Filename

    config.parameters.Simulation_Duration = 365
    # config.parameters.Climate_Model = "CLIMATE_BY_DATA"

    bednet_individual_events = ["Bednet_Got_New_One", "Bednet_Using", "Bednet_Discarded"]
    config.parameters.Custom_Individual_Events = list(config.parameters.Custom_Individual_Events) + bednet_individual_events

    set_ento(config)
    # set_log_level(config)


def build_project_config(config):

    config.parameters.Simulation_Type = "MALARIA_SIM"
    # malaria sim defaults
    set_team_defaults(config, manifest)

    # IP white list (non-schema)
    config.parameters["Disable_IP_Whitelist"] = 1

    # project params
    set_project_specific_params(config)

    return config
