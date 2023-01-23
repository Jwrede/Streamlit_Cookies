from jscode import *

import streamlit as st
import snowflake.connector
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
import json

st.set_page_config(layout="wide")

import authenticate as authenticate

authenticate.activate()

if authenticate.check_access():
    authenticate.button_logout()
else:
    authenticate.button_login()


@st.experimental_singleton
def init_connection():
    return snowflake.connector.connect(
        **st.secrets["snowflake"], client_session_keep_alive=True
    )

if (
    authenticate.check_access()
    and authenticate.check_role("READ")
):

    conn = init_connection()
    cur = conn.cursor()

    # sql = "SELECT DISTINCT(MASK_RULE_NAME) FROM MASKING_RULE_DEFINITION"
    # cur.execute(sql)
    # MASK_TYPES = cur.fetch_pandas_all()

    MASK_TYPES = [
        None,
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

    data = data[(data["SCHEMA_NAME"] == selected_table.split(".")[0]) & (data["VIEW_NAME"] == selected_table.split(".")[1])].copy()


    builder = GridOptionsBuilder.from_dataframe(data)
    builder.configure_column("MASK_RULE_NAME", editable=True, cellEditor="agSelectCellEditor", cellEditorParams={'values': MASK_TYPES })
    builder.configure_column('COL_MASK_KEY_FLAG', editable=True, cellRenderer=checkbox_renderer)
    build = builder.build()
    build['getRowStyle'] = jscode

    res = AgGrid(data, gridOptions=build, columns_auto_size_mode=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW, allow_unsafe_jscode=True)

    if authenticate.check_role("WRITE"):
        if st.button("Save"):
            for _, row in res.data.iterrows():
                print(
                    json.dumps(
                        {
                            'meta': {
                                'version': '1.0',
                                'triggered_from': '<service_name>',
                                'manual': 'false',
                                'user': '-'
                            },
                            'parameters': {
                                'database': st.secrets.get("snowflake").get("database"),
                                'update': {
                                    'schema_name': row["SCHEMA_NAME"],
                                    'view_name': row["VIEW_NAME"],
                                    'column_name': row["COLUMN_NAME"],
                                    'system': row["SYSTEM"],
                                    'client': row["CLIENT"],
                                    'mask_rule_name': row["MASK_RULE_NAME"], 
                                    'col_mask_key_flag': row["COL_MASK_KEY_FLAG"],
                                    'manual_column_sql': row["MANUAL_COLUMN_SQL"],
                                    'new_column_flag': row["NEW_COLUMN_FLAG"],
                                    'deleted_flag': row["DELETED_FLAG"]
                                } 
                            }
                        }
                    )
                )
else:
    st.write("Please Login")