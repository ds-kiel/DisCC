# Copyright 2024 Kiel University
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from dotenv import load_dotenv
import os


load_dotenv()
LOG_NAME = str(os.getenv('CURRENT_LOG'))
EVENT_LOG = str(os.getenv(f"{LOG_NAME}_LOG"))
FACTOR = float(os.getenv("FACTOR"))


class ActivityNode:
    """
    Activity node class for distributed implementation.
    Each node is responsible for one activity type.
    An event is triggered by calling function "trigger_event".
    """

    def __init__(self, activity_id, model_footprint_vector, model_start_activity, model_end_activity):
        self.activity_id = activity_id
        self.nodes_list = []

        # model information
        self.model_footprint_vector = model_footprint_vector
        self.model_start_activity = model_start_activity
        self.model_end_activity = model_end_activity

        # current log/trace info
        # one entry for each case id
        self.log_info_per_trace = {}
        self.full_log_predecessors = set()
        self.full_log_start_activity = False
        self.full_log_end_activity = False


    def set_nodes_list(self, nodes_list):
        self.nodes_list = nodes_list


    def get_matches_mismatches_full_log(self):
        matches = 0
        mismatches = 0
        for pred in self.full_log_predecessors:
            if self.model_footprint_vector[pred]:
                matches += 1
            else:
                mismatches += 1
        if self.full_log_start_activity:
            if self.model_start_activity:
                matches += 1
            else:
                mismatches += 1
        if self.full_log_end_activity:
            if self.model_end_activity:
                matches += 1
            else:
                mismatches += 1

        return mismatches, matches


    def check_model_conformance(self, direct_succession):
        pred, succ = direct_succession

        if succ != self.activity_id:
            print("Something went wrong. I should be the successor.")
            raise Exception

        if self.model_footprint_vector[pred] == 1:
            return True

        return False


    def non_conformance_alert(self, pred, case_id):
        print(f"Caution! Activity {self.activity_id} is succeeding {pred} in case {case_id}.")


    def trigger_event(self, activity_id, case_id, start_of_trace, end_of_trace, predecessor, mismatches, matches):
        # set up dict for case id
        if str(case_id) not in self.log_info_per_trace.keys():
            self.log_info_per_trace[str(case_id)] = {"is_start": False, "is_end": False, "predecessors": set(), "conformance_measure": None}

        # event is start event
        if start_of_trace:
            self.full_log_start_activity = True

            if not self.log_info_per_trace[str(case_id)]["is_start"]:
                self.log_info_per_trace[str(case_id)]["is_start"] = True
                if self.model_start_activity:
                    matches += 1
                else:
                    mismatches += 1

        # event is NOT start event
        else:
            # to later calculate measure for whole log
            self.full_log_predecessors.add(predecessor)

            # check whether predecessor is also predecessor in the model
            is_matching = self.check_model_conformance((predecessor, activity_id))
            if not is_matching:
                self.non_conformance_alert(predecessor, case_id)

            # only if it is a new direct succession: add the predecessor to list and
            # increment the number of matches or mismatches
            if predecessor not in self.log_info_per_trace[str(case_id)]["predecessors"]:
                self.log_info_per_trace[str(case_id)]["predecessors"].add(predecessor)

                if not is_matching:
                    mismatches += 1
                else:
                    matches += 1

        # if it is the end event of the trace -> calculate conformance metric
        if end_of_trace:
            self.full_log_end_activity = True

            if not self.log_info_per_trace[str(case_id)]["is_end"]:
                self.log_info_per_trace[str(case_id)]["is_end"] = True
                if self.model_end_activity:
                    matches += 1
                else:
                    mismatches += 1

            print(f"Matches: {matches}   Mismatches {mismatches}")

            conformance_metric_trace = matches / (matches + mismatches)
            self.log_info_per_trace[str(case_id)]["conformance_measure"] = conformance_metric_trace
            print(f"Conformance measure of trace = {conformance_metric_trace}       for case ID  {case_id}")

            # write into csv file
            # with open(f"outputs/{LOG_NAME}_fitness_per_trace_{int(FACTOR*100)}_percent.csv", "a") as f:
            #     f.write(f"{case_id};{conformance_metric_trace}\n")

        return mismatches, matches
