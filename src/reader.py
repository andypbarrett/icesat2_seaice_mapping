"""Readers for ICESat-2"""
from typing import Union, List
from pathlib import Path
import h5py
import pandas as pd
import numpy as np

atl03_height_vars = [
    "heights/h_ph",
    "heights/delta_time",
    "heights/lat_ph",
    "heights/lon_ph",
    "heights/quality_ph",
    "heights/signal_conf_ph",
    "heights/dist_ph_along",
    "heights/dist_ph_across",
]
atl03_geolocation_vars = [
    "geolocation/ph_index_beg",
    "geolocation/segment_ph_cnt",
    "geolocation/segment_dist_x",
]
atl03_geophysical_correction_vars = [
    "geophys_corr/tide_ocean",
    "geophys_corr/tide_equilibrium",
    "geophys_corr/dem_h",
]
atl03_surfaces = ["land", "ocean", "sea_ice", "land_ice", "inland_water"]


def read_atl03_vars(f, variables: List, index_var=None, prefix: str=None) -> dict:
    """Reads a sequence of variables from an atl03 granules and returns
    a dictionary.

    Arguments
    ---------
    f : h5py.File object
    variables : list of paths to variables
    prefix : prefix to append to column name

    Returns
    -------
    Dict with variable names as keys
    """
    names = []
    data = []
    for var in variables:
        if prefix:
            name = "_".join([prefix, var.split("/")[-1]])
        else:
            name = var.split("/")[-1]
        values = f[var][:]
        # handle datetimes
        if len(values.shape) != 1:
            values = np.unstack(values, axis=1)
            if "signal_conf_ph" in name:
                names += [f"{name}_{surface}" for surface in atl03_surfaces]
            else:
                names += [f"{name}_{i}" for i in range(len(values))]
            data += values
        else:
            names.append(name)
            data.append(values)

    return {k: v for k, v in zip(names, data)}

    
def atl03(filepath: Union[str, Path],
          beam: str, 
          height_variables=None,
          geolocation_variables: Union[bool, List]=True,
          geophysical_correction_variables: Union[bool, List]=True):
    """Read ATL03 data

    filepath : path to ATL03 file
    beam : beam identifier following gtxy where x is beam pair number (1,2,3) and y is l or r
    height_variables : list of height variables to read.  If None, reads standard list.  See below.
    geolocation_variables : list of geolocation variables.  
    geophysical_correction_variables : list of geophysical corrections to load

    Returns
    -------
    pandas.DataFrame indexed by photon array id - explain better
    """

    # make list of variables to read
    if height_variables == None:
        height_variables = atl03_height_vars
    photon_variables = [f"{beam}/{var}" for var in height_variables]

    segment_variables = []
    if geolocation_variables:
        if isinstance(geolocation_variables, list):
            if len(geolocation_variables) == 0:
                raise TypeError("geolocation_variables is empty list")
        else:
            geolocation_variables = atl03_geolocation_vars
        segment_variables += [f"{beam}/{var}" for var in geolocation_variables]

    if geophysical_correction_variables:
        if isinstance(geophysical_correction_variables, list):
            if len(geophysical_correction_variables) == 0:
                raise TypeError("geophysical_correction_variables is empty list")
        else:
            geophysical_correction_variables = atl03_geophysical_correction_vars
        segment_variables += [f"{beam}/{var}" for var in geophysical_correction_variables]

    # load variables
    f = h5py.File(filepath)

    # load photon variables
    df = pd.DataFrame(read_atl03_vars(f, photon_variables))

    # load segment variables - need to make index photon_index_begin
    # Need to deal with missing segments as indicated by photon_index_begin
    df_seg = pd.DataFrame(read_atl03_vars(f, segment_variables, prefix="seg"))
    
    f.close()

    return pd.concat([df, df_seg], axis=1)