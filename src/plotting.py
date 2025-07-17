from shapely.geometry import Polygon

def _get_bbox(r):
    """Returns a shapely Polygon containing spatial extent of granule
    
    r : earthaccess.results object

    Returns
    -------
    list of shapely.Polygon objects
    """
    try:
        gpolygon = r["umm"]["SpatialExtent"]['HorizontalSpatialDomain']['Geometry']['GPolygons']
    except KeyError as err:
        print(err)
        raise(KeyError())

    bbox = []
    for poly in gpolygon:
        bbox.append(Polygon([tuple(ll.values()) for ll in poly["Boundary"]["Points"]]))
    return bbox