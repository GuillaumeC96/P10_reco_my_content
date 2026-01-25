#!/usr/bin/env python3
"""
Test de charge de l'API Azure Functions
Teste la latence et la fiabilité de l'API avec plusieurs requêtes concurrentes
"""

import requests
import time
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Configuration
API_URL = "https://func-mycontent-reco-1269.azurewebsites.net/api/recommend"
N_REQUESTS = 50  # Nombre total de requêtes
N_CONCURRENT = 10  # Nombre de requêtes concurrentes
USERS_TO_TEST = [58, 100, 500, 1000, 2000, 5000]  # Différents users

# Couleurs
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def print_section(title):
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}{title}{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")

def print_success(msg):
    print(f"{GREEN}✅ {msg}{NC}")

def print_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{NC}")

def print_error(msg):
    print(f"{RED}❌ {msg}{NC}")

def test_single_request(user_id, n_recommendations=5):
    """Test une seule requête et retourne le temps de réponse"""
    payload = {
        "user_id": user_id,
        "n": n_recommendations
    }

    start_time = time.time()
    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        elapsed = (time.time() - start_time) * 1000  # en ms

        if response.status_code == 200:
            data = response.json()
            n_results = len(data.get('recommendations', []))
            return {
                'success': True,
                'latency_ms': elapsed,
                'user_id': user_id,
                'n_results': n_results,
                'status_code': response.status_code
            }
        else:
            return {
                'success': False,
                'latency_ms': elapsed,
                'user_id': user_id,
                'error': f"Status {response.status_code}",
                'status_code': response.status_code
            }
    except Exception as e:
        elapsed = (time.time() - start_time) * 1000
        return {
            'success': False,
            'latency_ms': elapsed,
            'user_id': user_id,
            'error': str(e),
            'status_code': 0
        }

def run_load_test():
    """Execute le test de charge"""
    print_section("TEST DE CHARGE API AZURE FUNCTIONS")

    print(f"Configuration:")
    print(f"  - API URL: {API_URL}")
    print(f"  - Nombre total de requêtes: {N_REQUESTS}")
    print(f"  - Requêtes concurrentes: {N_CONCURRENT}")
    print(f"  - Users testés: {USERS_TO_TEST}")

    # 1. TEST DE CONNECTIVITÉ
    print_section("1. TEST DE CONNECTIVITÉ")
    result = test_single_request(USERS_TO_TEST[0])
    if result['success']:
        print_success(f"API accessible - Latence: {result['latency_ms']:.0f}ms")
    else:
        print_error(f"API non accessible: {result.get('error')}")
        return

    # 2. TEST DE LATENCE PAR USER
    print_section("2. TEST DE LATENCE PAR USER")
    print("Test de différents utilisateurs...\n")

    for user_id in USERS_TO_TEST:
        result = test_single_request(user_id, n_recommendations=5)
        if result['success']:
            print(f"User {user_id:5d}: {result['latency_ms']:6.0f}ms - {result['n_results']} recommandations")
        else:
            print(f"User {user_id:5d}: {RED}ÉCHEC{NC} - {result.get('error')}")

    # 3. TEST DE CHARGE CONCURRENT
    print_section("3. TEST DE CHARGE CONCURRENT")
    print(f"Lancement de {N_REQUESTS} requêtes avec {N_CONCURRENT} workers concurrents...\n")

    results = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=N_CONCURRENT) as executor:
        # Créer les futures
        futures = []
        for i in range(N_REQUESTS):
            user_id = USERS_TO_TEST[i % len(USERS_TO_TEST)]
            future = executor.submit(test_single_request, user_id)
            futures.append(future)

        # Collecter les résultats avec barre de progression
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            if completed % 10 == 0:
                print(f"  Progression: {completed}/{N_REQUESTS} requêtes complétées")

    total_time = time.time() - start_time

    # 4. ANALYSE DES RÉSULTATS
    print_section("4. ANALYSE DES RÉSULTATS")

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"Requêtes réussies: {len(successful)}/{N_REQUESTS} ({len(successful)/N_REQUESTS*100:.1f}%)")
    print(f"Requêtes échouées: {len(failed)}/{N_REQUESTS} ({len(failed)/N_REQUESTS*100:.1f}%)")
    print(f"Temps total: {total_time:.2f}s")
    print(f"Throughput: {N_REQUESTS/total_time:.2f} req/s")

    if successful:
        latencies = [r['latency_ms'] for r in successful]

        print(f"\n{BLUE}Statistiques de latence:{NC}")
        print(f"  - Moyenne:   {statistics.mean(latencies):6.0f}ms")
        print(f"  - Médiane:   {statistics.median(latencies):6.0f}ms")
        print(f"  - Min:       {min(latencies):6.0f}ms")
        print(f"  - Max:       {max(latencies):6.0f}ms")
        print(f"  - P50:       {statistics.median(latencies):6.0f}ms")
        print(f"  - P95:       {sorted(latencies)[int(len(latencies)*0.95)]:6.0f}ms")
        print(f"  - P99:       {sorted(latencies)[int(len(latencies)*0.99)]:6.0f}ms")

    if failed:
        print(f"\n{RED}Erreurs rencontrées:{NC}")
        error_types = {}
        for r in failed:
            error = r.get('error', 'Unknown')
            error_types[error] = error_types.get(error, 0) + 1

        for error, count in error_types.items():
            print(f"  - {error}: {count} fois")

    # 5. ÉVALUATION
    print_section("5. ÉVALUATION")

    success_rate = len(successful) / N_REQUESTS
    avg_latency = statistics.mean([r['latency_ms'] for r in successful]) if successful else 0

    if success_rate >= 0.95 and avg_latency < 500:
        print_success("✅ EXCELLENT - API performante et fiable")
    elif success_rate >= 0.90 and avg_latency < 1000:
        print_warning("⚠️  BON - Quelques améliorations possibles")
    elif success_rate >= 0.80:
        print_warning("⚠️  MOYEN - Performance à améliorer")
    else:
        print_error("❌ INSUFFISANT - Problèmes de performance détectés")

    print(f"\n{BLUE}Recommandations:{NC}")
    if avg_latency > 500:
        print("  - Considérer un plan Premium pour réduire la latence")
    if success_rate < 0.95:
        print("  - Investiguer les causes d'échec")
    if avg_latency < 200:
        print("  - Performance excellente, aucune action requise")

    # 6. EXPORT DES RÉSULTATS
    print_section("6. EXPORT DES RÉSULTATS")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_charge_results_{timestamp}.json"

    report = {
        'timestamp': timestamp,
        'config': {
            'api_url': API_URL,
            'n_requests': N_REQUESTS,
            'n_concurrent': N_CONCURRENT,
            'users_tested': USERS_TO_TEST
        },
        'summary': {
            'total_requests': N_REQUESTS,
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': success_rate,
            'total_time_seconds': total_time,
            'throughput_req_per_sec': N_REQUESTS/total_time
        },
        'latency_stats': {
            'mean_ms': statistics.mean(latencies) if successful else 0,
            'median_ms': statistics.median(latencies) if successful else 0,
            'min_ms': min(latencies) if successful else 0,
            'max_ms': max(latencies) if successful else 0,
            'p95_ms': sorted(latencies)[int(len(latencies)*0.95)] if successful else 0,
            'p99_ms': sorted(latencies)[int(len(latencies)*0.99)] if successful else 0
        },
        'detailed_results': results
    }

    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    print_success(f"Résultats exportés: {filename}")

    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}TEST DE CHARGE TERMINÉ{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")

if __name__ == "__main__":
    run_load_test()
