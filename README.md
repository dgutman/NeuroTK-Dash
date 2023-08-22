# NeuroTK Dash Web Application & Python Package

## Setup (devel)
Create virtual or conda environment with Python >=3.8

(conda) 
```
$ conda create -n <env name> python
$ conda activate <env name>
```

(virtual env) 
```
$ python -m venv <env path>
$ source <env path>/bin/activate
```

Install required packages.
```
$ pip install -r requirements.txt
```

In **src** directory there is a *.env-template* file, before running rename or copy this to a file called .env and add your API key and DSA API URL.

## Running Application
```
$ docker compose up -d  # start mongo in detatched mode
$ python app.py  # run the app, runs on localhost:8050 by default
```

### Hints & Tips:
* Update requirements.txt: ```$ pip freeze > requirements.txt```
* NeuroTK main application is run in the app.py located at the root of the repository
* Additional standalone versions of the app are located in specific folders:
  * app/
  * dashApp/
  * refactor/
* src directory at the root of the repository contains the main files used by the web application 
* neurotk directory is a Python package with various useful functions used in data analysis
* algorithm directories contains the codeset used for the various CLIs created.

### Extras
#### Mean features

Web application for applying computer vision (including AI) in neuropathology digital image cohorts.
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