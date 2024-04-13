import boto3
from botocore.exceptions import ClientError

# Initialisation du client DynamoDB
dynamodb = boto3.resource('dynamodb', region_name = 'eu-west-3')
table = dynamodb.Table('Users')  # Remplacez par le nom réel de votre table

# Fonction pour supprimer un utilisateur de la table
def delete_user_from_table(user_id):
    try:
        response = table.delete_item(
            Key={
                'user_id': user_id  # Utilisez la clé de partition exacte
            }
        )
        print(f"Utilisateur {user_id} supprimé avec succès.")
    except ClientError as e:
        print(f"Erreur lors de la suppression de l'utilisateur {user_id}: {e}")

# Remplacez '0002' par l'ID utilisateur que vous souhaitez supprimer
delete_user_from_table('0002')
