# NeuroTK Web Application
Neuropathology project defining and large scale analysis using computational approaches. Utilizes the Digital Slide Archive ([DSA](https://github.com/DigitalSlideArchive)) for data storage and API (application programming interface) for its backend. Front-end is built using Dash Plotly and local database is hosted using MongoDB for faster performance. The Mongo database is run using Docker compose and the application is run using Python.

## Setup & Installation
Requirements:
* Python 3.10 or greater
* [Docker](https://docs.docker.com/engine/install/) installed

Instructions:
* Clone this repository
* In the root of the directory do the following to create the Mongo database:
  - ```$ docker compose install```
  - ```$ docker compose up -d```
* In the root of the repository: ```$ python install -r requirements.txt```
  - recommended to do this in a Python environment
* In the root of the repository: ```$ python app.py```
* App is hosted on http://localhost:8050/

Additional setup:
* In src directory there is a .env-template file. Rename or copy this to a .env file in the same location and set parameters to run your application, including URL to host at, port, API key for login (if not wanting to do this interactively), DSA API URL, and more.

## Tutorial
Tutorial on how to run the application will be coming. Also, to allow users to test the application easily, we will try to setup a dummy DSA instance with some de-identified images. Or setup instructions on how to set this up yourself.