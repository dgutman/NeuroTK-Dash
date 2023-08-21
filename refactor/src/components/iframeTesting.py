from flask import Flask, session, Response
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import requests
from flask_cors import CORS

server = Flask(__name__)
CORS(server)
server.secret_key = "your_secret_key"

app = dash.Dash(__name__, server=server)

app.layout = html.Div(
    [
        html.Button("Generate Token", id="generate-token-btn"),
        html.Iframe(id="my-iframe", src="/proxy_endpoint", width="100%", height="500"),
    ]
)


girder_token = "v1hpkI3hZSxMoYCOyvCILx3NFKG8MfNBgxr2Ue4V"


@app.callback(Output("my-iframe", "src"), Input("generate-token-btn", "n_clicks"))
def generate_token(n_clicks):
    print(n_clicks)
    if n_clicks:
        # Store your Girder token in the session
        session["girder_token"] = girder_token
    return "/proxy_endpoint"


# @server.route("/proxy_endpoint")
# def proxy_endpoint():
#     token = session.get("girder_token")
#     if not token:
#         return "Please generate a token first."

#     # Make a request to the external source with the token
#     response = requests.get(
#         "https://megabrain.neurology.emory.edu/",
#         headers={
#             "Girder-Token": girder_token
#         },  # Adjust this based on how HistomicsTK expects the token
#     )

#     # Relay the response back to the iframe
#     return Response(response.content, content_type=response.headers["content-type"])

import re


@server.route("/proxy_endpoint")
def proxy_endpoint():
    token = session.get("girder_token")
    if not token:
        return "Please generate a token first."

    # Make a request to the external source with the token
    response = requests.get(
        "https://megabrain.neurology.emory.edu/", headers={"Girder-Token": girder_token}
    )

    # Rewrite relative URLs to absolute ones
    content = response.content.decode("utf-8")
    content = re.sub(
        r"http://localhost:8050/", r"https://megabrain.neurology.emory.edu/", content
    )

    content = re.sub(
        r'href="/', r'href="https://megabrain.neurology.emory.edu/', content
    )
    content = re.sub(r'src="/', r'src="https://megabrain.neurology.emory.edu/', content)

    if "static" in content:
        print(content)

    content = re.sub(
        r'"static/', r'"https://megabrain.neurology.emory.edu/static/', content
    )

    # content_type = response.headers.get("content-type", "")
    # if (
    #     "text/html" in content_type
    #     or "text/css" in content_type
    #     or "application/javascript" in content_type
    # ):
    #     content = response.content.decode("utf-8")
    #     content = re.sub(
    #         r'"/api/v1', r'"https://megabrain.neurology.emory.edu/api/v1', content
    #     )  # Example rewrite

    # Relay the modified content back to the iframe
    return Response(content, content_type=response.headers["content-type"])


# @server.route("/proxy_endpoint")
# def proxy_endpoint():
#     token = session.get("girder_token")
#     if not token:
#         return "Please generate a token first."

#     # Make a request to the external source with the token
#     response = requests.get(
#         "https://megabrain.neurology.emory.edu/", headers={"Girder-Token": girder_token}
#     )

#     # Debug: Print out the first 500 characters of the response to see what you're getting
#     print(response.content[:500])

#     # Relay the response back to the iframe
#     return Response(response.content, content_type=response.headers["content-type"])


if __name__ == "__main__":
    app.run_server(debug=True)
