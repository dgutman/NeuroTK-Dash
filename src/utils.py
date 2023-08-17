# Utility functions.
from girder_client import GirderClient
from typing import List


def get_projects(gc: GirderClient, fld_id: str) -> List[dict]:
    """Get a list of NeuroTK folders for the user.
    
    Args:
        gc: Girder client.
        fld_id: DSA id of NeuroTK Projects folder.
    
    Returns:
        List of project metadata.
    
    """
    # Loop through public and then private folders.
    projects = []

    for fld in gc.listFolder(fld_id):
        for user in gc.listFolder(fld['_id']):
            for project in gc.listFolder(user['_id']):
                project['key'] = f"{user['name']}/{project['name']}"
                projects.append(
                    project
                )

    return projects
