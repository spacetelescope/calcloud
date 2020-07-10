"""This module implements pub/sub messaging thinly layered over AWS SNS + SQS.

XXXXXXX This module contains unfinished draft work:
   Topic, queue, and subscription creation work except for queue permissions 
       which must be set to Everybody on the console.
   Topic, queue, and subscription deletion work.
   Basic send and receive seem to work.  deduplication is not implmented.
   The messenger class is completely unfinished.

"""
import sys
import os
import json
import tempfile
import argparse

import yaml    # pyyaml package
import json
import boto3

from calcloud import log

# -------------------------------------------------------------

class MessageBus:
    def __init__(self, account, region, prefix_name, topic_name, queue_subscriptions, tags={}):
        self.account = account
        self.region = region
        self.prefix_name = prefix_name
        self.topic_name = prefix_name + "-" + topic_name
        self.queue_subscriptions = { 
            prefix_name + "-" + queue : queue_subscriptions[queue] for
            queue in queue_subscriptions
            }
        self.tags = tags
        self._topic_arn =  f"arn:aws:sns:{region}:{account}:{self.topic_name}"
        self._queue_info = {}
        self._arn_prefix = f"arn:aws:sqs:{region}:{account}:"
        self._url_prefix = f"https://sqs.{region}.amazonaws.com/{account}/"
        self._sns_client = boto3.client("sns", region_name=region)
        self._sqs_client = boto3.client("sqs", region_name=region)
        self._iam_client = boto3.client("iam", region_name=region)

    # ......................................................................................

    def init_bus(self):
        self._create_topic()
        self._create_queues()
        self._subscribe_queues()

    def _create_topic(self):
        self.topic = self._sns_client.create_topic(
            Name=self.topic_name,
            Tags=[{"Key": name, "Value": value} for name, value in self.tags.items()],
        )
        # self._sns_client.add_permission(
        #     TopicArn=self._topic_arn,
        #     Label=self.topic_name,
        #     AWSAccountId=[ "*" ],
        #     ActionName=[
        #         'Subscribe',
        #         'Unsubscribe',
        #         'Publish',
        #         'ListSubscriptions',
        #         'ListSubscriptionsByTopic',
        #         # 'AddPermission',
        #         # 'RemovePermission',
        #         # 'GetTopicAttributes',
        #         # 'SetTopicAttributes',
        #         # 'DeleteTopic',
        #     ],
        # )

    def _create_queues(self):
        existing_queues = self.list_queues()
        for queue_name, _message_types in self.queue_subscriptions.items():
            queue_url = self._url_prefix + queue_name
            if queue_url in existing_queues:
                continue
            self._queue_info[queue_name] = self._sqs_client.create_queue(
                QueueName=queue_name, tags=self.tags)
            self._sqs_client.add_permission(
                QueueUrl=queue_url,
                Label=queue_name + "-send-permission",
                AWSAccountIds=[self.account],
                Actions=[
                    "ReceiveMessage",
                    "SendMessage",
                    "DeleteMessage",
                    # "PurgeQueue",
                    # "ListQueues",
                    # "ListQueueTags",
                ],
            )
            # policy = {
            #     "Version": "2012-10-17",
            #     "Id": queue_name + "-send-policy",
            #     "Statement": 
            #      {
            #         "Sid": queue_name + "-send-policy",
            #         "Effect": "Allow",
            #         "Principal": {
            #              "AWS": [
            #                 "*",
            #                 # "arn:aws:iam::111122223333:role/role1",
            #                 # "arn:aws:iam::111122223333:user/username1"
            #              ]
            #         },
            #         "Action": [
            #             "sqs:SendMessage",
            #             "sqs:DeleteMessage"
            #         ],
            #         f"Resource": "arn:aws:sqs:{self.region}:{self.account}:{queue_name}",
            #     },
            # }

    def _subscribe_queues(self):
        for queue_name in self.queue_subscriptions:
            self._subscribe_queue(queue_name)

    def _subscribe_queue(self, queue_name):
        for existing in self.list_subscriptions():
            if queue_name in existing:
                return self._queue_info[queue_name]
        response = self._sns_client.subscribe(
            TopicArn=self._topic_arn,
            Protocol="sqs",
            Endpoint=self._arn_prefix + queue_name,
            ReturnSubscriptionArn=True,
        )
        arn = response["SubscriptionArn"]
        self._sns_client.set_subscription_attributes(
            SubscriptionArn=arn, 
            AttributeName='FilterPolicy', 
            AttributeValue=json.dumps(
                {"message_type": self.queue_subscriptions[queue_name]}
            ),
        )
        return arn

    # ......................................................................................

    def destroy_bus(self):
        for queue_name in self._queue_info:
            self._delete_queue(queue_name)
            self._delete_subscription(queue_name)
        self._delete_topic()

    def _delete_queue(self, queue_name):
        try:
            self._sqs_client.delete_queue(QueueUrl=self._url_prefix + queue_name)
        except Exception as exc:
            log.warning("Exception destroying queue", repr(queue_name), ":", str(exc))

    def _delete_subscription(self, queue_name):
        try:
            arn = self.list_subscriptions()[self._arn_prefix+queue_name]
            self._sns_client.unsubscribe(SubscriptionArn=arn)
        except Exception as exc:
            log.warning("Exception destroying subscription for", repr(queue_name), ":", str(exc))

    def _delete_topic(self):
        try:
            self._sns_client.delete_topic(TopicArn=self._topic_arn)
        except Exception as exc:
            log.warning("Exception destroying topic", repr(self._topic_arn), ":", str(exc))

    # ......................................................................................

    def purge_queue(self, queue_name):
        self._sqs_client.purge_queue(QueueUrl=self._url_prefix+queue_name)

    def list_subscriptions(self):
        try:
            response = self._sns_client.list_subscriptions_by_topic(TopicArn=self._topic_arn)
            return {subscription["Endpoint"]:subscription["SubscriptionArn"] 
                    for subscription in response["Subscriptions"]}
        except self._sns_client.exceptions.NotFoundException:
            return []

    def list_queues(self):
        response = self._sqs_client.list_queues(QueueNamePrefix=self.prefix_name)
        return response.get("QueueUrls", [])

    # ......................................................................................

    def send(self, message_sender, message_type, message_dict={}, **message_fields):
        message_dict = dict(message_dict)
        message_dict.update(message_fields)
        message_dict["message_type"] = message_type
        message_dict["message_sender"] = message_sender
        return self._sns_client.publish(
            TopicArn=self._topic_arn,
            Message=json.dumps({"default" : json.dumps(message_dict)}),
            MessageStructure='json',
            MessageAttributes={
                "message_type" : {
                    "DataType" : "String",
                    "StringValue" : message_type,
                },
                "message_sender" : {
                    "DataType" : "String",
                    "StringValue" : message_sender,
                },
            },
        )

# -------------------------------------------------------------

class MessageReceiver:
    def __init__(self, account, region, prefix_name):
        self.account = account
        self.region = region
        self.prefix_name = prefix_name
        self._url_prefix = f"https://sqs.{region}.amazonaws.com/{account}/{prefix_name}-"
        self._sqs_client = boto3.client('sqs')

    def receive(self, queue, wait_time=20):
        queue_url=f"{self._url_prefix}{queue}"
        response = self._sqs_client.receive_message(
            AttributeNames=["All"],
            MessageAttributeNames=["All"],
            QueueUrl=queue_url,
            WaitTimeSeconds=wait_time,  
        )
        message = response["Messages"][0]
        self._sqs_client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )
        serialized=json.loads(message["Body"])
        actual_message = json.loads(serialized["Message"])
        return actual_message

class Messenger:
    def __init__(self, command, bus_config, message_format="json", message_sender=None,
                message_file=None, message_updates=[], queue=None):
        self.command = command
        self.bus_config = yaml.load(bus_config)
        self.message_format = message_format
        self.message_sender = message_sender
        self.message_file = message_file
        self.message_updates = message_updates
        self.queue = queue
        self.bus = MessageBus(
            self.bus_config["account"], 
            self.bus_config["region"], 
            self.bus_config["prefix_name"], 
            self.bus_config["topic_name"], 
            self.bus_config["queue_subscriptions"])
        self.rcvr = MessageReceiver(
            self.bus_config["account"],
            self.bus_config["region"],
            self.bus_config["prefix_name"])
        self.s3_config_path = self.bus_config["s3_output_path"] + "/config.yaml"

    def load_message_file(self):
        if self.format == "json":
            message_dict = json.load(open(self.message_file)) if self.message_file else {}
        else:
            message_dict = yaml.load(self.message_file) if self.message_file else {}
        for update in self.message_updates:
            if update.count("=") != 1:
                raise ValueError("Malformed message key=value update pair.")
            key, value = update.split("=")
            message_dict[key] = value
        return message_dict

    def main(self):
        if self.command == "init-bus":
            self.init_bus()
        elif self.command == "destroy-bus":
            self.destroy_bus()
        elif self.command == "send-message":
            self.send_message()
        elif self.command == "receive-message":
            self.receive_message()

    def init_bus(self):
        self.bus.init_bus()
        with tempfile.NamedTemporaryFile(delete=False) as fileobj:
            fileobj.write(yaml.dumps(self.bus_config))
            fileobj.close()
            s3.upload_filepath(fileobj.name, self.s3_config_path)
            os.remove(fileobj.name)
    
    def destroy_bus(self):
        self.bus.destroy_bus()

    def send_message(self):
        message_type = self.message_dict.get("message_type")
        return self.bus.send_message(
            self.message_sender, message_type, self.message_dict)

    def receive_message(self):
        self.receive_message()

# Start on call from caldp-process to post dataset-processed message.
#
# # Send SNS/SQS message indicating dataset-processed or dataset-error
# aws s3 cp  --quiet ${s3_output_path}/config.yaml  pipeline-config.yaml
# python -m calcloud.messaging \
#     --command send-message \
#     --config-file pipeline-config.yaml \
#     --sender caldp-process \
#     --message-updates \
#         message_type=${message_type} \
#         ipppssoot=${ipppssoot} \
#         s3_output_path=${s3_output_path}

def parse_args(args):
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument(
        '--command', nargs=1, choices=["init-bus", "destroy-bus", "send-message", "receive-message"],
        help='Action for this program run.')
    parser.add_argument(
        '-c', '--config-file', metavar="CONFIG_FILE", dest='bus_config', type=str,
        help='Use configuration parameters from CONFIG_FILE.')
    parser.add_argument(
        '-m', '--message-file', metavar='MESSAGE_FILE', dest='message_file', type=str, default=None,
        help='Use message values from given file.')
    parser.add_argument(
        '-f', '--format', metavar='MESSAGE_FORMAT', dest='message_format', 
        choices=["json", "yaml"], default="json",
        help="Format of message file: json or yaml.")
    parser.add_argument(
        '-u', '--message-updates', nargs="+", dest="message_updates", default={},
        help='Fields to be added or updated to any message file prior to send.  key=value pairs.')
    parser.add_argument(
        '-s', '--sender', metavar="MESSAGE_SENDER", dest='message_sender', type=str,
        help='Name of system sending this message.')
    parser.add_argument(
        '-q', '--queue', metavar='RECEIVE_QUEUE', dest='queue', type=str,
        help='Name of queue to receive message from.')
    return vars(parser.parse_args(args))

def main(args):
    parsed = parse_args(args[1:])
    m = Messenger(**parsed)
    return m.main()

if __name__ == "__main__":
    main(sys.argv)