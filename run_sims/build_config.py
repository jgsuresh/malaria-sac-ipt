# import emodpy_malaria.malaria_config as emodpy_malaria_sim_config_module
from emod_api.config import default_from_schema_no_validation
from emodpy import emod_task
from emodpy_malaria.malaria_config import set_team_defaults, add_species, set_species_param, get_species_params

from jsuresh_helpers.running_emodpy import set_log_level
from run_sims import manifest


def set_full_config(config, is_burnin):
    set_core_config_params(config)
    set_project_config_params(config)

    if is_burnin:
        config.parameters.Simulation_Duration = 20 * 365
        config.parameters.Serialized_Population_Writing_Type = "TIMESTEP"
        config.parameters.Serialization_Time_Steps = [20 * 365]
        config.parameters.Serialization_Precision = "REDUCED"
    else:
        config.parameters.Simulation_Duration = 2 * 365
        # Draw from serialized file here

    return config


def set_core_config_params(config):
    config.parameters.Simulation_Type = "MALARIA_SIM"
    set_team_defaults(config, manifest)

    # IP white list (non-schema)
    config.parameters["Disable_IP_Whitelist"] = 1


def set_project_config_params(config):
    config.parameters.Enable_Initial_Prevalence = 1

    config.parameters.Enable_Vital_Dynamics = 1
    config.parameters.Enable_Natural_Mortality = 1
    config.parameters.Enable_Demographics_Birth = 1
    config.parameters.Age_Initialization_Distribution_Type = "DISTRIBUTION_SIMPLE"

    config.parameters.Climate_Model = "CLIMATE_CONSTANT"
    config.parameters.Base_Air_Temperature = 27
    config.parameters.Base_Land_Temperature = 27

    set_log_level(config)
    # set_ento(config, archetype=archetype)


def set_archetype_ento(config, habitat_scale, archetype="Southern"):
    if archetype == "Southern":
        species_list = ["arabiensis", "funestus"]
    elif archetype == "Sahel":
        species_list = ["gambiae"]
    elif archetype == "Central":
        species_list = ["funestus", "gambiae"]
    elif archetype == "Eastern":
        species_list = ["arabiensis", "funestus", "gambiae"]
    elif archetype == "Coastal Western":
        species_list = ["arabiensis", "funestus", "gambiae"]
    elif archetype == "Magude":
        species_list = ["arabiensis", "funestus"]
    else:
        raise NotImplementedError

    for species in species_list:
        add_species(config, manifest, species)
        # Default values for almost all vector species
        set_species_param(config, species, "Adult_Life_Expectancy", 20)
        set_species_param(config, species, "Vector_Sugar_Feeding_Frequency", "VECTOR_SUGAR_FEEDING_NONE")
        set_species_param(config, species, "Anthropophily", 0.65)
        # Remove any habitats that are set by default
        set_species_param(config, species, "Habitats", [], overwrite=True)


    # Archetype-specific vector params:
    if archetype == "Southern":
        set_species_param(config, "arabiensis", "Indoor_Feeding_Fraction", 0.5)
        set_species_param(config, "funestus", "Indoor_Feeding_Fraction", 0.9)

    elif archetype == "Sahel":
        set_species_param(config, "gambiae", "Indoor_Feeding_Fraction", 0.9)

    elif archetype == "Central":
        set_species_param(config, "funestus", "Indoor_Feeding_Fraction", 0.5)

        set_species_param(config, "gambiae", "Indoor_Feeding_Fraction", 0.5)
        set_species_param(config, "gambiae", "Anthropophily", 0.85)

    elif archetype == "Eastern":
        set_species_param(config, "arabiensis", "Indoor_Feeding_Fraction", 0.5)

        set_species_param(config, "funestus", "Indoor_Feeding_Fraction", 0.7)  # Motivated by Uganda Vectorlink 2019

        set_species_param(config, "gambiae", "Indoor_Feeding_Fraction", 0.85)
        set_species_param(config, "gambiae", "Anthropophily", 0.85)

    elif archetype == "Coastal Western":
        set_species_param(config, "arabiensis", "Indoor_Feeding_Fraction", 0.5)
        
        set_species_param(config, "funestus", "Indoor_Feeding_Fraction", 0.85)
        
        set_species_param(config, "gambiae", "Indoor_Feeding_Fraction", 0.85)
        set_species_param(config, "gambiae", "Anthropophily", 0.8)  # Slightly tuned down - Nigeria Vectorlink 2019

    elif archetype == "Magude":
        set_species_param(config, "arabiensis", "Indoor_Feeding_Fraction", 0.95)
        set_species_param(config, "funestus", "Indoor_Feeding_Fraction", 0.6)

    set_archetype_ento_splines(config, archetype=archetype, habitat_scale=habitat_scale)


def set_linear_spline_habitat(config, species, log10_max_larval_capacity, capacity_distribution_over_time):
    lhm = default_from_schema_no_validation.schema_to_config_subnode(manifest.schema_file, ["idmTypes", "idmType:VectorHabitat"])
    lhm.parameters.Habitat_Type = "LINEAR_SPLINE"
    lhm.parameters.Max_Larval_Capacity = 10**log10_max_larval_capacity
    lhm.parameters.Capacity_Distribution_Number_Of_Years = 1
    lhm.parameters.Capacity_Distribution_Over_Time.Times = [0.0, 30.4, 60.8, 91.3, 121.7, 152.1,
                                                            182.5, 212.9, 243.3, 273.8, 304.2, 334.6]
    lhm.parameters.Capacity_Distribution_Over_Time.Values = capacity_distribution_over_time

    get_species_params(config, species).Habitats.append(lhm.parameters)


def set_nonspline_habitat(config, species, habitat_type, max_larval_capacity):
    lhm = default_from_schema_no_validation.schema_to_config_subnode(manifest.schema_file, ["idmTypes", "idmType:VectorHabitat"])
    lhm.parameters.Habitat_Type = habitat_type
    lhm.parameters.Max_Larval_Capacity = max_larval_capacity

    get_species_params(config, species).Habitats.append(lhm.parameters)


def set_archetype_ento_splines(config, archetype, habitat_scale):
    if archetype == "Southern":
        arab_scale = habitat_scale
        funest_scale = arab_scale - 0.8

        set_linear_spline_habitat(config, "arabiensis", habitat_scale,
                                  [0.6, 0.8, 1.0, 0.9, 0.1, 0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.05])
        set_nonspline_habitat(config, "arabiensis", "CONSTANT", 10**4.9)

        set_linear_spline_habitat(config, "funestus", funest_scale,
                                  [0.13, 0.33, 1., 0.67, 0.67, 0.67, 0.33, 0.33, 0.2, 0.13, 0.067, 0.067])
    elif archetype == "Sahel":
        set_linear_spline_habitat(config, "gambiae", habitat_scale,
                                  [0.086, 0.023, 0.034, 0.0029, 0.077, 0.23, 0.11, 1., 0.19, 0.19, 0.074,0.06])
    elif archetype == "Central":
        gamb_scale = habitat_scale
        funest_scale = gamb_scale - 1.03  # Calculated for funestus to be ~5% of all mosquitos

        set_linear_spline_habitat(config, "funestus", funest_scale,
                                  [0.87, 0.82, 0.85, 0.9, 0.95, 0.93, 0.89, 0.87, 0.87, 0.94, 1.0, 0.97])
        set_linear_spline_habitat(config, "gambiae", gamb_scale,
                                  [0.51, 0.42, 0.52, 0.66, 0.86, 0.92, 0.82, 0.75, 0.84, 0.99, 1.0, 0.77])

    elif archetype == "Eastern" or archetype == "Coastal Western":
        #fixme Why are Coastal Western and Eastern archetype identical... that can't be right?

        # Amelia's spline setup
        x_overall_amelia = 63.1

        set_nonspline_habitat(config, "arabiensis", "CONSTANT", 40000000 * x_overall_amelia)
        set_nonspline_habitat(config, "arabiensis", "TEMPORARY_RAINFALL", 360000000 * x_overall_amelia)
        set_linear_spline_habitat(config, "arabiensis", habitat_scale,
                                  [0.086, 0.023, 0.034, 0.0029, 0.077, 0.23, 0.11, 1., 0.19, 0.19, 0.074, 0.06])

        set_nonspline_habitat(config, "funestus", "WATER_VEGETATION", 400000000 * x_overall_amelia)
        set_linear_spline_habitat(config, "funestus", habitat_scale,
                                  [0.086, 0.023, 0.034, 0.0029, 0.077, 0.23, 0.11, 1., 0.19, 0.19, 0.074, 0.06])

        # gambiae is identical to arabiensis
        set_nonspline_habitat(config, "gambiae", "CONSTANT", 40000000 * x_overall_amelia)
        set_nonspline_habitat(config, "gambiae", "TEMPORARY_RAINFALL", 360000000 * x_overall_amelia)
        set_linear_spline_habitat(config, "gambiae", habitat_scale,
                                  [0.086, 0.023, 0.034, 0.0029, 0.077, 0.23, 0.11, 1., 0.19, 0.19, 0.074, 0.06])

    elif archetype == "Magude":
        arab_scale = habitat_scale
        funest_scale = arab_scale - 0.56

        set_linear_spline_habitat(config, "arabiensis", habitat_scale,
                                  [0.005, 0.119, 1.000, 0.069, 0.184, 0.203, 0.486, 0.157, 0.149, 0.185, 0.119, 0.011])
        set_nonspline_habitat(config, "arabiensis", "CONSTANT", 10**4.9)

        set_linear_spline_habitat(config, "funestus", funest_scale,
                                  [0.009, 0.438, 0.005, 0.088, 0.049, 1.000, 0.023, 0.170, 0.015, 0.008, 0.376, 0.193])

    else:
        raise NotImplementedError

    return {"hab_scale": habitat_scale}