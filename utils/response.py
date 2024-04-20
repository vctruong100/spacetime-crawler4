import pickle

class Response(object):
    def __init__(self, resp_dict):
        self.url = resp_dict["url"]
        self.status = resp_dict["status"]
        self.error = resp_dict["error"] if "error" in resp_dict else None
        try:
            self.raw_response = (
                pickle.loads(resp_dict["response"])
                if "response" in resp_dict else
                None)

            # Check if response is a redirect
            self.is_redirect = self.status in {301, 302, 303, 307, 308}
        except TypeError:
            self.raw_response = None
