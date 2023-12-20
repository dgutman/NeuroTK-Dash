# NeuroTK Web Application
Neuropathology project defining and large scale analysis using computational approaches. Utilizes the Digital Slide Archive ([DSA](https://github.com/DigitalSlideArchive)) for data storage and API (application programming interface) for its backend. Front-end is built using Dash Plotly and local database is hosted using MongoDB for faster performance. The Mongo database is run using Docker compose and the application is run using Python.

## Requirements
* Python 3.10 or greater
  - To install required Python packages: ```$ python install -r requirements.txt```
* [Docker](https://docs.docker.com/engine/install/) installed

## Instructions
* Clone this repository (i.e. ```$ git clone https://github.com/dgutman/NeuroTK-Dash.git```)
* Navigate to cloned directory
* Create Mongo database with Docker compose:
  - ```$ docker compose build```
  - ```$ docker compose up -d```
    * "-d" runs container in detached mode
* Copy environmental template file to .env: ```$ cp src/.env-template src/.env```
  - Modify file as needed
* Run application: ```$ python app.py```
* App is hosted on http://localhost:8050/