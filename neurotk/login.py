from girder_client import GirderClient


def login(
    apiurl: str, username: str = None, password: str = None
) -> GirderClient:
    """Authenticate girder client instance.
    
    Args:
        apiurl: API URL.
        username: Username.
        password: Password.
    
    Returns:
        gc: Girder client.
        
    """
    gc = GirderClient(apiUrl=apiurl)

    if username is None or password is None:
        interactive = True
    else:
        interactive = False

    gc.authenticate(username=username, password=password, 
                    interactive=interactive)

    return gc
