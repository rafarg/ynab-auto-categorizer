#!/usr/bin/env python3
"""
YNAB Auto-Categorizer and Reporter
Categoriza transacciones con confirmación interactiva y sugerencias IA
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import os
import sys
import argparse
from collections import defaultdict
from pathlib import Path

# Archivo de reglas personalizado
RULES_FILE = Path(__file__).parent / "categorization_rules.json"


class YNABAutoCategorizer:
    def __init__(self, api_token: str, budget_id: str = "last-used"):
        """
        Inicializa el categorizador de YNAB
        """
        self.api_token = api_token
        self.budget_id = budget_id
        self.base_url = "https://api.ynab.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        # Cargar reglas desde archivo o usar por defecto
        self.categorization_rules = self._load_rules()
        self._categories_cache = None

    def _load_rules(self) -> Dict[str, List[str]]:
        """Carga reglas desde archivo JSON o usa las por defecto"""
        if RULES_FILE.exists():
            try:
                with open(RULES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass

        # Reglas por defecto
        return {
            "Supermercado": ["mercadona", "carrefour", "lidl", "aldi", "dia", "eroski", "alcampo", "hipercor"],
            "Restaurantes y bares": ["restaurant", "mcdonald", "burger", "pizza", "kebab", "cafeteria", "bar", "cerveceria"],
            "Gasolina": ["shell", "repsol", "cepsa", "bp", "galp", "gasolinera"],
            "Transporte Público": ["metro", "renfe", "uber", "cabify", "taxi", "bus", "emt"],
            "Suscripciones": ["netflix", "spotify", "hbo", "disney", "prime video", "youtube", "apple"],
            "Internet y móviles": ["vodafone", "movistar", "orange", "yoigo", "masmovil", "pepephone", "digi"],
            "Suministros (luz, agua y gas)": ["iberdrola", "endesa", "naturgy", "aqualia", "octopus", "holaluz"],
            "Ropa": ["zara", "h&m", "mango", "pull&bear", "bershka", "primark", "decathlon"],
            "Salud y belleza": ["farmacia", "pharmacy", "druni", "primor", "sephora"],
            "Deporte": ["gym", "gimnasio", "fitness", "mcfit", "basicfit"],
        }

    def _save_rules(self):
        """Guarda las reglas en archivo JSON"""
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.categorization_rules, f, ensure_ascii=False, indent=2)
        print(f"   💾 Regla guardada en {RULES_FILE.name}")

    def get_categories(self) -> Dict[str, str]:
        """Obtiene todas las categorías del presupuesto"""
        if self._categories_cache:
            return self._categories_cache

        url = f"{self.base_url}/budgets/{self.budget_id}/categories"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        categories = {}
        for group in response.json()["data"]["category_groups"]:
            for category in group["categories"]:
                if not category.get("hidden", False):
                    categories[category["name"]] = category["id"]

        self._categories_cache = categories
        return categories

    def get_monthly_budget(self, month: str = None) -> Dict[str, Dict]:
        """Obtiene el presupuesto mensual por categoría"""
        if month is None:
            month = datetime.now().strftime("%Y-%m-01")

        url = f"{self.base_url}/budgets/{self.budget_id}/months/{month}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        budget_data = {}
        for category in response.json()["data"]["month"]["categories"]:
            budget_data[category["name"]] = {
                "id": category["id"],
                "budgeted": category["budgeted"] / 1000,
                "activity": category["activity"] / 1000,
                "balance": category["balance"] / 1000,
            }

        return budget_data

    def get_uncategorized_transactions(self, days_back: int = 30) -> List[Dict]:
        """Obtiene transacciones sin categorizar"""
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        url = f"{self.base_url}/budgets/{self.budget_id}/transactions"
        params = {"since_date": since_date}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        transactions = response.json()["data"]["transactions"]

        # Filtrar solo las sin categorizar y que no sean transferencias internas
        uncategorized = [
            t for t in transactions
            if t.get("category_id") is None
            and not t.get("deleted")
            and not (t.get("transfer_account_id") is not None)  # Excluir transferencias
        ]

        return uncategorized

    def find_category_by_rules(self, payee_name: str) -> Optional[str]:
        """Busca categoría usando las reglas definidas"""
        if not payee_name:
            return None

        payee_lower = payee_name.lower()

        for category_name, keywords in self.categorization_rules.items():
            for keyword in keywords:
                if keyword.lower() in payee_lower:
                    return category_name

        return None

    def suggest_category_with_ai(self, payee_name: str, amount: float, available_categories: List[str]) -> Optional[str]:
        """Sugiere una categoría usando lógica heurística (simula IA)"""
        if not payee_name:
            return None

        payee_lower = payee_name.lower()

        # Heurísticas basadas en patrones comunes
        patterns = {
            "Supermercado": ["super", "market", "alimentacion", "comida", "grocery"],
            "Restaurantes y bares": ["rest", "cafe", "bar", "food", "eat", "cocina", "gastro"],
            "Gasolina": ["fuel", "gas", "petrol", "gasoil", "carburante"],
            "Suscripciones": ["subscription", "suscripcion", "monthly", "premium", "plus"],
            "Salud y belleza": ["health", "salud", "medic", "doctor", "clinic", "dent", "optic"],
            "Ropa": ["fashion", "moda", "clothes", "wear", "shoes", "zapato", "textile"],
            "Transporte Público": ["transport", "viaje", "travel", "ticket", "billete"],
            "Educación y cultura": ["book", "libro", "curso", "academy", "school", "university", "educa"],
            "Espectáculos y actividades": ["cinema", "cine", "teatro", "concert", "event", "entrada", "ticket"],
            "Hogar": ["home", "casa", "hogar", "furniture", "mueble", "ikea", "leroy"],
        }

        for category, keywords in patterns.items():
            if category in available_categories:
                for keyword in keywords:
                    if keyword in payee_lower:
                        return category

        # Si es un gasto pequeño recurrente, podría ser suscripción
        if -50 < amount < 0 and any(word in payee_lower for word in ["app", "cloud", "online", "digital"]):
            if "Suscripciones" in available_categories:
                return "Suscripciones"

        return None

    def add_rule(self, category: str, keyword: str):
        """Añade una nueva regla de categorización"""
        keyword = keyword.lower().strip()

        if category not in self.categorization_rules:
            self.categorization_rules[category] = []

        if keyword not in self.categorization_rules[category]:
            self.categorization_rules[category].append(keyword)
            self._save_rules()

    def update_transaction_category(self, transaction_id: str, category_id: str) -> bool:
        """Actualiza la categoría de una transacción"""
        url = f"{self.base_url}/budgets/{self.budget_id}/transactions/{transaction_id}"

        data = {
            "transaction": {
                "category_id": category_id
            }
        }

        response = requests.patch(url, headers=self.headers, json=data)
        return response.status_code == 200

    def interactive_categorize(self) -> Dict:
        """Categorización interactiva con confirmación para cada transacción"""
        print("\n🔍 Obteniendo datos de YNAB...")
        categories = self.get_categories()
        category_list = sorted(categories.keys())

        print("📥 Buscando transacciones sin categorizar...")
        uncategorized = self.get_uncategorized_transactions()

        if not uncategorized:
            print("\n✅ ¡No hay transacciones sin categorizar!")
            return {"total": 0, "categorized": 0, "skipped": 0}

        stats = {"total": len(uncategorized), "categorized": 0, "skipped": 0}

        print(f"\n📊 Encontradas {len(uncategorized)} transacciones sin categorizar\n")
        print("="*70)
        print("Opciones: [Enter]=Aceptar | [n]=Otra categoría | [s]=Saltar | [q]=Salir")
        print("="*70 + "\n")

        for i, transaction in enumerate(uncategorized, 1):
            payee_name = transaction.get("payee_name", "Sin nombre")
            amount = transaction["amount"] / 1000
            date = transaction["date"]

            print(f"\n[{i}/{len(uncategorized)}] {date} | {payee_name}")
            print(f"         Importe: €{amount:,.2f}")

            # Buscar categoría por reglas
            suggested_category = self.find_category_by_rules(payee_name)
            suggestion_source = "reglas"

            # Si no hay regla, intentar sugerir con IA
            if not suggested_category:
                suggested_category = self.suggest_category_with_ai(payee_name, amount, category_list)
                suggestion_source = "IA"

            if suggested_category and suggested_category in categories:
                print(f"         💡 Sugerencia ({suggestion_source}): {suggested_category}")

                choice = input("         ¿Aceptar? [Enter/n/s/q]: ").strip().lower()

                if choice == 'q':
                    print("\n⏹️  Categorización interrumpida")
                    break
                elif choice == 's':
                    print("         ⏭️  Saltada")
                    stats["skipped"] += 1
                    continue
                elif choice == 'n' or choice != '':
                    # Mostrar lista de categorías
                    selected_category = self._select_category(category_list)
                    if selected_category:
                        suggested_category = selected_category
                    else:
                        stats["skipped"] += 1
                        continue

                # Aplicar categoría
                if self.update_transaction_category(transaction["id"], categories[suggested_category]):
                    print(f"         ✅ Categorizada como: {suggested_category}")
                    stats["categorized"] += 1

                    # Si era sugerencia de IA, preguntar si guardar regla
                    if suggestion_source == "IA":
                        save_rule = input("         ¿Guardar regla para el futuro? [s/N]: ").strip().lower()
                        if save_rule == 's':
                            # Extraer palabra clave del payee
                            keyword = self._extract_keyword(payee_name)
                            if keyword:
                                self.add_rule(suggested_category, keyword)
                else:
                    print("         ❌ Error al actualizar")
            else:
                print("         ⚠️  Sin sugerencia automática")
                choice = input("         ¿Categorizar manualmente? [s/N/q]: ").strip().lower()

                if choice == 'q':
                    print("\n⏹️  Categorización interrumpida")
                    break
                elif choice == 's':
                    selected_category = self._select_category(category_list)
                    if selected_category:
                        if self.update_transaction_category(transaction["id"], categories[selected_category]):
                            print(f"         ✅ Categorizada como: {selected_category}")
                            stats["categorized"] += 1

                            # Preguntar si guardar regla
                            save_rule = input("         ¿Guardar regla para el futuro? [s/N]: ").strip().lower()
                            if save_rule == 's':
                                keyword = self._extract_keyword(payee_name)
                                if keyword:
                                    self.add_rule(selected_category, keyword)
                        else:
                            print("         ❌ Error al actualizar")
                    else:
                        stats["skipped"] += 1
                else:
                    stats["skipped"] += 1

        print("\n" + "="*70)
        print(f"📈 RESUMEN: {stats['categorized']} categorizadas, {stats['skipped']} saltadas")
        print("="*70)

        return stats

    def _select_category(self, category_list: List[str]) -> Optional[str]:
        """Permite seleccionar una categoría de la lista"""
        print("\n         Categorías disponibles:")

        # Mostrar en columnas
        for i, cat in enumerate(category_list, 1):
            print(f"         {i:2}. {cat}")

        try:
            choice = input("\n         Número de categoría (o Enter para cancelar): ").strip()
            if not choice:
                return None

            idx = int(choice) - 1
            if 0 <= idx < len(category_list):
                return category_list[idx]
        except ValueError:
            pass

        return None

    def _extract_keyword(self, payee_name: str) -> Optional[str]:
        """Extrae una palabra clave del nombre del comercio"""
        # Limpiar y extraer la palabra más significativa
        words = payee_name.lower().split()

        # Filtrar palabras comunes
        stop_words = {'de', 'la', 'el', 'los', 'las', 'del', 'al', 'en', 'por', 'para',
                      'con', 'sin', 'sobre', 'transfer', 'pago', 'compra', 'recibo',
                      's.l.', 's.a.', 'sl', 'sa', 'slu', 'nº', 'num', 'ref'}

        significant_words = [w for w in words if w not in stop_words and len(w) > 2]

        if significant_words:
            # Sugerir la primera palabra significativa
            suggested = significant_words[0]
            custom = input(f"         Palabra clave [{suggested}]: ").strip()
            return custom if custom else suggested

        return input("         Introduce palabra clave: ").strip() or None

    def get_report_data(self, weeks_back: int = 1) -> Dict:
        """Genera datos del reporte para un período"""
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks_back)

        url = f"{self.base_url}/budgets/{self.budget_id}/transactions"
        params = {"since_date": start_date.strftime("%Y-%m-%d")}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        transactions = response.json()["data"]["transactions"]
        categories = self.get_categories()
        category_names = {cid: name for name, cid in categories.items()}

        expenses_by_category = defaultdict(float)
        income_by_category = defaultdict(float)
        total_expenses = 0
        total_income = 0

        for t in transactions:
            if t.get("deleted") or t.get("transfer_account_id"):
                continue

            amount = t["amount"] / 1000
            category_id = t.get("category_id")
            category_name = category_names.get(category_id, "Sin categoría")

            if amount < 0:
                expenses_by_category[category_name] += abs(amount)
                total_expenses += abs(amount)
            else:
                income_by_category[category_name] += amount
                total_income += amount

        return {
            "period": f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net": total_income - total_expenses,
            "expenses_by_category": dict(sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True)),
            "income_by_category": dict(sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)),
            "transaction_count": len([t for t in transactions if not t.get("deleted") and not t.get("transfer_account_id")])
        }

    def print_report(self, title: str, report: Dict, monthly_budget: Dict = None):
        """Imprime un reporte formateado"""
        print(f"\n{'='*80}")
        print(f"📊 {title}")
        print(f"   Período: {report['period']}")
        print(f"{'='*80}")

        print(f"\n💰 RESUMEN:")
        print(f"   Ingresos:  €{report['total_income']:>10,.2f}")
        print(f"   Gastos:    €{report['total_expenses']:>10,.2f}")
        print(f"   {'─'*30}")
        balance_symbol = "✅" if report['net'] >= 0 else "⚠️"
        print(f"   {balance_symbol} Balance:  €{report['net']:>10,.2f}")

        if report['expenses_by_category']:
            print(f"\n📉 GASTOS POR CATEGORÍA:")
            if monthly_budget:
                print(f"   {'Categoría':<32} {'Presup.':>10} {'Gastado':>10} {'Disponible':>11} {'Estado'}")
                print(f"   {'-'*78}")
            else:
                print(f"   {'Categoría':<40} {'Gastado':>12} {'%':>8}")
                print(f"   {'-'*65}")

            for category, activity in report['expenses_by_category'].items():
                if monthly_budget and category in monthly_budget:
                    budget_info = monthly_budget[category]
                    budgeted = budget_info['budgeted']
                    balance = budget_info['balance']

                    if budgeted == 0:
                        status = "⚪"
                    elif balance < 0:
                        status = "🔴 Excedido"
                    elif balance < budgeted * 0.2:
                        status = "🟡 Bajo"
                    else:
                        status = "🟢 OK"

                    print(f"   {category:<32} €{budgeted:>8,.2f} €{activity:>8,.2f} €{balance:>9,.2f} {status}")
                else:
                    pct = (activity / report['total_expenses'] * 100) if report['total_expenses'] > 0 else 0
                    bar = "█" * min(int(pct / 5), 10)
                    print(f"   {category:<40} €{activity:>10,.2f} {pct:>6.1f}% {bar}")

        if report['income_by_category']:
            print(f"\n💵 INGRESOS POR CATEGORÍA:")
            for category, amount in report['income_by_category'].items():
                if category != "Sin categoría":
                    print(f"   {category:<40} €{amount:>10,.2f}")

        print(f"\n📝 Transacciones: {report['transaction_count']}")

    def show_full_report(self):
        """Muestra reporte completo: semanal y mensual"""
        print("\n🔍 Generando reportes...")

        # Obtener presupuesto mensual
        try:
            monthly_budget = self.get_monthly_budget()
        except:
            monthly_budget = {}

        # Reporte semanal
        weekly_report = self.get_report_data(weeks_back=1)
        self.print_report("REPORTE SEMANAL", weekly_report)

        # Reporte mensual
        monthly_report = self.get_report_data(weeks_back=4)
        self.print_report("REPORTE MENSUAL (Presupuesto vs Actividad)", monthly_report, monthly_budget)

        print("\n" + "="*80 + "\n")


def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="🏦 YNAB Auto-Categorizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modos de ejecución:
  categorize    Categorización interactiva de transacciones
  report        Mostrar reportes semanal y mensual

Ejemplos:
  python3 ynab_auto_categorizer.py categorize
  python3 ynab_auto_categorizer.py report
        """
    )

    parser.add_argument(
        'mode',
        nargs='?',
        choices=['categorize', 'report'],
        help='Modo de ejecución'
    )

    args = parser.parse_args()

    # Configuración
    API_TOKEN = os.getenv("YNAB_API_TOKEN", "")
    BUDGET_ID = os.getenv("YNAB_BUDGET_ID", "last-used")

    if not API_TOKEN or API_TOKEN == "TU_TOKEN_AQUI":
        print("⚠️  Por favor configura tu YNAB_API_TOKEN")
        print("   Puedes obtenerlo en: https://app.ynab.com/settings/developer")
        sys.exit(1)

    categorizer = YNABAutoCategorizer(API_TOKEN, BUDGET_ID)

    # Si no se especifica modo, mostrar menú
    if not args.mode:
        print("\n🏦 YNAB Auto-Categorizer")
        print("="*40)
        print("1. Categorizar transacciones")
        print("2. Ver reportes")
        print("="*40)

        choice = input("\nElige una opción (1-2): ").strip()

        if choice == "1":
            args.mode = "categorize"
        elif choice == "2":
            args.mode = "report"
        else:
            print("Opción no válida")
            sys.exit(1)

    # Ejecutar modo seleccionado
    if args.mode == "categorize":
        categorizer.interactive_categorize()
        # Mostrar reporte al finalizar
        print("\n" + "="*80)
        print("📊 REPORTE POST-CATEGORIZACIÓN")
        categorizer.show_full_report()

    elif args.mode == "report":
        categorizer.show_full_report()


if __name__ == "__main__":
    main()
