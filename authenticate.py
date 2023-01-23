import cognitojwt
from jose import JWTError
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from dotenv import load_dotenv
import requests
import base64
import json

# ------------------------------------
# Read constants from environment file
# ------------------------------------
load_dotenv()
cognito_secrets = st.secrets["cognito"]
COGNITO_DOMAIN = cognito_secrets.get("cognito_domain")
CLIENT_ID = cognito_secrets.get("client_id")
CLIENT_SECRET = cognito_secrets.get("client_secret")
APP_URI = cognito_secrets.get("app_uri")
POOL_ID = cognito_secrets.get("pool_id")
REGION = cognito_secrets.get("region")

cookie_manager = EncryptedCookieManager(prefix="streamlit/", password="test")

if not cookie_manager.ready():
    st.stop()

def initialise_st_state_vars():
    """
    Initialise Streamlit state variables.

    Returns:
        Nothing.
    """
    logout = st.experimental_get_query_params().get("logout")
    if "tokens" not in cookie_manager or logout is not None:
        cookie_manager["tokens"] = json.dumps({})
    if "user_groups" not in cookie_manager or logout is not None:
        cookie_manager["user_groups"] = json.dumps([])
    cookie_manager.save()


def get_auth_code():
    """
    Gets auth_code state variable.

    Returns:
        Nothing.
    """
    auth_query_params = st.experimental_get_query_params()
    try:
        auth_code = dict(auth_query_params)["code"][0]
    except (KeyError, TypeError):
        auth_code = ""

    return auth_code


def get_user_tokens(auth_code):
    """
    Gets user tokens by making a post request call.

    Args:
        auth_code: Authorization code from cognito server.

    Returns:
        {
        'access_token': access token from cognito server if user is successfully authenticated.
        'id_token': access token from cognito server if user is successfully authenticated.
        }

    """

    # Variables to make a post request
    token_url = f"{COGNITO_DOMAIN}/oauth2/token"
    client_secret_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    client_secret_encoded = str(
        base64.b64encode(client_secret_string.encode("utf-8")), "utf-8"
    )
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {client_secret_encoded}",
    }
    body = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": auth_code,
        "redirect_uri": APP_URI,
    }

    token_response = requests.post(token_url, headers=headers, data=body)
    try:
        access_token = token_response.json()["access_token"]
        id_token = token_response.json()["id_token"]
    except (KeyError, TypeError):
        access_token = ""
        id_token = ""

    return access_token, id_token


def get_user_info(access_token):
    """
    Gets user info from aws cognito server.

    Args:
        access_token: string access token from the aws cognito user pool
        retrieved using the access code.

    Returns:
        userinfo_response: json object.
    """
    userinfo_url = f"{COGNITO_DOMAIN}/oauth2/userInfo"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Authorization": f"Bearer {access_token}",
    }

    userinfo_response = requests.get(userinfo_url, headers=headers)

    return userinfo_response.json()


# Ref - https://gist.github.com/GuillaumeDerval/b300af6d4f906f38a051351afab3b95c
def pad_base64(data):
    """
    Makes sure base64 data is padded.

    Args:
        data: base64 token string.

    Returns:
        data: padded token string.
    """
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += "=" * (4 - missing_padding)
    return data

def get_user_groups(id_token):
    """
    Decode id token to get user cognito groups.

    Args:
        id_token: id token of a successfully authenticated user.

    Returns:
        user_groups: a list of all the cognito groups the user belongs to.
    """
    user_groups = []
    if id_token != "":
        header, payload, signature = id_token.split(".")
        printable_payload = base64.urlsafe_b64decode(pad_base64(payload))
        payload_dict = json.loads(printable_payload)
        try:
            user_groups = list(dict(payload_dict)["cognito:groups"])
        except (KeyError, TypeError):
            pass
    return user_groups


def activate():
    """
    Sets the streamlit state variables after user authentication.
    
    Returns:
        Nothing.
    """
    initialise_st_state_vars()
    auth_code = get_auth_code()
    access_token, id_token = get_user_tokens(auth_code)
    user_groups = get_user_groups(id_token)

    if access_token != "":
        cookie_manager["tokens"] = json.dumps({"access_token": access_token, "id_token": id_token})
        cookie_manager["user_groups"] = json.dumps(user_groups)
        cookie_manager.save()


def check_access():
    """
    Checks whether the current user is logged into Cognito

    Returns:
        bool
    """
    tokens = json.loads(cookie_manager.get("tokens"))
    if tokens is not None and "access_token" in tokens and "id_token" in tokens:
        return verify_token(tokens["id_token"])


def verify_token(id_token):
    """
    Checks if the id_token is valid and not expired yet

    Returns:
        bool
    """
    try:
        cognitojwt.decode(id_token, REGION, POOL_ID, CLIENT_ID)
        return True
    except (cognitojwt.exceptions.CognitoJWTException, JWTError) as e:
        return False


def check_role(role):
    cookie_user_groups = cookie_manager.get("user_groups")
    if cookie_user_groups is not None:
        return role in json.loads(cookie_user_groups)
    else:
        return False

# -----------------------------
# Login/ Logout HTML components
# -----------------------------
login_link = f"{COGNITO_DOMAIN}/login?client_id={CLIENT_ID}&response_type=code&scope=email+openid&redirect_uri={APP_URI}"
logout_link = f"{COGNITO_DOMAIN}/logout?client_id={CLIENT_ID}&logout_uri={APP_URI}%3Flogout=true"

html_css_login = """
<style>
.button-login {
  background-color: skyblue;
  color: white !important;
  padding: 1em 1.5em;
  text-decoration: none;
  text-transform: uppercase;
}

.button-login:hover {
  background-color: #555;
  text-decoration: none;
}

.button-login:active {
  background-color: black;
}

</style>
"""

html_button_login = (
    html_css_login
    + f"<a href='{login_link}' class='button-login' target='_self'>Log In</a>"
)
html_button_logout = (
    html_css_login
    + f"<a href='{logout_link}' class='button-login' target='_self'>Log Out</a>"
)


def button_login():
    """

    Returns:
        Html of the login button.
    """
    return st.sidebar.markdown(f"{html_button_login}", unsafe_allow_html=True)


def button_logout():
    """

    Returns:
        Html of the logout button.
    """
    return st.sidebar.markdown(f"{html_button_logout}", unsafe_allow_html=True)



