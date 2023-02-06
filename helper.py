from st_aggrid import JsCode
from aws_requests_auth.aws_auth import AWSRequestsAuth
import boto3
import requests
import json

def put_request_masking(trigger_json):
    service_name = "masking_service"
    api_url = "https://t27woae5z8.execute-api.eu-central-1.amazonaws.com/dev/masking"
    credentials = boto3.Session().get_credentials()
    auth = AWSRequestsAuth(
        aws_access_key=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        aws_token=credentials.token,
        aws_host='t27woae5z8.execute-api.eu-central-1.amazonaws.com',
        aws_region='eu-central-1',
        aws_service='execute-api'
    )
    response = requests.put(api_url, auth=auth, json=trigger_json, timeout=300)
    print("http response service_code from " + service_name + " src: " + str(response))
    print("http response from " + service_name + " src before parsing: " + str(response.content))
    print("http response headers from " + service_name + " src before parsing: " + str(response.headers))
    if response.status_code != 200:
        # hier könnte man ggf. die Errormessage des Service parsen, falls dieser eine zurückgibt.
        print(response.json())
        raise RuntimeError("Error calling " + service_name + " src with the event: " + json.dumps(trigger_json))
    response_json = response.json()
    parsed_response = response_json['data'][0][1]
    print("parsed response from " + service_name + " src " + str(parsed_response))
    return parsed_response


jscode = JsCode("""
    function(params) {
        if (params.data.NEW_COLUMN_FLAG === 1) {
            return {
                'color': 'white',
                'backgroundColor': 'orange'
            }
        }
    };
""")

checkbox_renderer = JsCode("""
    class CheckboxRenderer{

        init(params) {
            this.params = params;

            this.eGui = document.createElement('input');
            this.eGui.type = 'checkbox';
            this.eGui.checked = params.value;

            this.checkedHandler = this.checkedHandler.bind(this);
            this.eGui.addEventListener('click', this.checkedHandler);
        }

        checkedHandler(e) {
            let checked = e.target.checked;
            let colId = this.params.column.colId;
            this.params.node.setDataValue(colId, checked);
        }

        getGui(params) {
            return this.eGui;
        }

        destroy(params) {
            this.eGui.removeEventListener('click', this.checkedHandler);
        }
    }
""")