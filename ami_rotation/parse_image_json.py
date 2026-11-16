import sys
import json
from collections import OrderedDict
from datetime import datetime

# This command parses the response to `aws ec2 describe-images`.
# This response can be so long that it cannot be passed on the command-line.
# When you call this program, you can either:
# 1. pass the response on the command line, followed by the image-name-prefix
# 2. store the response in a file called images.json, and only pass the image-name-prefix
if len(sys.argv) == 3:
    # Response has been passed on command-line
    input_string = str(sys.argv[1])

    image_name_filter = sys.argv[2]
else:
    # Response is in images.json file
    with open("images.json", "r") as f:
        input_string = f.read()
    image_name_filter = sys.argv[1]

response = json.loads(input_string)
images = response["Images"]

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
