"""Module with functions called to perform various benchmarks."""

import time
import datetime


def measurement_log(thread_id, i, delta, measurement_count):
    """Log an info about the measurement status."""
    if thread_id is not None:
        print("    thread: #{t}    call {i}/{m}    {delta}".format(t=thread_id,
                                                                   i=i + 1,
                                                                   delta=delta,
                                                                   m=measurement_count))
    else:
        print("    #{i}    {delta}".format(i=i + 1, delta=delta))


def call_callback_function(function_to_call, s3):
    """Call the specified callback function."""
    assert function_to_call is not None, "Callback function is not specified."
    if s3 is None:
        retval = function_to_call(i)
    else:
        retval = function_to_call(i, s3)


def measure(function_to_call, check_function, measurement_count, pause_time, thread_id, s3=None):
    """Call the provided callback function repeatedly.

    Repeatedly call the provided callback function, then check results by provided check function,
    accumulate results and return them.
    """
    measurements = []
    debug = []
    for i in range(measurement_count):
        t1 = time.time()
        started_at = datetime.datetime.utcnow()

        call_callback_function(function_to_call, s3)

        print("Return value: ", retval)

        # let's ignore retval for concurrent calls (ATM)
        if thread_id is None:
            assert check_function(retval)

        t2 = time.time()
        finished_at = datetime.datetime.utcnow()

        delta = t2 - t1
        measurement_log(thread_id, i, delta, measurement_count)

        measurements.append({
            "measurement_number": i,
            "started_at": started_at,
            "finished_at": finished_at,
            "delta": delta})

        # we can store debug data taken from the stack analysis
        if "debug" in retval:
            debug.append(retval["debug"])

        time.sleep(pause_time)

    return measurements, debug


def core_api_benchmark(core_api, measurement_count, pause_time, thread_id=None):
    """Measure core API by accessing it and checking status code."""
    return measure(lambda i: core_api.get(),
                   lambda retval: retval.status_code == 200, measurement_count, pause_time,
                   thread_id)


def jobs_api_benchmark(jobs_api, measurement_count, pause_time, thread_id=None):
    """Measure jobs API by accessing it and checking status code."""
    return measure(lambda i: jobs_api.get(),
                   lambda retval: retval.status_code == 200, measurement_count, pause_time,
                   thread_id)


def stack_analysis_benchmark(core_api, measurement_count, pause_time, thread_id=None):
    """Measure server and worker modules by starting stack analysis."""
    return measure(lambda i: core_api.stack_analysis(thread_id, i),
                   lambda retval: retval["result"].status_code == 200,
                   measurement_count, pause_time, thread_id)


def component_analysis_benchmark(core_api, s3, measurement_count, pause_time,
                                 should_exist,
                                 thread_id=None,
                                 ecosystem=None, component=None, version=None):
    """Measure server and worker modules by starting component analysis."""
    expected_code = 200 if should_exist else 404
    return measure(lambda i, s3: core_api.component_analysis(thread_id, i,
                                                             ecosystem, component, version),
                   lambda retval: retval["result"] == expected_code,
                   measurement_count, pause_time, thread_id, s3)


def component_analysis_flow_scheduling(jobs_api, s3, measurement_count, pause_time,
                                       thread_id=None,
                                       ecosystem=None, component=None, version=None):
    """Measure jobs and worker modules by starting component analysis."""
    return measure(lambda i, s3: jobs_api.component_analysis(i, s3, thread_id,
                                                             ecosystem, component, version),
                   lambda retval: retval is True,
                   measurement_count, pause_time, thread_id, s3)


def package_query_to_graph_db(gremlin_api, measurement_count, pause_time,
                              thread_id=None):
    """Measure the simple package query to Gremlin database."""
    return measure(lambda i: gremlin_api.package_query(i, None),
                   lambda retval: gremlin_api.check_gremlin_response(retval),
                   measurement_count, pause_time, thread_id)


def package_version_query_to_graph_db(gremlin_api, measurement_count, pause_time,
                                      thread_id=None):
    """Measure the simple package+version query to Gremlin database."""
    return measure(lambda i: gremlin_api.package_version_query(i, None),
                   lambda retval: gremlin_api.check_gremlin_response(retval),
                   measurement_count, pause_time, thread_id)


def core_api_benchmark_thread(core_api, measurement_count, pause_time, q, thread_id):
    """Access core API in current thread and put results into the provided queue."""
    measurements = core_api_benchmark(core_api, measurement_count, pause_time, thread_id)
    q.put(measurements)


def component_analysis_read_thread_known_component(core_api, s3, measurement_count, pause_time,
                                                   q, thread_id):
    """Perform component analysis read in current thread and put results into the provided queue.

    Component analysis is performed for known comnonent.
    """
    measurements = component_analysis_benchmark(core_api, s3, measurement_count, pause_time, True,
                                                thread_id, "pypi", "clojure_py", "0.2.4")
    q.put(measurements)


def component_analysis_read_thread_unknown_component(core_api, s3, measurement_count, pause_time,
                                                     q, thread_id):
    """Perform component analysis read in current thread and put results into the provided queue.

    Component analysis is performed for unknown comnonent.
    """
    measurements = component_analysis_benchmark(core_api, s3, measurement_count, pause_time, False,
                                                thread_id,
                                                "pypi", "non_existing_component", "9.8.7")
    q.put(measurements)


def component_analysis_thread(jobs_api, s3, measurement_count, pause_time, q, thread_id):
    """Perform component analysis in current thread and put results into the provided queue."""
    measurements = component_analysis_flow_scheduling(jobs_api, s3, measurement_count,
                                                      pause_time, thread_id)
    q.put(measurements)


def stack_analysis_thread(core_api, s3, measurement_count, pause_time, q, thread_id):
    """Perform stack analysis in current thread and put results into the provided queue."""
    measurements = stack_analysis_benchmark(core_api, measurement_count,
                                            pause_time, thread_id)
    q.put(measurements)


def package_query_graph_db_thread(core_api, s3, measurement_count, pause_time, q, thread_id):
    """Perform query to graph DB in current thread and put results into the provided queue."""
    measurements = package_query_to_graph_db(core_api, measurement_count,
                                             pause_time, thread_id)
    q.put(measurements)


def package_version_query_graph_db_thread(core_api, s3, measurement_count, pause_time, q,
                                          thread_id):
    """Perform query to graph DB in current thread and put results into the provided queue."""
    measurements = package_version_query_to_graph_db(core_api, measurement_count,
                                                     pause_time, thread_id)
    q.put(measurements)
