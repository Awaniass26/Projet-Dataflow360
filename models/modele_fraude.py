# import mlflow
# import mlflow.sklearn
# from sklearn.ensemble import RandomForestClassifier

# mlflow.set_experiment("fraud_detection")

# with mlflow.start_run():

#     n_estimators = 200
#     max_depth = 10

#     model = RandomForestClassifier(
#         n_estimators=n_estimators,
#         max_depth=max_depth
#     )

#     model.fit(X_train, y_train)

#     predictions = model.predict(X_test)

#     # Paramètres
#     mlflow.log_param("n_estimators", n_estimators)
#     mlflow.log_param("max_depth", max_depth)

#     # Métriques
#     mlflow.log_metric("accuracy", accuracy)
#     mlflow.log_metric("precision", precision)
#     mlflow.log_metric("recall", recall)
#     mlflow.log_metric("f1_score", f1_score)

#     # Modèle
#     mlflow.sklearn.log_model(
#         model,
#         "fraud_model"
#     )