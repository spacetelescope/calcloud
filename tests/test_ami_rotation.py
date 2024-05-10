""" test that the ami rotation lambda will launch an ec2 instance """

import os


def test_ami_rotation(ec2_resource, ec2_client):
    # this import has to be inside the testing function or the lambda_handler complains about aws credentials
    import ami_rotation

    filters = [{"Name": "instance-state-name", "Values": ["running"]}]

    # make sure we're starting with no instances
    instances = ec2_resource.instances.filter(Filters=filters)
    assert len(list(instances)) == 0

    # get an image ID
    image_response = ec2_client.describe_images()
    image_id = image_response["Images"][0]["ImageId"]

    # create a launch template
    ec2_client.create_launch_template(
        LaunchTemplateName=os.environ["LAUNCH_TEMPLATE_NAME"], LaunchTemplateData={"ImageId": image_id}
    )

    vpc = ec2_client.create_vpc(CidrBlock="10.0.0.0/16")

    subnet = ec2_client.create_subnet(VpcId=vpc["Vpc"]["VpcId"], CidrBlock="10.0.0.0/16")

    os.environ["SUBNET"] = subnet["Subnet"]["SubnetId"]

    ami_rotation.lambda_handler({}, {})

    # make sure the lambda launched an instance
    instances = ec2_resource.instances.filter(Filters=filters)
    assert len(list(instances)) == 1
