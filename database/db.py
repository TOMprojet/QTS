import boto3

def fetch_user_configs():
    # Initialisation du client DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-3')
    table = dynamodb.Table('Users')  # Remplacez par le nom réel de votre table

    # Utilisation de la fonction scan pour récupérer seulement les attributs spécifiques
    response = table.scan(
        ProjectionExpression="public_key, secret_key, password_api, strategy"
    )

    # Extrait uniquement les items qui contiennent les attributs nécessaires
    user_configs = response['Items']
    
    # S'il y a d'autres pages de résultats, continuez à les récupérer
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            ProjectionExpression="public_key, secret_key, password_api, strategy",
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        user_configs.extend(response['Items'])

    return user_configs

# Appel de la fonction
user_configs = fetch_user_configs()
print(user_configs)
