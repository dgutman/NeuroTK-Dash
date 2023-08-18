from gc_utils import login, load_yaml

item_annotation_endpoint = "annotation/item/*"

cf = load_yaml(fp="conf.yaml")  # configuration variables
gc = login(cf.dsa_api_url, username=cf.username, password=cf.password)

def get_item_rois(item_id, annot_name=None):
    annots = gc.get(item_annotation_endpoint.replace("*", item_id))

    item_records = [
        element
        for annot in annots
        for element in annot["annotation"]["elements"]
        if (annot_name is None) or (annot["annotation"]["name"] == annot_name)
    ]

    return item_records