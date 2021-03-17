# Put functions relating to reports here

from emodpy_malaria.reporters.builtin import MalariaSummaryReport

def add_reports(emod_task, manifest):
    reporter = MalariaSummaryReport()  # Create the reporter

    def msr_config_builder( params ):
        params.Report_Description = "Annual Report"
        params.Start_Day = 2*365
        params.Reporting_Interval = 365
        params.Max_Number_Reports = 1
        params.Age_Bins = [2, 10, 125]
        params.Parasitemia_Bins = [0, 50, 200, 500, 2000000]
        # 'class', 'Duration_Days', 'Event_Trigger_List', 'Individual_Property_Filter', 'Infectiousness_Bins', 'Nodeset_Config', 'Pretty_Format'
        return params

    reporter.config(msr_config_builder, manifest)
    emod_task.reporters.add_reporter(reporter)

