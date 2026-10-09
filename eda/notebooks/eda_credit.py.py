#!/usr/bin/env python
# coding: utf-8

# In[1]:


import seaborn as sns
import matplotlib.pyplot as plt
#Importation du fichier
import pandas as pd
import numpy as np 
df=pd.read_csv("/home/mariama-oury/Documents/Data_Flow360/Projet-Dataflow360/notebooks/dataflow360_mobile_money_credit(1).csv")
df.head()


# In[2]:


df.info()


# In[3]:


df.head(100)


# In[4]:


# Affiche les modalités avec leur nombre d'apparitions (inclut les NaN)
print(df['eligibilite'].value_counts(dropna=False))


# In[5]:


#Nombre de lignes et de colonnes du dataset
df.shape


# In[6]:


#Valeurs manquantes
df.isnull().sum()


# In[7]:


#Valeurs manquantes
df.isnull().sum()


# In[8]:


# Compter le nombre de lignes doublons
nb_doublons = df.duplicated().sum()
print(f"Nombre de doublons stricts : {nb_doublons}")


# In[9]:


#Verification des types de variables 
df.info()


# In[10]:


#Verification des valeurs aberrantes
df.describe()


# In[11]:


# Verification des valeurs aberrantes
# 1. Sélection de toutes les colonnes numériques
num_cols = df.select_dtypes(include=['int64', 'float64']).columns

# 2. Création d'une grille de graphiques (ex: 5 lignes x 4 colonnes = 20 variables)
fig, axes = plt.subplots(nrows=5, ncols=4, figsize=(18, 14))
axes = axes.flatten()  # Applatir la grille pour boucler facilement dessus

# 3. Boucle pour afficher chaque boxplot
for i, col in enumerate(num_cols):
    sns.boxplot(x=df[col], ax=axes[i], color='skyblue')
    axes[i].set_title(col, fontsize=10)
    axes[i].set_xlabel('')

# Masquer les sous-graphiques vides s'il y a moins de 20 variables
for j in range(i + 1, len(axes)):
    fig.delaxes(axes[j])

plt.tight_layout()
plt.show()


# In[12]:


# ---------------------------------------------------------
# A. Matrice de Corrélation globale
# ---------------------------------------------------------
plt.figure(figsize=(14, 10))
corr_matrix = df.corr(numeric_only=True)

#Masque pour cacher la moitié supérieure symétrique (plus lisible)
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

sns.heatmap(
    corr_matrix, 
    mask=mask,
    annot=True, 
    fmt=".2f", 
    cmap="coolwarm", 
    vmin=-1, vmax=1, 
    linewidths=0.5
)
plt.title("Matrice de Corrélation - 20 Variables Quantitatives", fontsize=14)
plt.tight_layout()
plt.show()

# ---------------------------------------------------------
# B. Détection automatique des fortes colinéarités (|r| >= 0.70)
# ---------------------------------------------------------
upper_tri = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
strong_corr = upper_tri.stack().reset_index()
strong_corr.columns = ['Variable 1', 'Variable 2', 'Correlation']
strong_corr = strong_corr[strong_corr['Correlation'].abs() >= 0.70].sort_values(by='Correlation', ascending=False)

print("--- Paires de variables fortement corrélées (|r| >= 0.70) ---")
print(strong_corr)

# ---------------------------------------------------------
# C. Distribution de toutes les variables (Histogames + KDE)
# ---------------------------------------------------------
df.hist(figsize=(18, 14), bins=30, color='teal', edgecolor='black', grid=False)
plt.suptitle("Distributions des 20 variables quantitatives", fontsize=16)
plt.tight_layout()
plt.show()


# In[13]:


#Quantifier la distribution des variables quantitatives
skewness = df.select_dtypes(include="number").skew()

print(
    skewness
    .sort_values(ascending=False)
)


# In[14]:


# 5. Vérifier qu'il n'y a plus de NaN
print("\nModalités après conversion :")
print(df['eligibilite'].value_counts(dropna=False))


# In[15]:


# 1. S'assurer que la colonne est bien au format numérique
df['eligibilite'] = df['eligibilite'].astype(int)

# 2. Recalcul de la matrice de corrélation
corr_matrix = df.corr(numeric_only=True)

# 3. Extraction et tri
corr_defaut = corr_matrix[['eligibilite']].drop('eligibilite').sort_values(by='eligibilite', ascending=False)

# 4. Affichage graphique
plt.rcdefaults()
plt.figure(figsize=(5, 8))

sns.heatmap(
    corr_defaut, 
    annot=True, 
    fmt=".2f", 
    cmap="coolwarm", 
    vmin=-1, 
    vmax=1,
    cbar=True,
    linewidths=0.5,
    annot_kws={"size": 10, "weight": "bold"}
)

plt.title("Corrélation des variables avec 'eligibilite'", pad=15)
plt.tight_layout()
plt.show()


# In[16]:


# 2. Proportions en pourcentage (%)
print("\n--- Proportions (%) ---")
print(df["eligibilite"].value_counts(normalize=True) * 100)


# In[17]:


# 1. Effectifs bruts (nombre de lignes)
print("--- Effectifs bruts ---")
print(df["eligibilite"].value_counts())


# In[18]:


#Repartition des eligibles et non_eligibles par type d'activité

# Graphique en barres
pd.crosstab(df['type_activite'], df['eligibilite']).plot(
    kind='bar', 
    stacked=True, 
    figsize=(10, 6),
    color=['#4169E1', '#DC143C']
)

plt.title("Répartition des éligibles et non-éligibles par type d'activité")
plt.xlabel("Type d'activité")
plt.ylabel("Nombre de clients")
plt.xticks(rotation=45, ha='right')
plt.legend(["Non-éligible (0)", "Éligible (1)"])
plt.tight_layout()
plt.show()


# In[19]:


# Tableau avec les effectifs bruts (comptages)
tableau_frequences = pd.crosstab(df['type_activite'], df['eligibilite'])
print(tableau_frequences)


# In[20]:


import scipy.stats as stats

# 1. Calcul du tableau de contingence brut
tableau_contingence = pd.crosstab(df["type_activite"], df["eligibilite"])

# 2. Calcul du test du Khi-deux et récupération des effectifs théoriques
chi2, p_value, dof, attendus = stats.chi2_contingency(tableau_contingence)

# 3. Calcul des résidus standardisés
observes = tableau_contingence.values
residus = (observes - attendus) / np.sqrt(attendus)

# 4. Reconstruction automatique du DataFrame avec la bonne forme (shape)
df_residus = pd.DataFrame(
    residus, index=tableau_contingence.index, columns=tableau_contingence.columns
)

# 5. Affichage de la Heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(df_residus, annot=True, cmap="coolwarm", center=0, fmt=".2f")

plt.title("Analyse locale du lien : Type d'activité vs Éligibilité")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()


# In[21]:


from scipy.stats.contingency import association

# Calcul direct du V de Cramer à partir de votre tableau de contingence
v_cramer = association(tableau_contingence, method="cramer")

print(f"V de Cramer : {v_cramer:.4f}")


# In[22]:


import math

# 1. Liste de toutes vos variables numériques (excluant 'defaut')
variables_num = [
    'age',
    'anciennete_compte_mois',
    'nb_transactions_90j',
    'montant_transactions_90j',
    'montant_entrees_90j',
    'montant_sorties_90j',
    'solde_moyen_90j',
    'regularite_revenus',
    'nombre_credits_en_retard',
    'nombre_credits_impayes',
    'montant_credit_demande',
    'duree_credit_demande',
    'nb_credits_impayes',
    'stabilite_flux',
    'taux_remboursement',
]

# 2. Configuration de la grille de graphiques (ex: 5 lignes x 4 colonnes)
n_vars = len(variables_num)
n_cols = 4
n_rows = math.ceil(n_vars / n_cols)

fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, 4 * n_rows))
axes = axes.flatten()  # Aplatir la grille pour faciliter la boucle

# 3. Génération des Boxplots comparatifs par variable
for i, col in enumerate(variables_num):
    if col in df.columns:
        sns.boxplot(
            data=df,
            x='eligibilite',
            y=col,
            ax=axes[i],
            palette='Set2',
            showfliers=True,  # Met à False si tu veux cacher les outliers extrêmes
        )
        axes[i].set_title(f'{col} vs defaut', fontsize=11, fontweight='bold')
        axes[i].set_xlabel('Statut Défaut (0 = Non, 1 = Oui)')
        axes[i].set_ylabel(col)
        axes[i].grid(True, linestyle='--', alpha=0.5)

# 4. Supprimer les axes inutilisés dans la grille
for j in range(i + 1, len(axes)):
    fig.delaxes(axes[j])

plt.tight_layout()
plt.show()


# In[23]:


# Affiche la médiane exacte du taux de remboursement pour chaque groupe
df.groupby('eligibilite')['taux_remboursement'].median()


# In[24]:


print(df["taux_remboursement"].unique())


# In[25]:


#Valeurs manquantes
df.isnull().sum()


# In[26]:


#Convertir le df en csv
df.to_csv("dataset_credit_clean.csv", index=False)


# In[27]:


from scipy import stats


# In[28]:


from scipy.stats import chi2_contingency

table = pd.crosstab(df["type_activite"], df["eligibilite"])

chi2, p, ddl, expected = chi2_contingency(table)

print("Chi² :", chi2)
print("p-value :", p)


# In[29]:


n = table.to_numpy().sum()
r, k = table.shape

cramers_v = np.sqrt(
    chi2 / (n * min(r - 1, k - 1))
)

print("Cramér's V :", cramers_v)


# In[30]:


from scipy.stats import pearsonr

# Variables quantitatives
variables_quantitatives = df.select_dtypes(include="number").columns.tolist()

# Retirer les identifiants et la cible
variables_quantitatives = [
    col for col in variables_quantitatives
    if col not in ["client_id", "eligibilite"]
]

# Calcul des corrélations et p-values
resultats = []

for variable in variables_quantitatives:
    # Retirer les valeurs manquantes pour cette paire
    data = df[[variable, "eligibilite"]].dropna()

    correlation, p_value = pearsonr(
        data[variable],
        data["eligibilite"]
    )

    resultats.append({
        "variable": variable,
        "correlation": correlation,
        "p_value": p_value
    })

# Transformer en DataFrame
resultats = pd.DataFrame(resultats)

# Trier par valeur absolue de la corrélation
resultats["abs_correlation"] = resultats["correlation"].abs()

resultats = resultats.sort_values(
    "abs_correlation",
    ascending=False
)

print(resultats)


# In[31]:


#Comparaison des éligibles et des non_éligibles avec toutes les variables quantitatives 
variables_quantitatives = [
    "age",
    "anciennete_compte_mois",
    "nb_transactions_90j",
    "montant_transactions_90j",
    "montant_entrees_90j",
    "montant_sorties_90j",
    "solde_moyen_90j",
    "regularite_revenus",
    "nombre_credits_precedents",
    "taux_remboursement",
    "nombre_credits_en_retard",
    "nombre_credits_impayes",
    "montant_credit_demande",
    "duree_credit_demande",
    "stabilite_flux"
]

comparaison = df.groupby("eligibilite")[variables_quantitatives].median().T

print(comparaison)


# In[32]:


from scipy.stats import mannwhitneyu

resultats_mann_whitney = []

for variable in variables_quantitatives:

    groupe_eligible = df.loc[
        df["eligibilite"] == "eligible",
        variable
    ].dropna()

    groupe_non_eligible = df.loc[
        df["eligibilite"] == "non_eligible",
        variable
    ].dropna()

    statistique, p_value = mannwhitneyu(
        groupe_eligible,
        groupe_non_eligible,
        alternative="two-sided"
    )

    resultats_mann_whitney.append({
        "variable": variable,
        "U": statistique,
        "p_value": p_value
    })

resultats_mann_whitney = pd.DataFrame(resultats_mann_whitney)

resultats_mann_whitney = resultats_mann_whitney.sort_values(
    "p_value"
)

print(resultats_mann_whitney)


# In[33]:


variables_importantes = [
    "regularite_revenus",
    "taux_remboursement",
    "stabilite_flux",
    "nb_transactions_90j",
    "montant_entrees_90j",
    "solde_moyen_90j",
    "nombre_credits_impayes"
]

for variable in variables_importantes:

    plt.figure(figsize=(8, 5))

    sns.boxplot(
        data=df,
        x="eligibilite",
        y=variable
    )

    plt.title(f"{variable} selon l'éligibilité")
    plt.xlabel("Éligibilité")
    plt.ylabel(variable)

    plt.show()


# In[34]:


# Nombre de valeurs manquantes
valeurs_manquantes = df.isna().sum()

# Pourcentage de valeurs manquantes
pourcentage_manquant = (df.isna().mean() * 100).round(2)

# Tableau récapitulatif
manquants = pd.DataFrame({
    "nombre_manquant": valeurs_manquantes,
    "pourcentage_manquant": pourcentage_manquant
})

# Garder uniquement les variables qui ont des valeurs manquantes
manquants = manquants[manquants["nombre_manquant"] > 0]

print(manquants)


# In[35]:


print(
    df[df["taux_remboursement"].isna()]
    ["nombre_credits_precedents"]
    .value_counts()
    .sort_index()
)


# In[36]:


print(
    pd.crosstab(
        df["nombre_credits_precedents"],
        df["taux_remboursement"].isna(),
        normalize="index"
    ) * 100
)


# In[37]:


pd.crosstab(
    df["nombre_credits_precedents"] == 0,
    df["eligibilite"],
    normalize="index"
) * 100


# In[38]:


resultats_outliers = []

for variable in variables_quantitatives:

    Q1 = df[variable].quantile(0.25)
    Q3 = df[variable].quantile(0.75)

    IQR = Q3 - Q1

    borne_inferieure = Q1 - 1.5 * IQR
    borne_superieure = Q3 + 1.5 * IQR

    outliers = (
        (df[variable] < borne_inferieure) |
        (df[variable] > borne_superieure)
    )

    nombre_outliers = outliers.sum()

    pourcentage_outliers = (
        nombre_outliers / len(df) * 100
    )

    resultats_outliers.append({
        "variable": variable,
        "Q1": Q1,
        "Q3": Q3,
        "IQR": IQR,
        "borne_inferieure": borne_inferieure,
        "borne_superieure": borne_superieure,
        "nombre_outliers": nombre_outliers,
        "pourcentage_outliers": round(pourcentage_outliers, 2)
    })

resultats_outliers = pd.DataFrame(resultats_outliers)

resultats_outliers = resultats_outliers.sort_values(
    "pourcentage_outliers",
    ascending=False
)

print(resultats_outliers)


# In[39]:


#Convertir le df en csv
df.to_csv("dataset_Scoring_credit_2000000.csv", index=False)

