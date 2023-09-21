# Download images locally.
import sys

sys.path.append("../..")

from argparse import ArgumentParser
from tqdm import tqdm
import numpy as np
from PIL import Image
from io import BytesIO

from neurotk.utils import get_filename
from neurotk import login, imwrite
from neurotk.girder_utils import get_tile_metadata

from os import makedirs
from os.path import join


def parse_args():
    """CLI arguments."""
    parser = ArgumentParser()

    parser.add_argument("--user", type=str, default=None, help="DSA username.")
    parser.add_argument("--password", type=str, default=None, help="DSA password.")
    parser.add_argument(
        "--fld-id",
        type=str,
        default="650887979a8ab9ec771ba678",
        help="DSA folder ID with images of interest.",
    )
    parser.add_argument(
        "--save-dir", type=str, default=".", help="Location to save images."
    )
    parser.add_argument(
        "--api-url",
        type=str,
        help="DSA API URL.",
        default="http://glasslab.neurology.emory.edu:8080/api/v1",
    )

    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()

    # Authenticate client.
    gc = login(args.api_url, username=args.user, password=args.password)

    # Create location to save images.
    makedirs(args.save_dir, exist_ok=True)

    # Loop through all the images.
    for item in tqdm(list(gc.listItem(args.fld_id))):
        # Read the metadata to identify the nuclei/DAPI channel.
        channels = item.get("meta", {}).get("Channels", {})

        # Look for nuclei channel.
        channel = None

        for k, v in channels.items():
            if v == "Nuclei":
                channel = k
                break

        # Skip image if no nuclei channel.
        if channel is None:
            continue

        if channel.startswith("Channel"):
            # Special case where channels were not named.
            frame = int(channel[-1]) - 1  # get the frame
        else:
            # Identify the frame that contains nuclei image.
            channel_map = get_tile_metadata(gc, item["_id"]).get("channelmap", {})

            frame = channel_map[channel]

        # Get the image by frame.
        response = gc.get(
            f"item/{item['_id']}/tiles/region?units=base_pixels&exact="
            + f"false&frame={frame}&encoding=PNG",
            jsonResp=False,
        )

        # Save images.
        img = np.array(Image.open(BytesIO(response.content)))

        imwrite(join(args.save_dir, f"{get_filename(item['name'])}.png"), img)


if __name__ == "__main__":
    main()
