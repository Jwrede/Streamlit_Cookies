from helper import *

import requests
import streamlit as st
import snowflake.connector
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
import json
import boto3
from aws_requests_auth.aws_auth import AWSRequestsAuth

st.set_page_config(layout="wide")

from streamlit_authenticator import Authenticator

authenticator = Authenticator(**st.secrets["cognito"])
user_info = authenticator.activate()

if authenticator.check_access():
    st.sidebar.write(user_info["username"])
    authenticator.login_button(logout=True)
else:
    authenticator.login_button()


@st.experimental_singleton
def init_connection():
    return snowflake.connector.connect(
        **st.secrets["snowflake"], client_session_keep_alive=True
    )

if (
    authenticator.check_access()
    and authenticator.check_role("READ")
):
    conn = init_connection()
    cur = conn.cursor()

    # sql = "SELECT DISTINCT(MASK_RULE_NAME) FROM MASKING_RULE_DEFINITION"
    # cur.execute(sql)
    # MASK_TYPES = cur.fetch_pandas_all()

    MASK_TYPES = [
        "",
        "mask_erk",
        "mask_akz",
        "mask_date",
        "mask_date_char",
        "mask_email",
        "salted_dwh_haskey",
        "mask_fin",
        "mask_hash",
        "mask_lookup_firstname",
        "mask_lookup_lastname",
        "mask_nullify",
        "mask_plz",
        "mask_timestamp",
        "mask_typesaferedact",
        "unmask",
        "salted_dwh_hash"
    ]

    sql = "SELECT * FROM MASKING_VIEW_COLUMN;"
    cur.execute(sql)
    data = cur.fetch_pandas_all()

    data = data[["SCHEMA_NAME", "VIEW_NAME", "COLUMN_NAME", "SYSTEM", "CLIENT", "MASK_RULE_NAME", "COL_MASK_KEY_FLAG", "MANUAL_COLUMN_SQL", "NEW_COLUMN_FLAG", "DELETED_FLAG"]]

    schema_views = [f"{schema}.{view}" for schema, view in data[["SCHEMA_NAME", "VIEW_NAME"]].drop_duplicates(subset=["SCHEMA_NAME", "VIEW_NAME"]).values]
    selected_table = st.selectbox("View", schema_views)

    data = data[(data["SCHEMA_NAME"] == selected_table.split(".")[0]) & (data["VIEW_NAME"] == selected_table.split(".")[1])].copy().reset_index(drop=True)


    builder = GridOptionsBuilder.from_dataframe(data)
    builder.configure_column("MASK_RULE_NAME", editable=True, singleClickEdit=True, cellEditor="agSelectCellEditor", cellEditorParams={'values': MASK_TYPES })
    builder.configure_column("MANUAL_COLUMN_SQL", editable=True, singleClickEdit=True)
    data[['COL_MASK_KEY_FLAG', 'NEW_COLUMN_FLAG', "DELETED_FLAG"]] = data[['COL_MASK_KEY_FLAG', 'NEW_COLUMN_FLAG', "DELETED_FLAG"]].fillna(0).astype(int)
    builder.configure_column('COL_MASK_KEY_FLAG', editable=True, cellRenderer=checkbox_renderer)
    builder.configure_column('NEW_COLUMN_FLAG', editable=True, cellRenderer=checkbox_renderer)
    builder.configure_column('DELETED_FLAG', editable=True, cellRenderer=checkbox_renderer)
    build = builder.build()
    build['getRowStyle'] = jscode

    res = AgGrid(
        data, 
        gridOptions=build, 
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW, 
        allow_unsafe_jscode=True,
        enable_enterprise_modules=False,
        height=750
    )

    if authenticator.check_role("WRITE"):
        changed_rows = res.data.astype(str)[~(data.astype(str) == res.data.astype(str)).all(axis=1)]
        if st.button("Save"):
            if len(changed_rows) > 0:
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
                changes = json.dumps({
                    'meta': {
                        'version': '1.0',
                        'triggered_from': '<service_name>',
                        'manual': 'false',
                        'user': user_info["username"]
                    },
                    'parameters': {
                        'database': st.secrets.get("snowflake").get("database"),
                        'update': [{
                            'schema_name': row["SCHEMA_NAME"],
                            'view_name': row["VIEW_NAME"],
                            'column_name': row["COLUMN_NAME"],
                            'set': {
                                'mask_rule_name': row["MASK_RULE_NAME"], 
                                'col_mask_key_flag': row["COL_MASK_KEY_FLAG"],
                                'manual_column_sql': row["MANUAL_COLUMN_SQL"],
                                'new_column_flag': row["NEW_COLUMN_FLAG"],
                                'deleted_flag': row["DELETED_FLAG"]
                            }
                        } for _,row in changed_rows.iterrows()]
                    }
                })

                response = requests.put(api_url, auth=auth, json=changes, timeout=300)
                print(response.json())
                if response.status_code != 200: 
                    raise RuntimeError("Error")
            
else:
    st.write("Please Login")