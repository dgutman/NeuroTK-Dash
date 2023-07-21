from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import SimpleITK as sitk
from PIL import Image
import numpy as np
import dash_bootstrap_components as dbc
import base64, io, dash

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

image_path1 = "./assets/E20-9_1.HE.svs_thumb_1024.jpg"
image_path2 = "./assets/E20-9_1.p62.svs_thumb_1024.jpg"

simpleImageOverlay_layout = html.Div(
    style={"position": "relative", "width": "500px", "height": "600px"},
    children=[
        html.Div(
            id="image-container",
            style={
                "position": "absolute",
                "top": 0,
                "left": 0,
                "width": "100%",
                "height": "500px",
            },
            children=[
                html.Img(
                    src=image_path1,
                    id="image1",
                    style={
                        "position": "absolute",
                        "top": 0,
                        "left": 0,
                        "width": "100%",
                        "height": "100%",
                    },
                ),
                html.Img(
                    id="image2",
                    src=image_path2,
                    style={
                        "position": "absolute",
                        "top": 0,
                        "left": 0,
                        "width": "100%",
                        "height": "100%",
                    },
                ),
            ],
        ),
        html.Div(
            id="slider-container",
            style={
                "position": "absolute",
                "bottom": 0,
                "left": 0,
                "width": "100%",
                "height": "100px",
            },
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
                dbc.Col(id="input-image-reference", width=4),
                dbc.Col(id="input-image-moving", width=4),
                dbc.Col(id="output-image-register", width=4),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H3("Simple Image Overlay"),
                                            simpleImageOverlay_layout,
                                        ]
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                    width=12,
                ),
            ]
        ),
    ]
)

from SimpleITK import ElastixImageFilter


def register_images(fixed_image, moving_image):
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



@app.callback(
    [Output('input-image-reference', 'children'),
     Output('input-image-moving', 'children'),
     Output('output-image-register', 'children')],
    [Input('load-register', 'n_clicks')])
def register_images(n):
    if n > 0:
        # Load the reference and moving images
        reference_image = sitk.ReadImage('path_to_reference_image')
        moving_image = sitk.ReadImage('path_to_moving_image')

        # Create an instance of the ElastixImageFilter
        elastix_filter = ElastixImageFilter()
        elastix_filter.SetFixedImage(reference_image)
        elastix_filter.SetMovingImage(moving_image)

        # Set the parameters for the image registration
        elastix_filter.SetParameterMap(sitk.GetDefaultParameterMap('affine'))
        elastix_filter.Execute()

        # Get the registered image
        registered_image = elastix_filter.GetResultImage()

        # Convert the images to a format suitable for display
        reference_image_disp = sitk_to_pil(reference_image)
        moving_image_disp = sitk_to_pil(moving_image)
        registered_image_disp = sitk_to_pil(registered_image)

        # Display the images
        return generate_image_html(reference_image_disp), \
               generate_image_html(moving_image_disp), \
               generate_image_html(registered_image_disp)

    return None, None, None


def sitk_to_pil(sitk_image):
    # Convert the SimpleITK image to a PIL image
    np_array = sitk.GetArrayFromImage(sitk_image)
    pil_image = Image.fromarray(np_array)
    return pil_image


def generate_image_html(pil_image):
    # Convert the PIL image to a base64 encoded string
    buffered = io.BytesIO()
    pil_image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # Generate the HTML for the image
    return html.Img(src=f'data:image/jpeg;base64,{img_str}', style={'height':'100%', 'width':'100%'})



@app.callback(
    Output("image2", "style"),
    [Input("opacity-slider", "value")],
)
def update_opacity(value):
    return {
        "position": "absolute",
        "top": 0,
        "left": 0,
        "width": "100%",
        "height": "100%",
        "opacity": value,
    }

if __name__ == "__main__":
    app.run_server(debug=True)
