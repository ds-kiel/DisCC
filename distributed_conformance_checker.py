# Copyright 2024 Kiel University
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import math
import os

from dotenv import load_dotenv
from pm4py.algo.filtering.log.variants.variants_filter import \
    filter_variants_top_k
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.statistics.variants.log.get import get_variants

from activity_node import ActivityNode
from alpha_miner_original import run_original_alpha_miner
from auxiliaries.event_log_adjuster import no_doubled_timestamps
from auxiliaries.file_reader import read_event_log
from auxiliaries.model_calculator import (calculate_model_of_partial_log,
                                          compute_activities_and_mapping)

load_dotenv()
LOG_NAME = str(os.getenv('CURRENT_LOG'))
EVENT_LOG = str(os.getenv(f"{LOG_NAME}_LOG"))
FACTOR = float(os.getenv("FACTOR"))

# filename for "fitness per partial log"
# filename = f"outputs/{LOG_NAME}_fitness_per_partial_log_{int(FACTOR*100)}_percent.csv"
# filename for "fitness per trace"
# filename = f"outputs/{LOG_NAME}_fitness_per_trace_{int(FACTOR*100)}_percent.csv"

# set up output file
# with open(filename ,"w", encoding="utf-8") as f:
#     f.write("case_id;fitness\n")


# ----------

def get_node_by_id(nodes, node_id):
    for n in nodes:
        if n.activity_id == node_id:
            return n


def calculate_conformance_full_log(case_id):
    # Calculate conformance of full log
    total_mismatches = 0
    total_matches = 0

    for n in nodes:
        mismatches, matches = n.get_matches_mismatches_full_log()
        total_mismatches += mismatches
        total_matches += matches

    conformance_metric_log = total_matches/(total_mismatches + total_matches)
    print(f"\n\nConformance of full log (up till now) = {conformance_metric_log}")

    # with open(filename, "a") as f:
    #     f.write(f"{case_id};{conformance_metric_log}\n")

# ----------


# Create event logs
log = read_event_log(EVENT_LOG)
log = log.filter(items=["case:concept:name", "concept:name", "time:timestamp"]) # filter changes order
log = log.sort_values(["case:concept:name","time:timestamp"])
log = no_doubled_timestamps(log)
server_id_to_activity_name_mapping, activity_name_to_server_id_mapping, activity_count = compute_activities_and_mapping(log)
number_events = log.shape[0]

# Only use a certain percentage of variants for the model
variants = get_variants(log)
k = math.floor(FACTOR * len(variants))
model_event_log = filter_variants_top_k(log, k=k)
model_event_log = log_converter.apply(model_event_log, variant=log_converter.Variants.TO_DATA_FRAME)
model_fm, model_start_activities, model_end_activities = calculate_model_of_partial_log(model_event_log, activity_count, activity_name_to_server_id_mapping)

# run_original_alpha_miner(log)
# run_original_alpha_miner(model_event_log)


# Create nodes
nodes = []
for activity_id in activity_name_to_server_id_mapping.values():
    nodes.append(ActivityNode(activity_id, [row[activity_id] for row in model_fm], activity_id in model_start_activities, activity_id in model_end_activities))

for node in nodes:
    node.set_nodes_list(nodes)


## Checking Conformance
# Run through log
log["case_next_event"] = log["case:concept:name"].shift(-1)

# get fitness of partial log after every case
fitness = []
current_case = None
case_id = 0

for k, (_, row) in enumerate(log.iterrows()):

    activity_name = row['concept:name']
    activity_id = int(activity_name_to_server_id_mapping[str(activity_name)])
    case_name = str(row['case:concept:name'])
    case_name_next_event = str(row['case_next_event'])

    # start event
    if case_name != current_case:
        mismatches = 0
        matches = 0
        start_of_trace = True
        pred = None

    # not start event
    else:
        start_of_trace = False
        pred_name = log.iloc[k-1]['concept:name']
        pred = int(activity_name_to_server_id_mapping[str(pred_name)])

    # check whether it is an end event
    if k == int(log.shape[0]) - 1 or case_name != case_name_next_event:
        if k != int(log.shape[0]-1):
            print(f"case ID: {case_name}      next case: {case_name_next_event}     activity {server_id_to_activity_name_mapping[str(activity_id)]}")
        end_of_trace = True
    else:
        end_of_trace = False

    # trigger event at activity node
    mismatches, matches = get_node_by_id(nodes, activity_id).trigger_event(activity_id, case_id, start_of_trace, end_of_trace, pred, mismatches, matches)
    fitness.append(matches/(matches+mismatches))

    # calculate fitness after each trace
    if end_of_trace:
        calculate_conformance_full_log(case_id)
        case_id += 1
    current_case = case_name

# print(fitness)
