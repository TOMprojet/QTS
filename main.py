import asyncio
from database.db import fetch_user_configs
from strategies.envelopes.strategie_a import execute_strategy_a_for_user
from strategies.bolltrend.strategie_b import execute_strategy_b_for_user
from utilities.bitget_perp import PerpBitget

async def main():
    # Récupérer les configurations utilisateur.
    user_configs = fetch_user_configs()  # Assurez-vous que cette fonction est asynchrone si nécessaire.

    # Créer une tâche pour chaque utilisateur et stratégie.
    tasks = []
    for account_config in user_configs:
        exchange = PerpBitget(
            public_api=account_config["public_key"],
            secret_api=account_config["secret_key"],
            password=account_config.get("password_api", ""),
        )

        if account_config["strategy"] == "A":
            task = execute_strategy_a_for_user(account_config, exchange)
        elif account_config["strategy"] == "B":
            task = execute_strategy_b_for_user(account_config, exchange)
        else:
            continue  # Si aucune stratégie n'est définie, continuez avec le prochain utilisateur.
        
        # Ajouter la coroutine de la tâche à la liste des tâches à exécuter.
        tasks.append(task)

    # Utiliser asyncio.gather pour exécuter toutes les tâches en parallèle.
    await asyncio.gather(*tasks)

    # Une fois toutes les tâches terminées, fermer les connexions de l'échange.
    for task in tasks:
        await task.exchange.close()

if __name__ == "__main__":
    asyncio.run(main())

