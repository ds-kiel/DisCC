# DisCC - Distributed Conformance Checking

DisCC is a footprint-based, distributed, online conformance checking approach. <br/>
This implementation builds a model from the given log that only covers the main behavior of the log.
Then it runs through the whole log, checks every single event in terms of conformance to the model and calculates the fitness of each trace. Also the (partial) log's fitness after each trace is calculated.
The fitness measure we use is described in the work by Molka et al. (see citation below).

## Run DisCC
Make sure you install `python` and all necessary libraries beforehand (see `requirements.txt`).
Download an event log that you want to use and add its path to `.env`. (`CURRENT_LOG=“<some_name>”` determines which log is selected. Save the path to your event log under <some_name>_LOG.)
To use DisCC run `python3 distributed_conformance_checker.py`.

### Sliding Window
To evaluate the fitness when using the sliding window approach, we added another script.
This imitates the DisCC algorithm and does not use the `ActivityNode` class.
To use it, adjust the `WINDOW_SIZE` and the event log to examine with `CURRENT_LOG` in `.env` and run the script with `python3 conformance_analysis_sliding_window.py`.


<br/><br/><br/>


Molka, T. et al. "Conformance checking for BPMN-based process models." Proceedings of the 29th Annual ACM Symposium on Applied Computing. 2014.