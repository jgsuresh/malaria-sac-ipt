def update_sim_bic(simulation, value):
    simulation.task.config.parameters.Acquisition_Blocking_Immunity_Decay_Rate  = value*0.1
    return {"Base_Infectivity": value}

def update_sim_random_seed(simulation, value):
    simulation.task.config.parameters.Run_Number = value
    return {"Run_Number": value}