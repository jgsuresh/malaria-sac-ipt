from interventions import scenario_interventions


def update_sim_bic(simulation, value):
    simulation.task.config.parameters.Acquisition_Blocking_Immunity_Decay_Rate  = value*0.1
    return {"Base_Infectivity": value}

def update_sim_random_seed(simulation, value):
    simulation.task.config.parameters.Run_Number = value
    return {"Run_Number": value}

def sweep_over_scenarios(simulation, scenario_number):
    # scenario_interventions(scenario_number)

    return {"scenario": scenario_number}