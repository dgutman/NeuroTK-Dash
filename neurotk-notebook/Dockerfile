FROM python:3.9
RUN pip install ipython-sql sqlalchemy jupyter pandas geopandas matplotlib dask plotly girder_client pymongo

RUN pip install large-image[all] --find-links https://girder.github.io/large_image_wheels

RUN python -m pip install "dask[distributed]" --upgrade 

EXPOSE 8888
RUN mkdir /app
WORKDIR /app

COPY jupyter_notebook_config.json /root/.jupyter/jupyter_notebook_config.json

ENTRYPOINT [ "jupyter","notebook","--allow-root","--ip","0.0.0.0", "--NotebookApp.token=''", "--NotebookApp.password=''" ]
