Content-Type: multipart/mixed; boundary="==BOUNDARY==" 
MIME-Version: 1.0 

--==BOUNDARY==
MIME-Version: 1.0 
Content-Type: text/x-shellscript; charset="us-ascii"

#!/bin/bash

echo ECS_ENGINE_TASK_CLEANUP_WAIT_DURATION=10m>>/etc/ecs/ecs.config 

--==BOUNDARY==--