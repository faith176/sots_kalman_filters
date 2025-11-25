import random
import time

import requests
from basyx_client import BasyxClient

client = BasyxClient("http://localhost:8081")

AAS_ID = "urn:example:aas:sample"
submodule_ids = {
    "SM_ID" : "urn:example:submodel:data"
}


# Sample AAS JSON
aas_json = {
    "id": AAS_ID,
    "idShort": "SampleAAS",
    "assetInformation": {
        "assetKind": "Instance",
        "globalAssetId": "urn:example:asset:sample"
    },
    "submodels": []
}

# Sample Submodel JSON
sm_json = {
    "id": submodule_ids["SM_ID"],
    "idShort": "DataSM",
    "kind": "Instance",
    "modelType": "Submodel",
    "submodelElements": [
        {
            "idShort": "observedValue",
            "modelType": "Property",
            "valueType": "xs:double",
            "value": "0.0"
        },
        {
            "idShort": "timestamp",
            "modelType": "Property",
            "valueType": "xs:string",
            "value": "1970-01-01T00:00:00Z"
        },
    ]
}
                                                                    

# Delete AAS - clear env
client.delete_aas("urn:example:aas:sample")
client.delete_submodel("urn:example:submodel:data")
                                            
# Create AAS
client.create_submodel(sm_json)
client.create_aas(aas_json)
client.link_submodel(AAS_ID, submodule_ids["SM_ID"])

# --- Update Loop ---
while True:
    value = round(random.uniform(0, 50), 1)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    client.update_property(
        sm_id="urn:example:submodel:data",
        element_id="observedValue",
        new_value=value, 
    )
    client.update_property(
        sm_id="urn:example:submodel:data",
        element_id="timestamp",
        new_value=timestamp, 
    )
    print(f"Updating observedValue → {value, timestamp}")
    time.sleep(2)