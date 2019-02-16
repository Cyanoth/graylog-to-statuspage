import argparse
import json
import logging
import os
import time
import requests

LOGGING_FORMAT='%(asctime)s %(levelname)-8s %(message)s'
LOGGING_DATETIME_FORMAT='%Y-%m-%d %H:%M:%S'
DRY_RUN = False


def main(config_file_path):
    """
    Entry Point. Load configuration & infinite loop to update metrics
    :param config_file_path: Script configuration file containing API & metrics to monitor.
    """
    logging.info("------------------------------")
    logging.info("Graylog Metrics To StatusPage Metric Starting")
    logging.info("------------------------------")

    try:
        with open(config_file_path, 'r') as f:  # Load configuration
            config = json.load(f)
            statuspage_api_host = config["statuspageAPIHost"]
            graylog_api_host = config["graylogAPIHost"]
            statuspage_api_key = config["statuspageAPIKey"]
            graylog_api_token = config["graylogAPIToken"]
            update_delay = config["updateDelay"]
            metrics = config["metrics"]

        if update_delay < 1000:  # Maximum update frequency of StatusPage API is 1 second
            update_delay = 1000
            logging.warn("Update Delay too small. StatusPage maximum metric update frequency is 1 second. "
                         "The update delay value has been changed to 1000.")

        if len(metrics) == 0:
            logging.info("No metrics have been defined. This script has nothing to do, exiting now.")
            exit(0)

        while True:  # Continuously update the metics until script exits
            try:
                for metric in metrics:
                    logging.debug("Updating the metric: \"{}\"".format(metric["description"]))
                    # Get the metric value from Graylog
                    metric_value = get_graylog_metric_value(graylog_api_host, graylog_api_token, metric["graylogDashboardID"] ,metric["graylogWidgetID"])
                    # Send the metic value to StatusPage
                    send_statuspage_metric_value(statuspage_api_host, statuspage_api_key, metric["statuspageID"], metric["statuspageMetricID"], metric_value)
                    logging.info("Metric: \"{}\" value updated to: {}".format(metric["description"], metric_value))

            except requests.exceptions.HTTPError as err:
                logging.warn("Failed to update the metric: \"{}\". HTTP Error. Response: {}".format(metric["description"], err.response))
            except KeyError as err:
                logging.warn("Failed to update a metric because of a missing key in the conf file. Error: {}".format(err))
            except Exception as err:
               logging.warn("Failed to update a metric. Error: {}".format(err))

            logging.debug("All metrics updated. Next update in: {}ms".format(update_delay))
            time.sleep(update_delay / 1000.0)

    except Exception as err:
        logging.error("Unhandled Exception Occurred. Error: {}".format(err))
    finally:
        logging.info("*** Graylog Metrics To StatusPage Metrics stopping ***")


def get_graylog_metric_value(gl_apihost, gl_apitoken, gl_dashboardid, gl_widget_id):
    """
    Using Graylog API, retrieve the value of a metric
    :param gl_apihost: Protocol & domain name of the Graylog Server
    :param gl_apitoken: API token with permission to read dashboard metrics
    :param gl_dashboardid: ID of the Graylog Dashboard containing the metric
    :param gl_widget_id: ID of the widget containing the metric
    :return:
    """
    request_url = gl_apihost + "/api/dashboards/" + gl_dashboardid + "/widgets/" + gl_widget_id + "/value"
    logging.debug("GET {}".format(request_url))

    # Graylog API tokens are strange. For auth, the API token is used as a username & string 'token' for the password.
    res = requests.get(request_url, auth=(gl_apitoken, 'token'))
    res.raise_for_status()  # If not 200, raise HTTPError Exception
    metric_value = res.json()["result"]
    logging.debug("Result: {}".format(request_url, metric_value))
    return metric_value


def send_statuspage_metric_value(sp_apihost, sp_apikey, sp_pageid, sp_metricid, metric_value):
    """
    Send a metric value to StatusPage
    :param sp_apihost: Protocol & domain name of StatusPage API
    :param sp_apikey: API token with permission to write Metrics to StatusPage
    :param sp_pageid: Page ID containing the system metric
    :param sp_metricid: System Metric ID to update the value
    :param metric_value: Set the value of the metric
    """
    request_url = sp_apihost + "/v1/pages/" + sp_pageid + "/metrics/" + sp_metricid + "/data.json"
    payload = {'data': {'timestamp': int(time.time()), 'value': metric_value}}
    headers = {'Authorization': 'OAuth ' + sp_apikey}

    logging.debug("POST {} PAYLOAD: {}".format(request_url, payload))

    if not DRY_RUN:  # Don't send the value if dry-running
        res = requests.post(request_url, json=payload, headers=headers)
        res.raise_for_status()  # If not 200, raise HTTPError Exception


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-c', '--config', help="Configuration file that includes API & metrics to monitor", type=str,default="graylog_to_statuspage_conf.json")
    parser.add_argument('-d', '--dryrun', help="Dry-run mode. The value won't actually be sent to StatusPage.", action='store_true')
    parser.add_argument('-l', '--logfile', help="Specify the log-file to store logging information.", default='graylog_to_statuspage.log')
    parser.add_argument('-p', '--pidfile', help="Specify PID lock file for multiple instances.", default='/tmp/graylog_to_statuspage')
    parser.add_argument('-s', '--screen', help="Print log details to screen (console)", action='store_true')
    parser.add_argument('-v', '--verbose', help="Verbose. Log debug information", action='store_true')

    args = parser.parse_args()
    DRY_RUN = args.dryrun

    # PIDFile checks, to prevent more than one instance of this script running at the same time.
    pid = str(os.getpid())

    if os.path.isfile(args.pidfile):
        print("FATAL: Failed to start Graylog to StatusPage script. Another instance is already running!")
        exit(1)

    with open(args.pidfile, 'w') as file:
        file.write(pid)

    log_handlers = []

    # Logging output
    if args.logfile != "":
        log_handlers.append(logging.FileHandler(args.logfile))
    if args.screen:
        log_handlers.append(logging.StreamHandler())

    # Logging verbosity
    if args.verbose:
        logging.basicConfig(handlers=log_handlers, format=LOGGING_FORMAT, level=logging.DEBUG, datefmt=LOGGING_DATETIME_FORMAT)
    else:
        logging.basicConfig(handlers=log_handlers, format=LOGGING_FORMAT, level=logging.INFO, datefmt=LOGGING_DATETIME_FORMAT)

    try:
        main(args.config)
    finally:
        os.unlink(args.pidfile)