import boto3
from botocore.exceptions import ClientError

# Initialisation du client DynamoDB
dynamodb = boto3.resource('dynamodb', region_name ='eu-west-3')
table = dynamodb.Table('Users')  # Remplacez par le nom réel de votre table

# Liste d'utilisateurs à ajouter à la table
users_to_add = [
    {
        'user_id': '0002',
        'date': '14/04/2024',
        'email': 'janedoe@example.com',
        'password': 'JaneSecurePass92!',
        'password_api': 'JaneApiPass92!',
        'public_key': 'bg_15ExamplePublicKey',
        'secret_key': 'bdExampleSecretKey',
        'strategy': 'B',
        'user_name': 'JaneDoe'
    },
    # Plus d'utilisateurs...
]

# Fonction pour insérer des utilisateurs dans la table
def add_users_to_table(users_list):
    for user in users_list:
        try:
            table.put_item(Item=user)
            print(f"Utilisateur {user['user_id']} inséré avec succès.")
        except ClientError as e:
            print(f"Erreur lors de l'insertion de l'utilisateur {user['user_id']}: {e}")

# Exécutez la fonction pour ajouter des utilisateurs
add_users_to_table(users_to_add)
