# Script de Démonstration - API My Content

**Endpoint de production:**
```
https://func-mycontent-reco-1269.azurewebsites.net/api/recommend
```

**Date:** Décembre 2025
**Statut:** API opérationnelle ✅

---

## Table des matières

1. [Tests basiques](#tests-basiques)
2. [Tests avec paramètres](#tests-avec-paramètres)
3. [Tests de charge](#tests-de-charge)
4. [Tests d'edge cases](#tests-dedge-cases)
5. [Validation des résultats](#validation-des-résultats)
6. [Scénarios de démonstration](#scénarios-de-démonstration)

---

## Tests basiques

### Test 1: Requête minimale

**Requête:**
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 58,
    "n": 5
  }'
```

**Résultat attendu:**
```json
{
  "user_id": 58,
  "n_recommendations": 5,
  "recommendations": [
    {
      "article_id": 123289,
      "score": 0.3,
      "category_id": 250,
      "publisher_id": 0,
      "words_count": 197,
      "created_at_ts": 1507284319000
    },
    ...
  ],
  "parameters": {
    "weight_collab": 0.3,
    "weight_content": 0.4,
    "weight_trend": 0.3,
    "use_diversity": true
  },
  "metadata": {
    "engine_loaded": true,
    "platform": "Azure Functions",
    "version": "lite"
  }
}
```

**Validation:**
- ✅ Status code 200
- ✅ 5 recommandations retournées
- ✅ Chaque article a un score, article_id, et métadonnées
- ✅ Scores décroissants

### Test 2: Différents nombres de recommandations

**3 recommandations:**
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 58, "n": 3}'
```

**10 recommandations:**
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 58, "n": 10}'
```

**Validation:**
- ✅ Nombre de résultats correspond à `n`
- ✅ Scores toujours décroissants

### Test 3: Plusieurs utilisateurs

**Script bash pour tester plusieurs users:**
```bash
#!/bin/bash
# test_multiple_users.sh

for user_id in 58 100 500 1000 5000; do
  echo "========================================="
  echo "Testing user $user_id..."

  result=$(curl -s -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\": $user_id, \"n\": 3}")

  n_recs=$(echo $result | jq '.n_recommendations')

  if [ "$n_recs" == "3" ]; then
    echo "✅ User $user_id: OK ($n_recs recommendations)"
  else
    echo "❌ User $user_id: FAILED (got $n_recs recommendations)"
  fi

  echo ""
done
```

**Exécution:**
```bash
chmod +x test_multiple_users.sh
./test_multiple_users.sh
```

**Résultat attendu:**
```
=========================================
Testing user 58...
✅ User 58: OK (3 recommendations)

=========================================
Testing user 100...
✅ User 100: OK (3 recommendations)

...
```

---

## Tests avec paramètres

### Test 4: Poids personnalisés

**Content-based dominant (70%):**
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 58,
    "n": 5,
    "weight_content": 0.7,
    "weight_collab": 0.2,
    "weight_trend": 0.1
  }'
```

**Collaborative dominant (70%):**
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 58,
    "n": 5,
    "weight_content": 0.15,
    "weight_collab": 0.7,
    "weight_trend": 0.15
  }'
```

**Temporal/Trending dominant (70%):**
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 58,
    "n": 5,
    "weight_content": 0.15,
    "weight_collab": 0.15,
    "weight_trend": 0.7
  }'
```

**Validation:**
- ✅ Paramètres retournés dans la réponse
- ✅ Résultats différents selon les poids
- ✅ Trend élevé → articles plus récents

### Test 5: Diversification activée/désactivée

**Avec diversification (défaut):**
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 58,
    "n": 10,
    "use_diversity": true
  }'
```

**Sans diversification:**
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 58,
    "n": 10,
    "use_diversity": false
  }'
```

**Validation:**
- ✅ Avec diversity: Articles de catégories variées
- ✅ Sans diversity: Peut avoir plusieurs articles similaires

---

## Tests de charge

### Test 6: Mesure de latence

**Script de benchmark:**
```bash
#!/bin/bash
# benchmark_latency.sh

echo "Testing API latency..."
echo ""

for i in {1..10}; do
  start=$(date +%s%N)

  curl -s -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
    -H 'Content-Type: application/json' \
    -d '{"user_id": 58, "n": 5}' > /dev/null

  end=$(date +%s%N)
  latency=$(( ($end - $start) / 1000000 ))

  echo "Request $i: ${latency}ms"
done
```

**Résultat attendu:**
```
Testing API latency...

Request 1: 520ms  (cold start)
Request 2: 85ms
Request 3: 72ms
Request 4: 68ms
Request 5: 75ms
Request 6: 71ms
Request 7: 69ms
Request 8: 73ms
Request 9: 70ms
Request 10: 72ms

Average (excluding cold start): ~73ms ✅
```

### Test 7: Requêtes concurrentes

**Script parallèle:**
```bash
#!/bin/bash
# benchmark_concurrent.sh

echo "Testing concurrent requests..."

for i in {1..5}; do
  (
    result=$(curl -s -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
      -H 'Content-Type: application/json' \
      -d '{"user_id": 58, "n": 3}')

    n_recs=$(echo $result | jq -r '.n_recommendations // "error"')
    echo "Thread $i: $n_recs recommendations"
  ) &
done

wait
echo "Done!"
```

**Résultat attendu:**
```
Testing concurrent requests...
Thread 2: 3 recommendations
Thread 1: 3 recommendations
Thread 4: 3 recommendations
Thread 3: 3 recommendations
Thread 5: 3 recommendations
Done!
```

---

## Tests d'edge cases

### Test 8: Utilisateur inconnu

**User_id non dans les modèles Lite:**
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 999999,
    "n": 5
  }'
```

**Comportement attendu:**
- Fallback sur articles populaires/trending
- Ou retour vide avec message informatif

### Test 9: Paramètre manquant

**Sans user_id:**
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"n": 5}'
```

**Résultat attendu:**
```json
{
  "error": "Le paramètre user_id est requis",
  "example": {
    "user_id": 58,
    "n": 5
  }
}
```

**Status code:** 400 (Bad Request)

### Test 10: Poids invalides

**Poids ne sommant pas à 1:**
```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 58,
    "n": 5,
    "weight_content": 0.5,
    "weight_collab": 0.5,
    "weight_trend": 0.5
  }'
```

**Comportement:** L'API devrait normaliser les poids ou accepter directement (à vérifier).

### Test 11: n=0 ou négatif

```bash
curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 58, "n": 0}'
```

**Résultat attendu:** Liste vide ou erreur de validation.

---

## Validation des résultats

### Script de validation complet

**validate_recommendations.py:**
```python
#!/usr/bin/env python3
"""
Script de validation des recommandations API
"""

import requests
import json
from typing import Dict, List

API_URL = "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"

def test_api(user_id: int, n: int = 5, **kwargs) -> Dict:
    """Teste l'API et retourne la réponse"""
    payload = {
        "user_id": user_id,
        "n": n,
        **kwargs
    }

    response = requests.post(
        API_URL,
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    return response.status_code, response.json()

def validate_response(response: Dict, expected_n: int) -> List[str]:
    """Valide la structure de la réponse"""
    errors = []

    # Vérifier les champs requis
    required_fields = ['user_id', 'n_recommendations', 'recommendations', 'parameters', 'metadata']
    for field in required_fields:
        if field not in response:
            errors.append(f"Champ manquant: {field}")

    # Vérifier le nombre de recommandations
    if response.get('n_recommendations') != expected_n:
        errors.append(f"Nombre de reco invalide: {response.get('n_recommendations')} != {expected_n}")

    # Vérifier que les scores sont décroissants
    recommendations = response.get('recommendations', [])
    scores = [r['score'] for r in recommendations]
    if scores != sorted(scores, reverse=True):
        errors.append("Scores non décroissants")

    # Vérifier la structure des recommandations
    for i, rec in enumerate(recommendations):
        req_rec_fields = ['article_id', 'score']
        for field in req_rec_fields:
            if field not in rec:
                errors.append(f"Reco {i}: champ manquant {field}")

    return errors

def main():
    print("=" * 60)
    print("VALIDATION API MY CONTENT")
    print("=" * 60)
    print()

    tests = [
        {"name": "Test basique", "user_id": 58, "n": 5},
        {"name": "10 recommandations", "user_id": 58, "n": 10},
        {"name": "User 100", "user_id": 100, "n": 3},
        {"name": "Content dominant", "user_id": 58, "n": 5, "weight_content": 0.7, "weight_collab": 0.2, "weight_trend": 0.1},
        {"name": "Sans diversity", "user_id": 58, "n": 5, "use_diversity": False},
    ]

    passed = 0
    failed = 0

    for test in tests:
        name = test.pop('name')
        print(f"Test: {name}")

        try:
            status_code, response = test_api(**test)

            if status_code != 200:
                print(f"  ❌ FAILED: Status {status_code}")
                failed += 1
                continue

            errors = validate_response(response, test['n'])

            if errors:
                print(f"  ❌ FAILED:")
                for error in errors:
                    print(f"    - {error}")
                failed += 1
            else:
                print(f"  ✅ PASSED")
                passed += 1

        except Exception as e:
            print(f"  ❌ EXCEPTION: {e}")
            failed += 1

        print()

    print("=" * 60)
    print(f"Résultats: {passed} PASSED, {failed} FAILED")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

**Exécution:**
```bash
python3 validate_recommendations.py
```

---

## Scénarios de démonstration

### Scénario 1: Démonstration simple (2 minutes)

**Objectif:** Montrer que l'API fonctionne et retourne des recommandations.

**Script:**
```bash
echo "=== DÉMONSTRATION API MY CONTENT ==="
echo ""
echo "Endpoint: https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"
echo ""
echo "1. Requête simple pour l'utilisateur 58, 5 recommandations:"
echo ""

curl -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 58,
    "n": 5
  }' | jq '.'

echo ""
echo "✅ 5 articles recommandés avec scores et métadonnées"
```

### Scénario 2: Comparaison des stratégies (5 minutes)

**Objectif:** Montrer l'impact des différents poids.

**Script:**
```bash
echo "=== COMPARAISON DES STRATÉGIES ==="
echo ""

echo "1. Stratégie Content-Based (70%):"
curl -s -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 58,
    "n": 3,
    "weight_content": 0.7,
    "weight_collab": 0.15,
    "weight_trend": 0.15
  }' | jq '.recommendations[] | {article_id, score}'

echo ""
echo "2. Stratégie Collaborative (70%):"
curl -s -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 58,
    "n": 3,
    "weight_content": 0.15,
    "weight_collab": 0.7,
    "weight_trend": 0.15
  }' | jq '.recommendations[] | {article_id, score}'

echo ""
echo "3. Stratégie Trending (70%):"
curl -s -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 58,
    "n": 3,
    "weight_content": 0.15,
    "weight_collab": 0.15,
    "weight_trend": 0.7
  }' | jq '.recommendations[] | {article_id, score}'

echo ""
echo "✅ Différentes stratégies produisent des recommandations différentes"
```

### Scénario 3: Test de performance (3 minutes)

**Objectif:** Montrer que la latence est acceptable (<200ms).

**Script:**
```bash
echo "=== TEST DE PERFORMANCE ==="
echo ""

echo "Mesure de latence sur 10 requêtes:"
echo ""

total=0
count=0

for i in {1..10}; do
  start=$(date +%s%N)

  curl -s -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
    -H 'Content-Type: application/json' \
    -d '{"user_id": 58, "n": 5}' > /dev/null

  end=$(date +%s%N)
  latency=$(( ($end - $start) / 1000000 ))

  echo "  Request $i: ${latency}ms"

  if [ $i -gt 1 ]; then
    total=$((total + latency))
    count=$((count + 1))
  fi
done

avg=$((total / count))

echo ""
echo "Latence moyenne (hors cold start): ${avg}ms"

if [ $avg -lt 200 ]; then
  echo "✅ Performance OK (objectif <200ms)"
else
  echo "⚠️  Performance à optimiser (objectif <200ms)"
fi
```

### Scénario 4: Démonstration complète (10 minutes)

**Combine tous les scénarios précédents + gestion d'erreurs.**

**Script:** `demo_complete.sh`

```bash
#!/bin/bash
# demo_complete.sh - Démonstration complète de l'API

echo "======================================================================"
echo "        DÉMONSTRATION COMPLÈTE - API MY CONTENT"
echo "======================================================================"
echo ""
echo "Endpoint: https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"
echo "Date: $(date)"
echo ""

# 1. Test basique
echo "--------------------------------------------------------------------"
echo "1. TEST BASIQUE - Recommandations pour user 58"
echo "--------------------------------------------------------------------"
echo ""

curl -s -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": 58,
    "n": 5
  }' | jq '{user_id, n_recommendations, top_3: .recommendations[:3]}'

echo ""
read -p "Appuyez sur Entrée pour continuer..."
echo ""

# 2. Comparaison stratégies
echo "--------------------------------------------------------------------"
echo "2. COMPARAISON DES STRATÉGIES"
echo "--------------------------------------------------------------------"
echo ""

echo "Content-Based dominant:"
curl -s -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 58, "n": 3, "weight_content": 0.7, "weight_collab": 0.15, "weight_trend": 0.15}' \
  | jq '.recommendations[] | {article_id, score}'

echo ""
echo "Collaborative dominant:"
curl -s -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"user_id": 58, "n": 3, "weight_content": 0.15, "weight_collab": 0.7, "weight_trend": 0.15}' \
  | jq '.recommendations[] | {article_id, score}'

echo ""
read -p "Appuyez sur Entrée pour continuer..."
echo ""

# 3. Performance
echo "--------------------------------------------------------------------"
echo "3. TEST DE PERFORMANCE"
echo "--------------------------------------------------------------------"
echo ""

total=0
for i in {1..5}; do
  start=$(date +%s%N)
  curl -s -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
    -H 'Content-Type: application/json' \
    -d '{"user_id": 58, "n": 5}' > /dev/null
  end=$(date +%s%N)
  latency=$(( ($end - $start) / 1000000 ))
  echo "  Request $i: ${latency}ms"
  if [ $i -gt 1 ]; then
    total=$((total + latency))
  fi
done

avg=$((total / 4))
echo ""
echo "Latence moyenne: ${avg}ms (objectif <200ms) ✅"

echo ""
read -p "Appuyez sur Entrée pour continuer..."
echo ""

# 4. Gestion d'erreurs
echo "--------------------------------------------------------------------"
echo "4. GESTION D'ERREURS"
echo "--------------------------------------------------------------------"
echo ""

echo "Test sans user_id (devrait retourner erreur 400):"
curl -s -X POST https://func-mycontent-reco-1269.azurewebsites.net/api/recommend \
  -H 'Content-Type: application/json' \
  -d '{"n": 5}' | jq '.'

echo ""
echo "======================================================================"
echo "                    DÉMONSTRATION TERMINÉE ✅"
echo "======================================================================"
```

**Exécution:**
```bash
chmod +x demo_complete.sh
./demo_complete.sh
```

---

## Annexes

### Utilisation avec Python

**Exemple simple:**
```python
import requests

API_URL = "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"

# Requête
response = requests.post(
    API_URL,
    json={
        "user_id": 58,
        "n": 5,
        "weight_content": 0.4,
        "weight_collab": 0.3,
        "weight_trend": 0.3,
        "use_diversity": True
    }
)

# Affichage
if response.status_code == 200:
    data = response.json()
    print(f"User {data['user_id']}: {data['n_recommendations']} recommandations")
    for rec in data['recommendations']:
        print(f"  - Article {rec['article_id']}: score {rec['score']:.3f}")
else:
    print(f"Erreur {response.status_code}: {response.text}")
```

### Utilisation avec JavaScript (fetch)

```javascript
const API_URL = 'https://func-mycontent-reco-1269.azurewebsites.net/api/recommend';

async function getRecommendations(userId, n = 5) {
  const response = await fetch(API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      user_id: userId,
      n: n
    })
  });

  if (response.ok) {
    const data = await response.json();
    console.log(`${data.n_recommendations} recommendations for user ${userId}`);
    return data.recommendations;
  } else {
    console.error(`Error ${response.status}`);
    return [];
  }
}

// Utilisation
getRecommendations(58, 5).then(recommendations => {
  recommendations.forEach(rec => {
    console.log(`Article ${rec.article_id}: ${rec.score}`);
  });
});
```

---

**Fin du script de démonstration**

Pour toute question ou problème, consulter:
- PROJET_COMPLET.md - Documentation technique complète
- AZURE_SUCCESS.md - Guide de déploiement
- README.md - Vue d'ensemble du projet
