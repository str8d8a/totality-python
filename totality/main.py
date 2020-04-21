from __future__ import annotations
import os
from datetime import datetime
from dateutil.parser import isoparse
from typing import Optional, Dict, List, Any, Union, Callable
from contextlib import contextmanager
from dotted_dict import DottedDict

import requests
import basket_case as bc
from geojson import Feature, Point

ALLOWED_VALUES = {
    "organization_type": [
        "non-profit", "company", "government agency", "individual", "other"
    ],
    "transducer": [
        "camera - visible", "camera - IR", "lidar", "SAR", "microphone",
        "camera - other", "EM - other", "other", "eye", "ear", "skin",
        "nose", "transponder"
    ],
    "recognition": [
        "deterministic", "perception - human", "perception - machine", "formal process"
    ]
}

DEFAULT_BATCH_SIZE = 20

class Totality(object):
    def __init__(self, api_key=None):
        self.api_key = api_key
    
    def create_nodes_collection(self, *args, **kwargs) -> ObservationsCollection:
        return ObservationsCollection("nodes", self, *args, **kwargs)
    
    def create_readings_collection(self, *args, **kwargs) -> ObservationsCollection:
        return ObservationsCollection("readings", self, *args, **kwargs)


class ObservationsCollection(object):
    def __init__(self,
                 collection_type: str,
                 client: Totality,
                 username: Optional[str]=None,
                 key_id: Optional[str]=None,
                 email: Optional[str]=None,
                 fullname: Optional[str]=None,
                 contributor_metadata: Optional[Dict[str, Any]]=None,
                 organization_name: Optional[str]=None,
                 organization_type: Optional[str]=None,
                 series_name: Optional[str]=None,
                 transducer: Optional[str]=None,
                 platform: Optional[str]=None,
                 recognition: Optional[str]=None,
                 observed_at: Optional[Union[str, datetime]]=None):
        
        self.client = client
        self.collection_type = collection_type
        self.observed_at = observed_at
        
        # contributor
        self.username = username
        self.key_id = key_id
        self.email = email
        self.fullname = fullname
        self.contributor_metadata = contributor_metadata
        
        # source
        self.organization_name = organization_name
        self.organization_type = organization_type
        self.series_name = series_name
        
        # collectionMethod
        self.transducer = transducer
        self.platform = platform
        self.recognition = recognition
        
        self.observations: List[Observation] = []
    
    def __setattr__(self, name, value):
        if name in [
            "username", "key_id", "email", "fullname", 
            "organization_name", "organization_type", "series_name", 
            "transducer", "platform", "recognition"]:
            if isinstance(value, str):
                if name in ALLOWED_VALUES:
                    if value not in ALLOWED_VALUES[name]:
                        raise ValueError(f"{name} {value} is not valid")
                self.__dict__[name] = value
            elif value is None:
                pass
            else:
                raise TypeError(f"Attr {name} must be of type str")
        elif name == "collection_type":
            if value in ["nodes", "readings"]:
                self.__dict__["collection_type"] = value
            else:
                raise ValueError(f"collection_type {value} is not valid")
        elif name == "observed_at":
            if isinstance(value, datetime):
                self.__dict__[name] = value
            elif isinstance(value, str):
                # throws ValueError if value doesn't parse
                try:
                    self.__dict__[name] = isoparse(value)
                except ValueError as e:
                    self.__dict__[name] = value
                
        else:
            self.__dict__[name] = value
    
     
    def add(self, obs: Observation):
        self.observations.append(obs)
        if self.is_context:
            self._maybe_push()
    
    def flush(self):
        if len(self.observations) == 0:
            return
        doc = self.to_doc()
        doc[self.collection_type] = [obs.to_item() for obs in self.observations]
        obs_resp = requests.post(
            f'https://totality.str8d8a.info/dev/observations/{self.collection_type}',
            headers={
                'x-api-key': self.client.api_key,
                'Content-Type': 'application/json'
            },
            json=doc)
        if obs_resp.status_code != 200:
            print(f'POST observation responded with status code {obs_resp.status_code}')
            print(obs_resp.text)
        self.observations = []

    
    def _maybe_push(self):
        if len(self.observations) >= DEFAULT_BATCH_SIZE:
            self.flush()
                
    def __enter__(self):
        self.__dict__['is_context'] = True
    
    def __exit__(self, type, value, traceback):
        self.flush()
    
    def to_doc(self) -> Dict[str, Any]:
        doc: Dict[str, Any] = {}
        self._update_doc(doc, "contributor", ["username", "key_id", "email", "fullname"])
        self._update_doc(doc, "source", ["organization_name", "organization_type", "series_name"])
        self._update_doc(doc, "collectionMethod", ["transducer", "platform", "recognition"])
        if hasattr(self, 'observed_at'):
            doc['observedAt'] = str(self.observed_at)
        return doc
    
    def _update_doc(self, doc, key, fields):
        found = {}
        for field in fields:
            val = self.__dict__.get(field, None)
            if val:
                found[field] = val
        if len(found.keys()) > 0:
            doc[key] = found

class Observation(object):
    def __init__(self,
                 lat: float,
                 lon: float,
                 observed_at: Optional[Union[str, datetime]]=None,
                 collection: Optional[ObservationsCollection]=None,
                 **kwargs):
        self.location = Point((lon, lat))
        self.observed_at = observed_at
        if collection:
            self.collection = collection
        else:
            self.collection = ObservationsCollection(**kwargs)
    
    def __setattr__(self, name, value):
        if name == "location":
            if isinstance(value, Point):
                self.__dict__[name] = value
            else:
                raise TypeError("Attr location must be of type Point")
        elif name == "observed_at":
            if isinstance(value, datetime):
                self.__dict__[name] = value
            elif isinstance(value, str):
                # throws ValueError if value doesn't parse
                self.__dict__[name] = isoparse(value)
        elif name == "collection":
            self.__dict__[name] = value
        else:
            raise ValueError(f"field {name} not valid")
        
    
    def to_item(self) -> Dict[str, Any]:
        raise NotImplementedError()
    
    def to_doc(self) -> Dict[str, Any]:
        outer = self.collection.to_doc()
        return outer
    

class Node(Observation):
    def __init__(self, 
                 node_id: NodeId,
                 lat: float, 
                 lon: float, 
                 observed_at: Optional[Union[str, datetime]]=None,
                 shape: Optional[Union[Feature, Dict]]=None,
                 data: Optional[Dict]=None,
                 services: Optional[List]=None,
                 **kwargs):
        super().__init__(lat=lat, lon=lon, observed_at=observed_at, **kwargs)
        self.node_type = node_id.node_type
        self.node_id = node_id
        self.shape = shape
        self.data = data
        self.services = services
        
    def __setattr__(self, name, value):
        if value is None:
            return
        if name == "node_type":
            if value in ["facility", "admin", "resource", "reservoir", "process"]:
                self.__dict__[name] = value
            else:
                raise ValueError(f"node_type {value} is not valid")
        elif name == "data":
            if isinstance(value, dict):
                self.__dict__[name] = value
            else: 
                raise TypeError("Attr data must be of type dict")
        elif name == "node_id":
            if isinstance(value, NodeId):
                self.__dict__[name] = value
            else:
                raise TypeError("Attr node_id must be of type NodeId")
        elif name == "shape":
            if isinstance(value, Feature) or isinstance(value, dict):
                self.__dict__[name] = value
            else:
                raise TypeError("Attr shape must be a valid Feature")
        elif name == "services":
            raise NotImplementedError()
        else:
            super().__setattr__(name, value)
    
    def to_item(self) -> Dict[str, Any]:
        # self.check_node_type()
        # self.check_lat_lon()
        item = {
            "location": self.location,
            "nodeType": self.node_type,
            "nodeId": self.node_id.to_dict()
        }
        if hasattr(self, 'observed_at') and self.observed_at:
            item['observedAt'] = self.observed_at
        if self.shape:
            item['shape'] = self.shape
        if self.data:
            item['data'] = self.data
        return item
    
    def to_doc(self):
        doc = super().to_doc()
        doc['nodes'] = [self.to_item()]
        return doc
    

class Reading(Observation):
    def __init__(self,
                 lat: float, 
                 lon: float,
                 unit: str,
                 value: Union[int, float, str],
                 observed_at: Optional[Union[str, datetime]]=None):
        super().__init__(lat=lat, lon=lon, observed_at=observed_at)
        self.unit = unit
        self.value = value
    
    def to_item(self) -> Dict[str, Any]:
        pass
    
    def to_doc(self):
        doc = super().to_doc()
        doc['nodes'] = [self.to_item()]


class NodeId(DottedDict):
    codes_to_names = {
        "000": "node_type",
        "010": "kind",
        "020": "catalog",
        "022": "catalog_title",
        "027": "admin_level",
        "028": "admin_name",
        "030": "catalog_id",
        "035": "common_name"
    }
    codes = set(codes_to_names.keys())
    names = set(codes_to_names.values())
    names_to_codes = {v: k for k, v in codes_to_names.items()}
    
    @classmethod
    def full_key(cls, k: str) -> str:
        return f"{k} {bc.title(cls.codes_to_names[k])}"
    
    def __init__(self, **kwargs):
        super().__init__()
        self.__dict__['id_dict'] = {}
        for k, v in kwargs.items():
            self.__setattr__(k, v)
    
    def __setattr__(self, name, value):
        if name in self.codes:
            self.id_dict[name] = value
        elif name in self.names:
            self.__dict__['id_dict'][self.names_to_codes[name]] = value
        else:
            raise ValueError(f"ID field {name} not recognized")
    
    def __getattr__(self, name):
        d = self.__dict__['id_dict']
        if name in d:
            return d[name]
        elif name in self.names:
            code = self.names_to_codes[name]
            if code in d:
                return d[code]
            else:
                full = self.full_key(code)
                raise Exception(f"NodeId component {full} is not set")
        else:
            return super().__getattr__(name)
            
    
    def to_dict(self):
        return {
            self.full_key(k): v for k, v in self.id_dict.items()
        }
    
        