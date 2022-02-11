#fixme Doesn't work yet (dtk-tools copied)

def burnin_setup(cb, archetype):
    cb.set_param("Simulation_Duration", 50 * 365)
    cb.set_param("Serialization_Type", "TIMESTEP")
    cb.set_param("Serialization_Time_Steps", [50 * 365])
    cb.set_param("Serialization_Precision", "REDUCED")
    add_burnin_historical_interventions(cb, archetype=archetype)
    # recurring_outbreak(cb, outbreak_fraction=0.005)
    seasonal_daily_importations(cb, 25)

def draw_from_serialized_file(cb, burnin_dict):
    filepath = os.path.join(burnin_dict["path"], "output")
    cb.set_param("Serialized_Population_Path", filepath)
    cb.set_param("Serialized_Population_Filenames", ["state-18250.dtk"])

    return {"burnin_approx_pfpr2_10": burnin_dict["approximate_pfpr2_10"],
            "burnin_habitat_scale": burnin_dict["habitat_scale"]}
