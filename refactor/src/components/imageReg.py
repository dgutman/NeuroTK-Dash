import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import SimpleITK as sitk
from PIL import Image
import numpy as np

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div(
    [
        html.Button("Load and register images", id="load-register", n_clicks=0),
        html.Div(id="output-image-register"),
    ]
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
    Output("output-image-register", "children"),
    [Input("load-register", "n_clicks")],
    prevent_initial_call=True,
)
def update_output(n_clicks):
    # Paths to your images - replace these with the actual paths to your images
    image_path1 = "./assets/E20-9_1.HE.svs_thumb_1024.jpg"
    image_path2 = "./assets/E20-9_1.p62.svs_thumb_1024.jpg"

    img1_array = load_image(image_path1)
    img2_array = load_image(image_path2)

    # Convert to grayscale
    img1_gray = np.dot(img1_array[..., :3], [0.2989, 0.5870, 0.1140])
    img2_gray = np.dot(img2_array[..., :3], [0.2989, 0.5870, 0.1140])

    fixed_image = sitk.GetImageFromArray(img1_gray, isVector=False)
    moving_image = sitk.GetImageFromArray(img2_gray, isVector=False)

    # fixed_image = sitk.GetImageFromArray(img1_array, isVector=False)
    # moving_image = sitk.GetImageFromArray(img2_array, isVector=False)

    transform = register_images(fixed_image, moving_image)
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(fixed_image)
    resampler.SetInterpolator(sitk.sitkLinear)
    resampler.SetDefaultPixelValue(100)
    resampler.SetTransform(transform)

    out = resampler.Execute(moving_image)
    resampled_img = sitk.GetArrayFromImage(out)

    fig1 = px.imshow(img1_array, color_continuous_scale="gray")
    fig2 = px.imshow(resampled_img, color_continuous_scale="gray")

    return html.Div(
        [
            dcc.Graph(figure=fig1),
            dcc.Graph(figure=fig2),
        ]
    )


if __name__ == "__main__":
    app.run_server(debug=True)
