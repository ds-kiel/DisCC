import numpy as np


def calculate_model_of_partial_log(df, activity_count, activity_name_to_server_id_mapping):

    last_activity = None
    current_case = None

    fm = np.zeros(shape=(activity_count, activity_count))
    start_activities = set()
    end_activities = set()

    for j, row in df.iterrows():
        activity_name = row['concept:name']
        activity_id = int(activity_name_to_server_id_mapping[str(activity_name)])
        case_id = row['case:concept:name']

        # new case id -> start activity -> no predecessor
        if current_case == case_id:

            # update pred -> dir succ in fm
            if last_activity or last_activity == 0:
                fm[last_activity][activity_id] = 1

        # otherwise activity is start activity
        else:
            start_activities.add(activity_id)

        # activity is end activity if it is the last event or the next event has another case id
        if j == int(df.shape[0]) - 1 or str(case_id) != str(df.iloc[j+1]['case:concept:name']):
            end_activities.add(activity_id)

        # update current_case and last_activity
        current_case = case_id
        last_activity = activity_id

    return fm, list(start_activities), list(end_activities)


def compute_activities_and_mapping(df):
    """
    Computes a mapping from server IDs to activity names and the other way around.
    """
    activities_in_traces = set(row["concept:name"] for _,row in df.iterrows())
    id_to_name = {}
    name_to_id = {}
    for j, activity_name in enumerate(activities_in_traces):
        id_to_name[str(j)] = activity_name
        name_to_id[activity_name] = j
    return id_to_name, name_to_id, len(activities_in_traces)