from aws_cdk import (
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda as _lambda,
    App,
    Stack,
    RemovalPolicy,
    Duration,

)
from constructs import Construct
# pip install without cache

class TifToPngConversionStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # S3 Bucket
        input_bucket = s3.Bucket(self, 'InputBucket', removal_policy=RemovalPolicy.DESTROY)

        conversion_lambda = _lambda.Function(
            self, 'ConversionLambda',
            runtime=_lambda.Runtime.FROM_IMAGE,
            code=_lambda.Code.from_asset_image(directory="../", file="src/dbscan/Dockerfile"),
            handler=_lambda.Handler.FROM_IMAGE,
            environment={
                "OUTPUT_BUCKET_NAME": input_bucket.bucket_name,
            },
            timeout=Duration.minutes(15),
        )

        # Grant Lambda permission to read from S3 bucket
        input_bucket.grant_read(conversion_lambda)

        # EventBridge Rule
        event_rule = events.Rule(
            self, 'EventRule',
            event_pattern={
                'source': ['aws.s3'],
                'detail': {
                    'eventName': ['PutObject'],
                },
                'resources': [input_bucket.bucket_arn],
            }
        )

        # Add Lambda as a target for the EventBridge Rule
        event_rule.add_target(targets.LambdaFunction(conversion_lambda))

        # Lambda IAM Policy to write to S3
        conversion_lambda.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['s3:PutObject'],
                resources=[f"{input_bucket.bucket_arn}/*"]
            )
        )

app = App()
TifToPngConversionStack(app, "TifToPngConversionStack")
app.synth()
