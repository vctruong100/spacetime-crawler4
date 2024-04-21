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
            if self.raw_response and self.raw_response.is_redirect:
                    self.url = self.raw_response.headers["Location"]
        except TypeError:
            self.raw_response = None
