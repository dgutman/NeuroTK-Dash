# NeuroTK-Dash

Dashboard and plotly/dash app for interacting with DSA and NeuroTK functions

## Getting started for debug and development

python -m venv .pyenv
source .pyenv/bin/activate

pip install -r requirements.txt



##### Updating package list during debug or if I added soemthing new and exciting
pip freeze > requirements.txt


### Mean features

Web application for applying computer vision (including AI) in neuropathology digital image cohorts.

## What is in this current stack

#### Dash App

There are several components, including a Dash application https://plotly.com/dash/

This will serve as the main app / dashboard for interacting with the DSA.

This should be running at http://localhost:8050

#### Backend database PostGIS

This is a postgres database with the pgvector and postgis extensions. This is used to cache certain queries, and/or for future work related to spatial queries

#### Backend database MONGODB

To simplify things, I have another service running mongodb. Since the DSA itself uses a mongodatabase, this makes it MUCH easier to cache DSA queries locally. Also there are some cases where having a NoSQL database to stuff data into is easier than a full relational database (e.g. PostGres)

#### Jupyter notebook

Another service at http://127.0.0.1:8888 is running a jupyter notebook instance. This is for local debugging, database queries and/or development

## Getting started

docker compose up

*NOTE:* If the app hangs after running `python3 app.py` and gives no error, etc. ensure you are in the network and/or VPN is on and running as expected.

## Files by Function

 - src
  - components
    - imageSetViewer.py: generates panels which visualize the images related to the selection/filters applied to the main table in "Item Set Datatable"
    - statsGraph.py: generates graph/table which give counts of stainID and regionName
    - annotationViewPanel.py: code for pulling and plotting annotations, including existing annotations and any being generalized
  - pages
    - home.py: generates home page, including building and populating the main table in "Item Set Datatable"
  - utils
    - api.py: various functions used to interact with the DSA/girder client