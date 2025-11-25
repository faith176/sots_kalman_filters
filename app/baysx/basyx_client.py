import requests
import base64
import json

class BasyxClient:

    def __init__(self, env: str):
        """
        env: URL of AAS environment (e.g. http://localhost:8081)
        """
        self.env = env.rstrip("/")
        print(f"[BaSyxClient] Connected to {self.env}")

    @staticmethod
    def encode_id(identifier: str) -> str:
        encoded = base64.urlsafe_b64encode(identifier.encode("utf-8"))
        return encoded.decode("utf-8").rstrip("=")

    # ----------------------------------------------------------------------
    # Create Submodel (plain ID in JSON is fine)
    # ----------------------------------------------------------------------
    def create_submodel(self, sm_json: dict):
        url = f"{self.env}/submodels"
        print(f"[POST] {url}")
        resp = requests.post(url, json=sm_json)
        print(f"[create_submodel] {resp.status_code} -> {resp.text}")
        return resp

    # ----------------------------------------------------------------------
    # Create AAS (plain ID in JSON is fine)
    # ----------------------------------------------------------------------
    def create_aas(self, aas_json: dict):
        url = f"{self.env}/shells"
        print(f"[POST] {url}")
        resp = requests.post(url, json=aas_json)
        print(f"[create_aas] {resp.status_code} -> {resp.text}")
        return resp

    # ----------------------------------------------------------------------
    # Delete AAS (encoded ID required in URL)
    # ----------------------------------------------------------------------
    def delete_aas(self, aas_id: str):
        encoded = self.encode_id(aas_id)
        url = f"{self.env}/shells/{encoded}"
        print(f"[DELETE] {url}")
        resp = requests.delete(url)
        print(f"[delete_aas] {resp.status_code} -> {resp.text}")
        return resp

    # ----------------------------------------------------------------------
    # Delete Submodel (encoded ID required in URL)
    # ----------------------------------------------------------------------
    def delete_submodel(self, sm_id: str):
        encoded = self.encode_id(sm_id)
        url = f"{self.env}/submodels/{encoded}"
        print(f"[DELETE] {url}")
        resp = requests.delete(url)
        print(f"[delete_submodel] {resp.status_code} -> {resp.text}")
        return resp
    

    def link_submodel(self, aas_id: str, sm_id: str):
        encoded_aas = self.encode_id(aas_id)
        aas_url = f"{self.env}/shells/{encoded_aas}"

        print(f"[GET] {aas_url}")
        get_resp = requests.get(aas_url)
        print(f"[link_submodel:get] {get_resp.status_code} -> {get_resp.text}")

        if get_resp.status_code != 200:
            print("[link_submodel] Failed to GET AAS")
            return get_resp

        aas = get_resp.json()

        # Attach submodel reference link manually
        ref = {
            "type": "ModelReference",
            "keys": [
                {
                    "type": "Submodel",
                    "value": sm_id
                }
            ]
        }

        if "submodels" not in aas or aas["submodels"] is None:
            aas["submodels"] = []
            
        if ref not in aas["submodels"]:
            aas["submodels"].append(ref)

        print(f"[PUT] {aas_url}")
        put_resp = requests.put(aas_url, json=aas)
        print(f"[link_submodel:put] {put_resp.status_code} -> {put_resp.text}")
        return put_resp


    def update_property(self, sm_id: str, element_id: str, new_value):
        endcoded_sm_id = self.encode_id(sm_id)

        # GET the full element object
        get_url = f"{self.env}/submodels/{endcoded_sm_id}/submodel-elements/{element_id}"
        print(f"[GET] {get_url}")
        get_resp = requests.get(get_url)

        if get_resp.status_code != 200:
            print(f"[update_property] GET failed: {get_resp.status_code} -> {get_resp.text}")
            return get_resp

        elem = get_resp.json()

        # Update the value field
        elem["value"] = str(new_value)

        # Send it back
        put_url = get_url
        print(f"[PUT] {put_url}")
        put_resp = requests.put(put_url, json=elem)


        dashboard_url = f"http://localhost:8085/api/elements/{endcoded_sm_id}/{element_id}/value"
        payload = {"value": new_value}
        requests.post(dashboard_url, json=payload)

        print(f"[update_property] {put_resp.status_code} -> {put_resp.text}")
        return put_resp

