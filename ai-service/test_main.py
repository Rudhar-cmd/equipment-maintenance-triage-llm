from main import AnalyzeRequest, retrieve_evidence, priority

def test_evidence():
    p=AnalyzeRequest(equipment={"type":"Industrial Compressor"},issue={"description":"high temperature and vibration","sensorReadings":[]})
    assert retrieve_evidence(p)

def test_priority():
    p=AnalyzeRequest(equipment={},issue={},thresholdChecks=[{"triggered":True}])
    assert priority(p)=="HIGH"
