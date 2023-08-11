- Created the calcloud-ami-rotation CodeBuild project to take over running
  the biweekly AMI rotation script previously run by the
  calcloud-env-AmiRotation Lambda
- Replaced the deprecated sklearn==0.0 package with scikit-learn==1.0.2
- default base docker image set to CALDP_cosandpin_CAL_rc1
- default crds update to hst_1089.pmap
