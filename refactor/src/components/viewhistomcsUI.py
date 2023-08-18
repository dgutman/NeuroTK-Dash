### This will create an iframe and load/interact with histomics UI.. tada!
from dash import html



histomicsui_layout = html.Iframe(src="https://megabrain.neurology.emory.edu/histomicstk",id="histomicsui_iframe",
                style={"height": "1067px", "width": "100%"})


