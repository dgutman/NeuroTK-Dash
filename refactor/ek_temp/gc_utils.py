# Girder client utility functions
# - login
# - get_items
# - delete_non_image_items
# - del_empty_flds

import yaml


# from tqdm import tqdm
from collections import namedtuple
from girder_client import GirderClient, HttpError


def load_yaml(fp: str = "./megabrain_stats_gen/conf.yaml") -> object:
    """Load a yaml file.

    Args:
        fp: Filepath of yaml file.

    Returns:
        Contents of the yaml file as a list or dict.

    """
    with open(fp, "r") as fh:
        cf = yaml.safe_load(fh)

        for k in list(cf.keys()):
            new_k = k.replace("-", "_")

            if new_k != k:
                cf[new_k] = cf[k]
                del cf[k]

    return namedtuple("ObjectName", cf.keys())(*cf.values())


def login(api_url: str, username: str = None, password: str = None) -> GirderClient:
    """Get girder client.

    Args:
        api_url: The DSA instance api url.
        username: Username to authenticate client with, if None then interactive authentication is used.
        password: Password to authenticate client with, if None then interactive authentication is used.

    Returns:
        Authenticated girder client instance.

    """
    gc = GirderClient(apiUrl=api_url)

    if username is None or password is None:
        interactive = True
    else:
        interactive = False

    gc.authenticate(username=username, password=password, interactive=interactive)

    return gc


def get_items(gc: GirderClient, parent_id: str) -> list:
    """Recursively gets items in a collection or folder parent location.

    Args:
        gc: Authenticated girder client instance.
        parent_id: The id of the collection / folder to get all items under.

    Returns:
        List of items in parent folder / collection.

    """
    try:
        items = gc.get(f"resource/{parent_id}/items?type=collection&limit=0&sort=_id&sortdir=1")
    except HttpError:
        items = gc.get(f"resource/{parent_id}/items?type=folder&limit=0&sort=_id&sortdir=1")

    return items


def delete_non_image_items(gc: GirderClient, items: str, exts: tuple = (".svs", ".ndpi", ".czi")) -> (list, str):
    """Delete DSA items that whose names don't end with a given set of extensions.

    Args:
        gc: Authenticated girder client instance.
        items: List of DSA items.
        exts: Acceptable extensions, checks on the item name.

    Returns:
        A list of the items that were not deleted.
        A report with each item deleted (name and id).

    """
    if not len(exts):
        raise Exception("You did not pass any extensions, exception to avoid deleting all items!")

    report = "Items deleted:\n"

    n = 0

    remaining_items = []

    for item in tqdm(items):
        if not item["name"].endswith(exts):
            n += 1
            report += f"{n}. {item['name']} (id: {item['_id']})\n"
            _ = gc.delete(f"item/{item['_id']}")
        else:
            remaining_items.append(item)

    if n:
        return remaining_items, report.strip()
    else:
        return remaining_items, "No items where deleted."


def del_empty_flds(gc, src_id, parent_type="collection"):
    """Traverse a DSA collection or folder and delete all folders that have nothing inside them. This function
    uses recursive logic to delete from the lowest folder first and move up after.

    Args:
        gc: Authenticated girder client instance.
        src_id: Collection or folder ID.
        parent_type: Specify if the source id is for a collection or folder.

    """
    # list items and folders in parent location
    folders = list(gc.listFolder(src_id, parentFolderType=parent_type))

    if parent_type == "folder":
        items = list(gc.listItem(src_id))
    else:
        items = []  # items are not allowed at the collection level

    if len(folders) > 0:
        # if there are folders then check each one by invoking this function (iterative) on it
        if parent_type == "collection":
            for fld in tqdm(folders):
                del_empty_flds(gc, fld["_id"], parent_type="folder")
        else:
            for fld in folders:
                del_empty_flds(gc, fld["_id"], parent_type="folder")

        # get folders again, some might have been deleted
        folders = list(gc.listFolder(src_id, parentFolderType=parent_type))

    # if both folders and items are empty delete this folder
    if parent_type != "collection" and not len(items) + len(folders):
        fld = gc.getFolder(src_id)
        print(f'  Deleting folder {fld["name"]}')
        _ = gc.delete(f"folder/{src_id}")
