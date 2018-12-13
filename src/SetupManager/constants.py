import os

RTS_ARTIFACT_SUFFIXES = {
    "ekstazi" : ["clz"],
    "starts" : ["zlc", "graph"]
}

RTS_RUN_COMMAND = {
    "ekstazi" : "mvn test",
    "starts" : "mvn starts:starts"
}

EKSTAZI_XML_PATH = "{}/ekstazi.xml".format(os.path.dirname(os.path.realpath(__file__)))
STARTS_XML_PATH = "{}/starts.xml".format(os.path.dirname(os.path.realpath(__file__)))
SUREFIRE_XML_PATH = "{}/surefire.xml".format(os.path.dirname(os.path.realpath(__file__)))

WEBHOOK_ENTRY = "https://cireinteract.azurewebsites.net/api/CINotificationEndPoint?code=AEW9Jm5ijk8SNN2PA0hIPwAxIcb3lqjqWL97EadKyB6qWSkNqNC0bQ=="
REPORT_STORAGE_ENTRY = "https://cireinteract.azurewebsites.net/api/StoreReportEndPoint?code=tl93p4oBpLOxwwYgaFanI/JhDdlynBag5LXYETBfNAM6QSjUaIfXgw=="
