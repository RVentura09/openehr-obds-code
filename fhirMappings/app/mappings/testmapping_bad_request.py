# Test Mapping to trigger Bad Reqeuest

class PseudoResource:
    def __init__(self, id, resource_type):
        self.id = id
        self.resource_type = resource_type

    def json(self):
        return '{"resourceType": "Patient", "Notallowed": "here"}'

def map_ressource(_) -> str:

    return [PseudoResource('someID123', 'Patient')]
