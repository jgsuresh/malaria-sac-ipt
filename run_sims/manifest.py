import os

base_folder = "C:/Users/joshsu/Code/malaria-sac-ipt/run_sims/"

# Ensure the following locations exist
schema_file = os.path.join(base_folder, "download/schema.json")
eradication_path = os.path.join(base_folder, "download/Eradication")
assets_input_dir = os.path.join(base_folder, "Assets")
plugins_folder = os.path.join(base_folder, "download/reporter_plugins")
current_directory = ""
ep4_path = os.path.join(base_folder, "Assets")
burnin_directory = os.path.join(base_folder, "Assets")
sif = os.path.join(base_folder, "Assets/sif.id")

# Demographics files for different archetypes
# demographics_file_path = os.path.join(base_folder, "Assets"
demographics_file_path_central = os.path.join(base_folder, "Assets/demo_central.json")
demographics_file_path_coastal_western = os.path.join(base_folder, "Assets/demo_coastal_western.json")
demographics_file_path_eastern = os.path.join(base_folder, "Assets/demo_eastern.json")
demographics_file_path_sahel = os.path.join(base_folder, "Assets/demo_sahel.json")
demographics_file_path_southern = os.path.join(base_folder, "Assets/demo_southern.json")

# CSVs for intervention setup
additional_csv_folder = os.path.join(base_folder, "Assets/")