import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import SimpleITK as sitk
from PIL import Image
import numpy as np
import dash_bootstrap_components as dbc

# added by ek ------------------------------------------
import cv2 as cv 
from utils import get_item_rois
import plotly.graph_objects as go
# ------------------------------------------------------

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

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
                            html.H3("Opacity Slider"),
                            dcc.Slider(id="opacity-slider", min=0, max=1, step=0.1, value=0.5),
                            html.Div(id="output-overlay-image"),
                        ]
                    ),
                    width=4,
                ),
                dbc.Col(id="output-affine-transform", width=4),
                dbc.Col(id="output-ek-rect", width=4), # added by ek
            ],
        ),
    ],
)


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


def load_image(image_path):
    image = Image.open(image_path)
    return np.array(image)


# Define the callback for loading and registering images
@app.callback(
    Output("input-image-reference", "children"),
    Output("input-image-moving", "children"),
    Output("output-image-register", "children"),
    Output("output-overlay-image", "children"),
    Output("output-ek-rect", "children"), # added by ek
    Output("output-affine-transform", "children"),
    [Input("load-register", "n_clicks"), Input("opacity-slider", "value")],
    prevent_initial_call=True,
)
def update_output(n_clicks, opacity_value):
    # Paths to your images - replace these with the actual paths to your images
    image_path1 = "./assets/E20-9_1.HE.svs_thumb_1024.jpg"
    image_path2 = "./assets/E20-9_1.p62.svs_thumb_1024.jpg"
    
    # added by ek ------------------------------------------
    beils_image_id = "641bfd93867536bb7a236b9a" 
    rois = get_item_rois(beils_image_id, "ManualGrayMatter")
    beils_gray_matter = [np.asarray(val["points"])[..., :2] for val in rois]
    # ------------------------------------------------------

    img1_array = load_image(image_path1)
    img2_array = load_image(image_path2)

    # Convert to grayscale
    img1_gray = np.dot(img1_array[..., :3], [0.2989, 0.5870, 0.1140])
    img2_gray = np.dot(img2_array[..., :3], [0.2989, 0.5870, 0.1140])

    fixed_image = sitk.GetImageFromArray(img1_gray, isVector=False)
    moving_image = sitk.GetImageFromArray(img2_gray, isVector=False)

    transform = register_images(fixed_image, moving_image)
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(fixed_image)
    resampler.SetInterpolator(sitk.sitkLinear)
    resampler.SetDefaultPixelValue(100)
    resampler.SetTransform(transform)

    out = resampler.Execute(moving_image)
    resampled_img = sitk.GetArrayFromImage(out)

    fig1 = px.imshow(img1_array, color_continuous_scale="gray")
    fig2 = px.imshow(img2_array, color_continuous_scale="gray")
    fig3 = px.imshow(resampled_img, color_continuous_scale="gray")

    # added by ek ------------------------------------------
    # img1_y, img1_x, _ = img1_array.shape
    # img1_array = img1_array.astype(np.uint8)
    # img1_array = cv.rectangle(img1_array, (int(img1_x * 0.25), int(img1_y * 0.25)), (int(img1_x * 0.75), int(img1_y * 0.75)), [255, 0, 0], 5)
    # fig5 = px.imshow(img1_array, color_continuous_scale="gray")

    fig5 = go.Figure(px.imshow(img1_array, color_continuous_scale="gray"))
    for val in beils_gray_matter:
        fig5.add_trace(go.Scatter(x=val[:,0], y=val[:,1]))
    
    # # Creating a figure object
    # fig5 = go.Figure()
    # # Adding an image trace to the figure with the image array and the color domain
    # fig5.add_trace(go.Image(z=img1_array, zmin=[0, 0, 0, 0], zmax=[255, 255, 255, 255]))
    # # Looping through the vals list and adding a scatter trace for each element with the x and y coordinates and the mode
    # for val in beils_gray_matter:
    #     fig5.add_trace(go.Scatter(x=val[:,0], y=val[:,1], mode="lines"))
    # # Updating the layout of the figure to show the image in its original size and orientation by setting the xaxis and yaxis ranges, scaleanchor and constrain attributes and the margin
    # fig5.update_layout(xaxis=dict(showgrid=False, range=[0, img1_array.shape[1]], constrain="domain"),
    #                    yaxis=dict(showgrid=False, range=[img1_array.shape[0], 0], scaleanchor="x", constrain="domain"),
    #                    margin=dict(l=0, r=0, t=0, b=0))

    # ------------------------------------------------------

    # overlay images
    img1_gray_rescaled = (img1_gray * 255 / img1_gray.max()).astype(np.uint8)
    resampled_img_rescaled = (resampled_img * 255 / resampled_img.max()).astype(np.uint8)
    overlay_img = (img1_gray_rescaled * (1.0 - opacity_value) + resampled_img_rescaled * opacity_value).astype(
        np.uint8
    )
    fig4 = px.imshow(overlay_img, color_continuous_scale="gray")

    overlay_image = html.Div(
        [
            html.H3("Overlay"),
            dcc.Graph(figure=fig4),
        ]
    )

    input_image_reference = html.Div(
        [
            html.H3("Reference"),
            dcc.Graph(figure=fig1),
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
    
    # added by ek ------------------------------------------
    ek_graph = html.Div(
        [
            html.H3("Generalize Annot from Beils"),
            dcc.Graph(figure=fig5),
        ]
    )
    # ------------------------------------------------------

    # Display the affine transform parameters
    affine_params = transform.GetParameters()
    affine_transform_display = html.Div(
        [
            html.H3("Affine Transform Parameters"),
            html.P(f"Translation: {affine_params[0]}, {affine_params[1]}"),
            html.P(f"Rotation: {affine_params[2]}"),
        ]
    )

    return (
        input_image_reference,
        input_image_moving,
        output_images,
        overlay_image,
        ek_graph, # added by ek
        affine_transform_display,
    )


if __name__ == "__main__":
    app.run_server(debug=True)
