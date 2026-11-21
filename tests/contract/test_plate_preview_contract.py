def test_preview_openapi_and_auth(client):
    paths=client.get("/openapi.json").json()["paths"]
    route="/api/v1/enrichment-jobs/{enrichmentJobId}/detections/{detectionId}/plate-preview"
    assert route in paths
    operation=paths[route]["get"]
    assert operation["security"]==[{"ApiKeyAuth":[]}]
    assert "X-Plate-Preview-Metadata" in operation["responses"]["200"]["headers"]
    denied=client.get("/api/v1/enrichment-jobs/unknown/detections/1/plate-preview")
    assert denied.status_code==401 and denied.headers["cache-control"]=="no-store"

def test_all_generated_openapi_references_are_resolvable(client):
 document=client.get("/openapi.json").json()
 def visit(value):
  if isinstance(value,dict):
   if "$ref" in value and value["$ref"].startswith("#/"):
    target=document
    for part in value["$ref"][2:].split("/"):target=target[part.replace("~1","/").replace("~0","~")]
   for child in value.values():visit(child)
  elif isinstance(value,list):
   for child in value:visit(child)
 visit(document)
 assert "PlatePreviewMetadata" in document["components"]["schemas"]
