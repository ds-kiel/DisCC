import math
import os

from dotenv import load_dotenv
from pm4py.algo.filtering.log.variants.variants_filter import \
    filter_variants_top_k
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.statistics.variants.log.get import get_variants

from auxiliaries.event_log_adjuster import no_doubled_timestamps
from auxiliaries.file_reader import read_event_log
from auxiliaries.model_calculator import (calculate_model_of_partial_log,
                                          compute_activities_and_mapping)

load_dotenv()
LOG_NAME = str(os.getenv('CURRENT_LOG'))
EVENT_LOG = str(os.getenv(f"{LOG_NAME}_LOG"))
FACTOR = float(os.getenv("FACTOR"))
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE"))
STEP = int(WINDOW_SIZE/2)

"""
Disclaimer:
Not using ActivityNode class for sliding window approach -- this is future work.
"""

# set up output file
# filename = f"outputs/{LOG_NAME}_fitness_per_log_window_{WINDOW_SIZE}_step_{STEP}_{int(FACTOR*100)}_percent.csv"
# with open(filename, "w", encoding="utf-8") as f:
#     f.write("case_id;fitness\n")


def calculate_conformance_measure(dir_succ_in_log):

    # make relations to set independent from case
    dir_succ_in_log = set([(a,b) for (a,b),_ in dir_succ_in_log])

    # compare log and model and compute fitness
    match = 0
    nmbr_dir_succ_in_log = len(dir_succ_in_log)

    for (a, b) in dir_succ_in_log:
        # start
        if (not a and a != 0) and b in model_start_activities:
            match += 1
        # end
        elif (not b and b != 0) and a in model_end_activities:
            match += 1
        # direct succession
        elif (a or a == 0) and (b or b == 0) and model_fm[a][b]:
            match += 1

    # compute and return fitness
    return match / nmbr_dir_succ_in_log


# Create event log
log = read_event_log(EVENT_LOG)
log = log.filter(items=["case:concept:name", "concept:name", "time:timestamp"]) # filter changes order
log = log.sort_values(["case:concept:name","time:timestamp"])
log = no_doubled_timestamps(log)
server_id_to_activity_name_mapping, activity_name_to_server_id_mapping, activity_count = compute_activities_and_mapping(log)

# Only use a certain percentage of variants for the model
variants = get_variants(log)
k = math.floor(FACTOR * len(variants))
model_event_log = filter_variants_top_k(log, k=k)
model_event_log = log_converter.apply(model_event_log, variant=log_converter.Variants.TO_DATA_FRAME)
model_fm, model_start_activities, model_end_activities = calculate_model_of_partial_log(model_event_log, activity_count, activity_name_to_server_id_mapping)

log["case_next_event"] = log["case:concept:name"].shift(-1)
log["case_last_event"] = log["case:concept:name"].shift(1)
log["predecessor_activity_name"] = log["concept:name"].shift(1)



# Run through log with sliding window
# [((a,b),case)]
case_count = 0
direct_successions = []
for (_, row) in log.iterrows():
    activity_id = int(activity_name_to_server_id_mapping[str(row["concept:name"])])

    # start
    if row["case:concept:name"] != row["case_last_event"]:
        direct_successions.append(((None, activity_id), case_count))
    # not start
    else:
        pred = int(activity_name_to_server_id_mapping[str(row["predecessor_activity_name"])])
        direct_successions.append(((pred, activity_id), case_count))

    # end
    if row["case:concept:name"] != row["case_next_event"]:
        direct_successions.append(((activity_id, None), case_count))
        case_count += 1

number_cases = case_count

# calculate conformance for different windows
log_dir_succ_in_window = []
for (a,b), case in direct_successions:
    log_dir_succ_in_window.append(((a,b),case))

    if case % STEP == 0 and case >= WINDOW_SIZE and (not b and b != 0):
        # calculate conformance
        fitness = calculate_conformance_measure(log_dir_succ_in_window)
        print(f"Fitness {fitness}   case {case}")

        # remove first 50 cases
        (_,_),smallest_case = log_dir_succ_in_window[0]
        log_dir_succ_in_window = [((a,b),case) for (a,b), case in log_dir_succ_in_window if case >= smallest_case+STEP]
        # with open(filename ,"a", encoding="utf-8") as f:
        #     f.write(f"{case};{fitness}\n")

fitness = calculate_conformance_measure(log_dir_succ_in_window)
(_,_),last_case = log_dir_succ_in_window[-1]
print(f"Fitness {fitness}   case {last_case}")
# with open(filename ,"a", encoding="utf-8") as f:
#     f.write(f"{last_case};{fitness}\n")