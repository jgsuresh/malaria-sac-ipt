from emodpy_malaria.reporters.builtin import add_malaria_summary_report, add_report_event_counter, \
    add_report_node_demographics, add_report_intervention_pop_avg

from run_sims import manifest

summary_report_age_bins = list(range(20)) + list(range(20, 125, 5))


def add_scenario_reports(emod_task, include_summary=True, include_inset=True, include_bednet_events_in_counter=False):
    if include_summary:
        add_malaria_summary_report(emod_task, manifest=manifest, age_bins=summary_report_age_bins, start_day=365)

    events_to_count = [
        "Received_Treatment",
        # "Received_Test",
        "Received_Campaign_Drugs",
        "Received_SMC",
        # "Received_Ivermectin",
        # "Received_Primaquine"
    ]
    if include_bednet_events_in_counter:
        events_to_count += ["Bednet_Discarded", "Bednet_Got_New_One", "Bednet_Using"]

    add_report_event_counter(emod_task, manifest=manifest, event_trigger_list=events_to_count)


    if include_inset:
        emod_task.config.parameters.Enable_Default_Reporting = 1
    else:
        emod_task.config.parameters.Enable_Default_Reporting = 0


def add_burnin_reports(emod_task, archetype, include_inset=True):
    add_malaria_summary_report(emod_task, manifest=manifest, start_day=45*365)
    add_report_intervention_pop_avg(emod_task, manifest=manifest)

    if include_inset:
        emod_task.config.parameters.Enable_Default_Reporting = 1
    else:
        emod_task.config.parameters.Enable_Default_Reporting = 0


    # events_to_count = ["NewClinicalCase"] #TESTING ONLY
    events_to_count = [
        "Bednet_Discarded",
        "Bednet_Got_New_One",
        "Bednet_Using",
        "Received_Treatment",
        "NonDiseaseDeaths"]

    if archetype == "Sahel":
        events_to_count += ["Received_SMC"]

    add_report_event_counter(emod_task,
                             manifest=manifest,
                             event_trigger_list=events_to_count,
                             start_day=0,
                             end_day=365*50)


def add_testing_reports(emod_task):
    add_scenario_reports(emod_task, include_summary=True, include_inset=True, include_bednet_events_in_counter=True)

    add_report_node_demographics(emod_task, manifest=manifest, ip_key_to_collect='SchoolStatus', stratify_by_gender=0)


    add_malaria_summary_report(emod_task,
                               manifest=manifest,
                               must_have_ip_key_value="SchoolStatus:AttendsSchool",
                               filename_suffix="AttendsSchool",
                               age_bins=summary_report_age_bins,
                               pretty_format=1)

    add_malaria_summary_report(emod_task,
                               manifest=manifest,
                               must_have_ip_key_value="SchoolStatus:DoesNotAttendSchool",
                               filename_suffix="DoesNotAttendSchool",
                               age_bins=summary_report_age_bins,
                               pretty_format=1)
