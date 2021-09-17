import sys
import json
from collections import OrderedDict
from datetime import datetime

response = json.loads(str(sys.argv[1]))
images = response["Images"]
image_name_filter = sys.argv[2]

stsciLinux2Ami = {}
for image in images:
    creationDate = image["CreationDate"]
    imageId = image["ImageId"]
    name = image["Name"]
    # Only look at particular AMIs
    if name.startswith(image_name_filter):
        stsciLinux2Ami.update({creationDate: imageId})
# Order the list most recent date first
orderedAmi = OrderedDict(
    sorted(stsciLinux2Ami.items(), key=lambda x: datetime.strptime(x[0], "%Y-%m-%dT%H:%M:%S.%f%z"), reverse=True)
)
# Print first element in the ordered dict
print(list(orderedAmi.values())[0])
