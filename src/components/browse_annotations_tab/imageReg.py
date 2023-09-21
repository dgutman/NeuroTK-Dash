import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import SimpleITK as sitk
from PIL import Image
import numpy as np
import dash_bootstrap_components as dbc
import base64, io
import plotly.graph_objects as go



# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

image_path1 = "./assets/E20-9_1.HE.svs_thumb_1024.jpg"
image_path2 = "./assets/E20-9_1.p62.svs_thumb_1024.jpg"

overlay_box_style = {"position": "relative", "width": "400px", "height": "500px"}
# overlay_box_style = {"position":"relative"}

overlay_image_layout = html.Div(
    style=overlay_box_style,
    children=[
        html.Div(
            id="image-container",
            style={"position": "absolute", "top": 0, "left": 0, "width": "100%", "height": "400px"},
            children=[
                html.Img(
                    id="image1",
                    src=image_path1,
                    style={"position": "absolute", "top": 0, "left": 0, "width": "100%", "height": "100%"},
                ),
                html.Img(
                    id="image2",
                    src=image_path2,
                    style={"position": "absolute", "top": 0, "left": 0, "width": "100%", "height": "100%"},
                ),
            ],
        ),
        html.Div(
            id="slider-container",
            style={"position": "absolute", "bottom": 0, "left": 0, "width": "100%", "height": "100px"},
            children=[
                html.Label("Opacity", style={"textAlign": "center"}),
                html.Div(
                    style={"width": "100%"},
                    children=[
                        dcc.Slider(
                            id="opacity-slider",
                            min=0,
                            max=1,
                            step=0.1,
                            value=1,
                        )
                    ],
                ),
            ],
        ),
    ],
)
# Define the layout of the app
app.layout = html.Div(
    [
        html.Button("Load and register images", id="load-register", n_clicks=0),
        dbc.Row(
            [
                dbc.Col(overlay_image_layout, width=3),
                dbc.Col(id="input-image-reference", width=3),
                dbc.Col(id="input-image-moving", width=3),
                dbc.Col(id="output-image-register", width=3),
                   dbc.Col(id="output-affine-transform", width=2)
            ]
        ),
       
    ],
)



@app.callback(Output("image2", "style"), [Input("opacity-slider", "value")], [State("image2", "style")])
def update_image2_opacity(opacity, style):
    style.update({"opacity": opacity})
    return style


def register_images(fixed_image, moving_image):
    
    # Convert to grayscale
    fixed_gray = np.dot(fixed_image[..., :3], [0.2989, 0.5870, 0.1140])
    moving_gray = np.dot(moving_image[..., :3], [0.2989, 0.5870, 0.1140])

    fixed_image = sitk.GetImageFromArray(fixed_gray, isVector=False)
    moving_image = sitk.GetImageFromArray(moving_gray, isVector=False)
    
    initial_transform = sitk.CenteredTransformInitializer(
        fixed_image,
        moving_image,
        sitk.Euler2DTransform(),
        sitk.CenteredTransformInitializerFilter.GEOMETRY,
    )

    registration_method = sitk.ImageRegistrationMethod()

    # Similarity metric settings.
    registration_method.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
    registration_method.SetMetricSamplingPercentage(0.01)

    registration_method.SetInterpolator(sitk.sitkLinear)

    # Optimizer settings.
    registration_method.SetOptimizerAsGradientDescent(
        learningRate=1.0,
        numberOfIterations=100,
        convergenceMinimumValue=1e-6,
        convergenceWindowSize=10,
    )
    registration_method.SetOptimizerScalesFromPhysicalShift()

    # Setup for the multi-resolution framework.
    registration_method.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
    registration_method.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
    registration_method.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

    # Don't optimize in-place, we would possibly like to run this cell multiple times.
    registration_method.SetInitialTransform(initial_transform, inPlace=False)

    final_transform = registration_method.Execute(
        sitk.Cast(fixed_image, sitk.sitkFloat32),
        sitk.Cast(moving_image, sitk.sitkFloat32),
    )

    return final_transform


def load_image(image_path):
    image = Image.open(image_path)
    return np.array(image)

def resampleImage(fixed_image, moving_image, transform, outputGray=False):

    # For now, I have to make everything grayscale so xfm works..
    fixed_image = np.dot(fixed_image[..., :3], [0.2989, 0.5870, 0.1140])
    moving_image = np.dot(moving_image[..., :3], [0.2989, 0.5870, 0.1140])

    # Convert to SimpleITK images
    fixed_image = sitk.GetImageFromArray(fixed_image)
    moving_image = sitk.GetImageFromArray(moving_image)

    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(fixed_image)
    resampler.SetInterpolator(sitk.sitkLinear)
    resampler.SetDefaultPixelValue(100)
    resampler.SetTransform(transform)

    out = resampler.Execute(moving_image)
    return out




# Define the callback for loading and registering images
@app.callback(
    Output("input-image-reference", "children"),
    Output("input-image-moving", "children"),
    Output("output-image-register", "children"),
    Output("image2", "src"),
    Output("output-affine-transform", "children"),
    [Input("load-register", "n_clicks"), Input("opacity-slider", "value")],
    prevent_initial_call=True,
)
def update_output(n_clicks, opacity_value):
    # Paths to your images - replace these with the actual paths to your images

    img1_array = load_image(image_path1)
    img2_array = load_image(image_path2)
 
    transform = register_images(img1_array, img2_array)
    out = resampleImage( img1_array, img2_array, transform)

    resampled_img = sitk.GetArrayFromImage(out)

    fig1 = px.imshow(img1_array)#,# color_continuous_scale="gray")
    fig2 = px.imshow(img2_array)#, color_continuous_scale="gray")

    fig3 = go.Figure(
        go.Heatmap(
            z=np.flipud(resampled_img),#.T,
            colorscale="gray",
            showscale=False  # This line removes the color bar
        )
    )
    
    input_image_reference = html.Div(
        [
            html.H3("Reference"),
            dcc.Graph(figure=fig1,style={"width": "100%", "height": "100%"}),
        ]
    )

    input_image_moving = html.Div(
        [
            html.H3("Moving"),
            dcc.Graph(figure=fig2),
        ]
    )

    output_images = html.Div(
        [
            html.H3("Registered"),
            dcc.Graph(figure=fig3),
        ]
    )

    # Display the affine transform parameters
    affine_params = transform.GetParameters()
    affine_transform_display = html.Div(
    [
        html.H3("Affine Transform Parameters", style={"color": "white", "background-color": "blue", "padding": "10px", "text-align": "center"}),
        html.P(f"Translation: {affine_params[0]}, {affine_params[1]}", style={"padding": "10px"}),
        html.P(f"Rotation: {affine_params[2]}", style={"padding": "10px"}),
    ],
    style={"border": "2px solid blue", "border-radius": "15px", "padding": "10px", "margin-top": "15px"}
        )

    img_io = io.BytesIO()
    Image.fromarray(resampled_img).convert("RGB").save(img_io, "JPEG", quality=95)
    b64image = base64.b64encode(img_io.getvalue()).decode("utf-8")

    return (
        input_image_reference,
        input_image_moving,
        output_images,
        "data:image/jpeg;base64," + b64image,
        affine_transform_display,
    )

if __name__ == "__main__":
    app.run_server(debug=True)
