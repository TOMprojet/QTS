import boto3

def fetch_user_configs():
    dynamodb = boto3.resource('dynamodb', region_name ='eu-west-3')
    table = dynamodb.Table('Users')  # Remplacez 'Users' par le nom de votre table
    response = table.scan()

    return response['Items']
