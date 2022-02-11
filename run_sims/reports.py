from emodpy_malaria.reporters.builtin import add_malaria_summary_report, add_report_event_counter, \
    add_report_node_demographics

from run_sims import manifest

summary_report_age_bins = list(range(20)) + list(range(20, 125, 5))


def add_scenario_reports(emod_task, include_summary=True, include_inset=True, include_bednet_events_in_counter=False):
    if include_summary:
        add_malaria_summary_report(emod_task, manifest=manifest, age_bins=summary_report_age_bins, start_day=365)

    events_to_count = [
        "Received_Treatment",
        "Received_Test",
        "Received_Campaign_Drugs",
        "Received_RCD_Drugs",
        "Received_SMC",
        "Received_Ivermectin",
        "Received_Primaquine"
    ]
    if include_bednet_events_in_counter:
        events_to_count += ["Bednet_Discarded", "Bednet_Got_New_One", "Bednet_Using"]

    add_report_event_counter(emod_task, manifest=manifest, event_trigger_list=events_to_count)


    if include_inset:
        emod_task.config.parameters.Enable_Default_Reporting = 1
    else:
        emod_task.config.parameters.Enable_Default_Reporting = 0


def add_burnin_reports(emod_task, include_inset=False):
    add_malaria_summary_report(emod_task, manifest=manifest, start_day=45*365)

    if include_inset:
        emod_task.config.parameters.Enable_Default_Reporting = 1
    else:
        emod_task.config.parameters.Enable_Default_Reporting = 0

    events_to_count = ["NewClinicalCase"] #TESTING ONLY
    # events_to_count = [
    #     "Bednet_Discarded",
    #     "Bednet_Got_New_One",
    #     "Bednet_Using",
    #     "Received_Treatment",
    #     "Received_SMC"]

    add_report_event_counter(emod_task,
                             manifest=manifest,
                             event_trigger_list=events_to_count,
                             duration_days=365*50)


def add_testing_reports(emod_task):
    add_scenario_reports(emod_task, include_summary=True, include_inset=True, include_bednet_events_in_counter=True)

    add_report_node_demographics(emod_task, manifest=manifest, individual_property_to_collect='SchoolStatus', stratify_by_gender=0)


    add_malaria_summary_report(emod_task,
                               manifest=manifest,
                               individual_property_filter="SchoolStatus:AttendsSchool",
                               report_description="AttendsSchool",
                               age_bins=summary_report_age_bins)

    add_malaria_summary_report(emod_task,
                               manifest=manifest,
                               individual_property_filter="SchoolStatus:DoesNotAttendSchool",
                               report_description="DoesNotAttendSchool",
                               age_bins=summary_report_age_bins)