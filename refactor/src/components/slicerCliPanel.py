import dash
import dash_core_components as dcc
import dash_html_components as html
import xml.etree.ElementTree as ET
import json
from dash import Output, Input, State


def generate_dash_layout_from_slicer_cli(xml_string):
    root = ET.fromstring(xml_string)

    components = []

    for param in root.findall(".//parameters"):
        label = param.find("label").text if param.find("label") is not None else ""
        components.append(html.H3(label))

        for image in param.findall("image"):
            name = image.find("name").text if image.find("name") is not None else ""
            label = image.find("label").text if image.find("label") is not None else ""
            components.append(html.Label(label))
            components.append(dcc.Upload(id=name))

        for region in param.findall("region"):
            name = region.find("name").text if region.find("name") is not None else ""
            label = (
                region.find("label").text if region.find("label") is not None else ""
            )
            default = (
                region.find("default").text
                if region.find("default") is not None
                else ""
            )
            components.append(html.Label(label))
            components.append(dcc.Input(id=name, value=default, type="text"))

        for enum in param.findall("string-enumeration"):
            name = enum.find("name").text if enum.find("name") is not None else ""
            label = enum.find("label").text if enum.find("label") is not None else ""
            options = [elem.text for elem in enum.findall("element")]
            components.append(html.Label(label))
            components.append(
                dcc.Dropdown(
                    id=name,
                    options=[{"label": op, "value": op} for op in options],
                    value=options[0],
                )
            )

        for vector in param.findall("double-vector"):
            name = vector.find("name").text if vector.find("name") is not None else ""
            label = (
                vector.find("label").text if vector.find("label") is not None else ""
            )
            default = (
                vector.find("default").text
                if vector.find("default") is not None
                else ""
            )
            components.append(html.Label(label))
            components.append(dcc.Input(id=name, value=default, type="text"))

        # New code for float fields
        for flt in param.findall("float"):
            name = flt.find("name").text if flt.find("name") is not None else ""
            label = flt.find("label").text if flt.find("label") is not None else ""
            default = (
                flt.find("default").text if flt.find("default") is not None else ""
            )
            components.append(html.Label(label))
            components.append(dcc.Input(id=name, value=default, type="number"))

    #    print(components)
    components.append(html.Button("Submit CLI Task", id="SubmitCLITask"))

    # Add a Div to display the JSON result
    components.append(html.Div(id="cli_output"))

    return html.Div(components)


xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n<executable>\n  <category>HistomicsTK</category>\n  <title>Positive Pixel Count</title>\n  <description>Counts different types of positive pixels based on values in the HSI color space</description>\n  <version>0.1.0</version>\n  <documentation-url>https://digitalslidearchive.github.io/HistomicsTK</documentation-url>\n  <license>Apache 2.0</license>\n  <contributor>David Manthey (Kitware), Neal Siekierski (Kitware)</contributor>\n  <acknowledgements>This work is part of the HistomicsTK project.</acknowledgements>\n  <parameters>\n    <label>I/O</label>\n    <description>Input/output parameters.</description>\n    <image>\n      <name>inputImageFile</name>\n      <label>Input Image</label>\n      <channel>input</channel>\n      <index>0</index>\n      <description>Input image in which to count and classify positive pixels</description>\n    </image>\n    <region shapes="rectangle,polygon,multipolygon">\n      <name>region</name>\n      <label>Analysis ROI</label>\n      <longflag>region</longflag>\n      <description>Region of interest where analysis is performed.  This is either -1,-1,-1,-1 for the whole image, or a four-element vector in the format "left, top, width, height", or a list of four or more x,y vertices to specify a polygon.</description>\n      <default>-1,-1,-1,-1</default>\n    </region>\n    <float>\n      <name>hue_value</name>\n      <label>Hue Value</label>\n      <index>1</index>\n      <description>Center of the hue range in HSI space for the positive color, in the range [0, 1]</description>\n      <default>0.83</default>\n    </float>\n    <float>\n      <name>hue_width</name>\n      <label>Hue Width</label>\n      <index>2</index>\n      <description>Width of the hue range in HSI space</description>\n      <default>0.15</default>\n    </float>\n    <float>\n      <name>saturation_minimum</name>\n      <label>Minimum Saturation</label>\n      <index>3</index>\n      <description>Minimum saturation of positive pixels in HSI space, in the range [0, 1]</description>\n      <default>0.05</default>\n    </float>\n    <float>\n      <name>intensity_upper_limit</name>\n      <label>Upper Intensity Limit</label>\n      <index>4</index>\n      <description>Intensity threshold in HSI space above which a pixel is considered negative, in the range [0, 1]</description>\n      <default>0.95</default>\n    </float>\n    <float>\n      <name>intensity_weak_threshold</name>\n      <label>Intensity Threshold for Weak Pixels</label>\n      <index>5</index>\n      <description>Intensity threshold in HSI space that separates weak-positive pixels (above) from plain positive pixels (below)</description>\n      <default>0.65</default>\n    </float>\n    <float>\n      <name>intensity_strong_threshold</name>\n      <label>Intensity Threshold for Strong Pixels</label>\n      <index>6</index>\n      <description>Intensity threshold in HSI space that separates plain positive pixels (above) from strong positive pixels (below)</description>\n      <default>0.35</default>\n    </float>\n    <float>\n      <name>intensity_lower_limit</name>\n      <label>Lower Intensity Limit</label>\n      <index>7</index>\n      <description>Intensity threshold in HSI space below which a pixel is considered negative</description>\n      <default>0.05</default>\n    </float>\n    <image fileExtensions=".tiff" reference="inputImageFile">\n      <name>outputLabelImage</name>\n      <longflag>outputLabelImage</longflag>\n      <label>Output Label Image</label>\n      <description>Color-coded image of the region, showing the various classes of pixel</description>\n      <channel>output</channel>\n    </image>\n    <string-enumeration>\n      <name>outputImageForm</name>\n      <label>Image Format</label>\n      <description>The output image can either be colored for easy visibility or coded as categorical values where 0 is negative, 1 weak, 2 plain, and 3 strong</description>\n      <channel>input</channel>\n      <longflag>output_form</longflag>\n      <element>visible</element>\n      <element>pixelmap</element>\n      <default>visible</default>\n    </string-enumeration>\n    <file fileExtensions=".anot" reference="inputImageFile">\n      <name>outputAnnotationFile</name>\n      <label>Image Annotation</label>\n      <description>Annotation to relate the image to the source (*.anot)</description>\n      <channel>output</channel>\n      <longflag>image_annotation</longflag>\n    </file>\n  </parameters>\n  <parameters advanced="true">\n    <label>Frame and Style</label>\n    <description>Frame parameters</description>\n    <string>\n      <name>frame</name>\n      <longflag>frame</longflag>\n      <label>Frame Index</label>\n      <description>Frame index in a multi-frame image</description>\n      <default>{#control:#current_image_frame#}</default>\n    </string>\n    <string>\n      <name>style</name>\n      <longflag>style</longflag>\n      <label>Style Options</label>\n      <description>Image style options for compositing a multi-frame image</description>\n      <default>{#control:#current_image_style#}</default>\n    </string>\n  </parameters>\n  <parameters advanced="true">\n    <label>Dask</label>\n    <description>Dask parameters</description>\n    <string>\n      <name>scheduler</name>\n      <label>Scheduler Address</label>\n      <description>Address of a dask scheduler in the format \'127.0.0.1:8786\'.  Not passing this parameter sets up a dask cluster on the local machine.  \'multiprocessing\' uses Python multiprocessing.  \'multithreading\' uses Python multiprocessing in threaded mode.</description>\n      <longflag>scheduler</longflag>\n      <default></default>\n    </string>\n    <integer>\n      <name>num_workers</name>\n      <label>Number of workers</label>\n      <description>Number of dask workers to start while setting up a local cluster internally. If a negative value is specified then the number of workers is set to number of cpu cores on the machine minus the number of workers specified.</description>\n      <longflag>num_workers</longflag>\n      <default>-1</default>\n    </integer>\n    <integer>\n      <name>num_threads_per_worker</name>\n      <label>Number of threads per worker</label>\n      <description>Number of threads to use per worker while setting up a local cluster internally. Must be a positive integer >= 1.</description>\n      <longflag>num_threads_per_worker</longflag>\n      <default>1</default>\n    </integer>\n  </parameters>\n</executable>\n\n'.replace(
    "\n", ""
)

trimmed_xml_content = xml_content.strip()

# Example usage
app = dash.Dash(__name__)
xml_content = """..."""  # Your XML content here
app.layout = generate_dash_layout_from_slicer_cli(trimmed_xml_content)


# Callback to generate the JSON result
@app.callback(
    Output("cli_output", "children"),
    Input("SubmitCLITask", "n_clicks"),
    # Assuming all IDs are unique and they match the names in the XML,
    # dynamically generate the list of State objects
    [
        State(component_id, "value")
        for component_id in [
            "inputImageFile",
            "region",
            "stain_1",
            "stain_1_vector",
            "stain_2",
            "stain_2_vector",
            "stain_3",
            "hue_value",
            "hue_width",
            "saturation_minimum",
            "intensity_upper_limit",
            "intensity_weak_threshold",
            "intensity_strong_threshold",
            "intensity_lower_limit",
            "outputImageForm",
            "frame",
            "style",
            "scheduler",
            # "num_workers",
            # "num_threads_per_worker",
        ]
    ],
)
def generate_cli_output(n_clicks, *args):
    if not n_clicks:
        return ""

    # Map names to values
    names = [
        "inputImageFile",
        "region",
        "stain_1",
        "stain_1_vector",
        "stain_2",
        "stain_2_vector",
        "stain_3",
        "hue_value",
        "hue_width",
        "saturation_minimum",
        "intensity_upper_limit",
        "intensity_weak_threshold",
        "intensity_strong_threshold",
        "intensity_lower_limit",
        "outputImageForm",
        "frame",
        "style",
        "scheduler",
        "num_workers",
        "num_threads_per_worker",
    ]
    result = {name: value for name, value in zip(names, args)}

    return html.Pre(json.dumps(result, indent=4))


if __name__ == "__main__":
    app.run_server(debug=True)
