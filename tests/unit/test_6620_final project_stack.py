import aws_cdk as core
import aws_cdk.assertions as assertions

from 6620_final project.6620_final project_stack import 6620FinalProjectStack

# example tests. To run these tests, uncomment this file along with the example
# resource in 6620_final project/6620_final project_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = 6620FinalProjectStack(app, "6620-final-project")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
