import os
from datetime import datetime
from dateutil.parser import isoparse
from typing import Optional, Dict, List, Any, Union

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

class Totality(object):
    def __init__(self):
        pass
    
    def create_node(self) -> Node:
        pass


class ObservationsCollection(object):
    def __init__(self,
                 username: str=None,
                 key_id: str=None,
                 email: str=None,
                 fullname: str=None,
                 contributor_metadata: Dict=None,
                 organization_name: str=None,
                 organization_type: str=None,
                 series_name: str=None,
                 transducer: str=None,
                 platform: str=None,
                 recognition: str=None,
                 observed_at: Optional[Union[str, datetime]]=None):
        
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
            else:
                raise TypeError(f"Attr {name} must be of type str")
        elif name == "observed_at":
            if isinstance(value, datetime):
                self.__dict__[name] = value
            elif isinstance(value, str):
                # throws ValueError if value doesn't parse
                self.__dict__[name] = isoparse(value)
            
    
    def add(self, obs: Observation):
        self.observations.append(obs)
    
    def to_doc(self) -> Dict:
        doc = {}
        self._update_doc(doc, "contributor", ["username", "key_id", "email", "fullname"])
        self._update_doc(doc, "source", ["organization_name", "organization_type", "series_name"])
        self._update_doc(doc, "collectionMethod", ["transducer", "platform", "recognition"])
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
    def __init__(self):
        pass


class Node(Observation):
    def __init__(self, 
                 node_type: str, 
                 node_id: NodeId,
                 lat: float, 
                 lon: float, 
                 shape: Optional[Union[Feature, Dict]]=None,
                 data: Optional[Dict]=None,
                 observed_at: Optional[Union[str, datetime]]=None,
                 services: Optional[List]=None,
                 **kwargs):
        super().__init__()
        self.node_type = node_type
        self.node_id = node_id
        self.location = Point((lon, lat))
        self.shape = shape
        self.data = data
        self.observed_at = observed_at
        self.services = services
        self.collection = ObservationsCollection(**kwargs)
        
    
    def __setattr__(self, name, value):
        if name == "node_type":
            if value in ["facility", "admin", "resource", "reservoir", "process"]:
                self.__dict__[name] = value
            else:
                raise ValueError(f"node_type {value} is not valid")
        elif name == "observed_at":
            if isinstance(value, datetime):
                self.__dict__[name] = value
            elif isinstance(value, str):
                # throws ValueError if value doesn't parse
                self.__dict__[name] = isoparse(value)
        elif name == "data":
            if isinstance(value, dict):
                self.__dict__[name] = value
            else: 
                raise TypeError("Attr data must be of type dict")
        elif name == "location":
            if isinstance(value, Point):
                self.__dict__[name] = value
            else:
                raise TypeError("Attr location must be of type Point")
        elif name == "node_id":
            raise NotImplementedError()
        elif name == "shape":
            raise NotImplementedError()
        elif name == "services":
            raise NotImplementedError()
        
        else:
            raise ValueError(f"field {name} not valid")
    
    def to_item(self):
        self.check_node_type()
        self.check_lat_lon()
        item = {
            "location": {
                "type": "Point",
                "coordinates": [self.lon, self.lat]
            },
            "nodeType": self.node_type
        }
    
    def to_doc(self):
        pass


class Facility(Node):
    def __init__(self, **kwargs):
        super().__init__("facility", **kwargs)
    

class Reading(Observation):
    def __init__(self):
        super().__init__()