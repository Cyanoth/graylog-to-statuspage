# Graylog to Statuspage System Metrics

A python script which periodically gets the value of a metric from a Graylog instance and posts the value to a system metric on statuspage.io 
Include are files to run this script continuously in a docker container. 

## Getting Started

You must first setup your Graylog instance & statuspage. Clone this repository to your local machine. 

Create a dashboard on Graylog. Perform a search on Graylog, and click 'Add count to dashboard', select the newly created dashboard. Alternatively, you may select the statistics of field and add the mean/minimum/maximum/variance etc to the dashboard. Create a local user on Graylog, give read-permission to access the dashboard. [Generate a API token for this user.](http://docs.graylog.org/en/2.5/pages/configuration/rest_api.html#creating-and-using-access-token) 

Create a system metric on the manage statuspage, select "I'll submit my own data for this metric".

### Prerequisites

To run this script outside of a container. Ensure python3 is installed and run:
```
pip install -r requirements.txt
```

To run this script as a container, ensure you have docker installed.

### Configuring

After completing the stages in Getting Started, edit the file graylog_to_statuspage_config.yaml to define the API domain & API key of your graylog instance and statuspage.

```
statuspageAPIHost: "https://api.statuspage.io"
statuspageAPIKey: "abcdefgh1234ijlmn02324"
graylogAPIHost: "https://graylog.coolhost.com"
graylogAPIToken: "rfjdsjdqwe432fnk"
```

Add a section 'metrics' and for each metric you'd like send from graylog to statuspage, add the following block:

```
  - description: "Frontend Incoming Requests"      # Give a human-readable description of this metric, so you can identify without looking up the ID.
    graylogDashboardID: "rfjdsjdqwe432fnk" # Click the 'i' next to the metric on a graylog dashboard to reveal the dashboard ID.
    graylogWidgetID: "asfqsad-12124-asda-12421-fvsdfaqwe" # Click the 'i' next to the metric on a graylog dashboard to reveal the widget ID.
    statuspageID: "lfdlwe23sd" # Statuspage Page ID is revealed upon creating a new statuspage system metric with custom data. 
    statuspageMetricID: "jsdksa212" # Metric ID is revealed upon creating a new statuspage system metric with custom data. 
```

Now run the script:
```
python graylog_to_statuspage.py -v -s
```

To see the list of possible starting arguments, run:
```
python graylog_to_statuspage.py --help 
```

You should see the following:
```
INFO     ------------------------------
INFO     Graylog Metrics To StatusPage Metric Starting
INFO     ------------------------------
DEBUG    Updating the metric: "Frontend Incoming Requests"
DEBUG    GET https://graylog.coolhost.com/api/dashboards/rfjdsjdqwe432fnk/widgets/asfqsad-12124-asda-12421-fvsdfaqwe/value
DEBUG    Starting new HTTPS connection (1): graylog.coolhost.com
DEBUG    https://graylog.coolhost.com/api/dashboards/rfjdsjdqwe432fnk/widgets/asfqsad-12124-asda-12421-fvsdfaqwe/value HTTP/1.1" 200 70
DEBUG    Result: https://graylog.coolhost.com/api/dashboards/rfjdsjdqwe432fnk/widgets/asfqsad-12124-asda-12421-fvsdfaqwe/value
DEBUG    POST https://api.statuspage.io/v1/pages/lfdlwe23sd/metrics/jsdksa212/data.json PAYLOAD: {'data': {'timestamp': 1550424695, 'value': 1274}}
INFO     Metric: "Frontend Incoming Requests" value updated to: 1274

```

## Deployment

After configuration, you can run this script continuously from within a docker container.

Within the working directory run:
```
docker build -t graylog_to_statuspage .
docker run graylog_to_statuspage
```

Note, that this will embedded the configuration file within the docker image. Y

You may to use docker-compose to create a named volume and copy the configuration file to here. This helps keep the docker image generic & configuration separate:
```
docker-compose build
docker-compose up
```
Customise the Dockerfile & docker-compose file to meet your deployment requirements.