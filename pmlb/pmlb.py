# -*- coding: utf-8 -*-

"""
PMLB was primarily developed at the University of Pennsylvania by:
    - Randal S. Olson (rso@randalolson.com)
    - William La Cava (lacava@upenn.edu)
    - Weixuan Fu (weixuanf@upenn.edu)
    - and many more generous open source contributors

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
and associated documentation files (the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial
portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import pandas as pd
import os
from .dataset_lists import classification_dataset_names, regression_dataset_names
import requests
import warnings
import subprocess
import pathlib

dataset_names = classification_dataset_names + regression_dataset_names
GITHUB_URL = 'https://github.com/EpistasisLab/penn-ml-benchmarks/raw/master/datasets'
suffix = '.tsv.gz'

def fetch_data(dataset_name, return_X_y=False, local_cache_dir=None, dropna=True):
    """Download a data set from the PMLB, (optionally) store it locally, and return the data set.

    You must be connected to the internet if you are fetching a data set that is not cached locally.

    Parameters
    ----------
    dataset_name: str
        The name of the data set to load from PMLB.
    return_X_y: bool (default: False)
        Whether to return the data in scikit-learn format, with the features and labels stored in separate NumPy arrays.
    local_cache_dir: str (default: None)
        The directory on your local machine to store the data files.
        If None, then the local data cache will not be used.
    dropna: bool
        If True, pmlb will drop NAs in exported dataset.

    Returns
    ----------
    dataset: pd.DataFrame or (array-like, array-like)
        if return_X_y == False: A pandas DataFrame containing the fetched data set.
        if return_X_y == True: A tuple of NumPy arrays containing (features, labels)

    """

    if local_cache_dir is None:
        if dataset_name not in dataset_names:
            raise ValueError('Dataset not found in PMLB.')
        dataset_url = get_dataset_url(GITHUB_URL,
                                        dataset_name, suffix)
        dataset = pd.read_csv(dataset_url, sep='\t', compression='gzip')
    else:
        dataset_path = os.path.join(local_cache_dir, dataset_name,
                                    dataset_name+suffix)

        # Use the local cache if the file already exists there
        if os.path.exists(dataset_path):
            dataset = pd.read_csv(dataset_path, sep='\t', compression='gzip')
        # Download the data to the local cache if it is not already there
        else:
            if dataset_name not in dataset_names:
                raise ValueError('Dataset not found in PMLB.')
            dataset_url = get_dataset_url(GITHUB_URL,
                                            dataset_name, suffix)
            dataset = pd.read_csv(dataset_url, sep='\t', compression='gzip')
            dataset_dir = os.path.split(dataset_path)[0]
            if not os.path.isdir(dataset_dir):
                os.makedirs(dataset_dir)
            dataset.to_csv(dataset_path, sep='\t', compression='gzip',
                    index=False)

    if dropna:
        dataset.dropna(inplace=True)
    if return_X_y:
        X = dataset.drop('target', axis=1).values
        y = dataset['target'].values
        return (X, y)
    else:
        return dataset


def get_dataset_url(GITHUB_URL, dataset_name, suffix):
    dataset_url = '{GITHUB_URL}/{DATASET_NAME}/{DATASET_NAME}{SUFFIX}'.format(
                                GITHUB_URL=GITHUB_URL,
                                DATASET_NAME=dataset_name,
                                SUFFIX=suffix
                                )

    re = requests.get(dataset_url)
    if re.status_code != 200:
        raise ValueError('Dataset not found in PMLB.')
    return dataset_url


def get_updated_datasets():
    """Looks at commit and returns a list of datasets that were updated."""
    cmd = 'git diff --name-only HEAD HEAD~1'
    res = subprocess.check_output(cmd.split(), universal_newlines=True).rstrip()
    changed_datasets = set()
    changed_metadatas = set()
    for path in res.splitlines():
        path = pathlib.Path(path)
        if path.parts[0] != 'datasets':
            continue
        if path.name.endswith('.tsv.gz'):
            changed_datasets.add(path.parts[-2])
        if path.name == 'metadata.yaml':
            changed_metadatas.add(path.parts[-2])
    # changed_metadatas &= set(dataset_names)
    changed_datasets = sorted(changed_datasets)
    changed_metadatas = sorted(changed_metadatas)
    print(
        f'changed datasets: {changed_datasets}\n'
        f'changed metadata: {changed_metadatas}'
    )
    return {'changed_datasets': changed_datasets,
            'changed_metadatas': changed_metadatas}


def filter_datasets(obs_min = None, obs_max = None, feat_min = None, feat_max = None, class_min = None, class_max = None, endpt = None, max_imbalance = None, task = None):
     """Filters existing datasets by given parameters, and returns a list of their names.
     
     Parameters
     ----------
     obs_min: int (default: None)
         The minimum acceptable number of observations/instances in the dataset
     obs_Max: int (default: None)
         The maximum acceptable number of observations/instances in the dataset
     feat_min: int (default: None)
         The minimum acceptable number of features in the dataset
     feat_max: int (default: None)
         The maximum acceptable number of features in the dataset
     class_min: int (default: None)
         The minimum acceptable number of classes in the dataset
     class_max: int (default: None)
         The maximum acceptable number of classes in the dataset
     max_imbalance: float (default: None)
         Maximum acceptable imbalance value for the dataset
     endpt: str (default: None)
         Whether the dataset endpoint type should be discrete, continuous, categorical, or binary
     task: str (default: None)
         Whether the dataset is suited for classification or regression problems

     Returns
     ----------
     list (str): 
         list of names of datasets within filters. Will return an empty list if no datasets match.
         
     
     """

     tempdf = pd.read_csv('https://raw.githubusercontent.com/EpistasisLab/penn-ml-benchmarks/master/datasets/all_summary_stats.csv')
     if obs_min is not None:
         tempdf = tempdf.loc[tempdf['#instances'] >= obs_min]
     if obs_max is not None:
         tempdf = tempdf.loc[tempdf['#instances'] <= obs_max]
     if feat_Min is not None:
         tempdf = tempdf.loc[tempdf['#features'] >= feat_min]
     if feat_Max is not None:
         tempdf = tempdf.loc[tempdf['#features'] <= feat_max]
     if class_min is not None:
         tempdf = tempdf.loc[tempdf['#Classes'] >= class_min]
     if class_max is not None:
         tempdf = tempdf.loc[tempdf['#Classes'] <= class_max]
     if max_imbalance is not None:
         tempdf = tempdf.loc[tempdf['Imbalance_metric'] < max_imbalance]
     if endpt is not None:
         tempdf = tempdf.loc[tempdf['Endpoint_type'] == endpt]
     if task is not None:
         tempdf = tempdf.loc[tempdf['problem_type'] == task]
     return list(tempdf['dataset'].values)

