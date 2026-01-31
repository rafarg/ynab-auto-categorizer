#!/usr/bin/env python3
"""
YNAB Auto-Categorizer and Weekly Reporter
Categoriza automáticamente transacciones y genera reportes semanales
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
from collections import defaultdict

class YNABAutoCategorizer:
    def __init__(self, api_token: str, budget_id: str = "last-used"):
        """
        Inicializa el categorizador de YNAB
        
        Args:
            api_token: Token de acceso personal de YNAB
            budget_id: ID del presupuesto (usa "last-used" para el último usado)
        """
        self.api_token = api_token
        self.budget_id = budget_id
        self.base_url = "https://api.ynab.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
        
        # Reglas de categorización (puedes personalizarlas)
        self.categorization_rules = {
            # Comida y supermercados
            "Comestibles": ["mercadona", "carrefour", "lidl", "aldi", "dia", "eroski", "alcampo"],
            "Restaurantes": ["restaurant", "mcdonald", "burger", "pizza", "kebab", "cafeteria"],
            
            # Transporte
            "Gasolina": ["shell", "repsol", "cepsa", "bp", "galp"],
            "Transporte Público": ["metro", "renfe", "uber", "cabify", "taxi", "bus"],
            
            # Entretenimiento
            "Entretenimiento": ["netflix", "spotify", "hbo", "disney", "prime video", "cinema", "cine"],
            
            # Servicios
            "Teléfono/Internet": ["vodafone", "movistar", "orange", "yoigo", "masmovil"],
            "Electricidad/Agua": ["iberdrola", "endesa", "naturgy", "aqualia"],
            
            # Compras
            "Ropa": ["zara", "h&m", "mango", "pull&bear", "bershka"],
            "Amazon": ["amazon"],
            
            # Salud
            "Farmacia": ["farmacia", "pharmacy"],
            "Gimnasio": ["gym", "gimnasio", "fitness"],
        }
    
    def get_categories(self) -> Dict[str, str]:
        """Obtiene todas las categorías del presupuesto"""
        url = f"{self.base_url}/budgets/{self.budget_id}/categories"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        categories = {}
        for group in response.json()["data"]["category_groups"]:
            for category in group["categories"]:
                categories[category["name"]] = category["id"]
        
        return categories
    
    def get_uncategorized_transactions(self, days_back: int = 30) -> List[Dict]:
        """
        Obtiene transacciones sin categorizar
        
        Args:
            days_back: Días hacia atrás para buscar transacciones
        """
        since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        url = f"{self.base_url}/budgets/{self.budget_id}/transactions"
        params = {"since_date": since_date}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        transactions = response.json()["data"]["transactions"]
        
        # Filtrar solo las sin categorizar (category_id es null)
        uncategorized = [t for t in transactions if t.get("category_id") is None and not t.get("deleted")]
        
        return uncategorized
    
    def categorize_transaction(self, payee_name: str, available_categories: Dict[str, str]) -> Optional[str]:
        """
        Categoriza una transacción basándose en el nombre del comercio
        
        Args:
            payee_name: Nombre del comercio/beneficiario
            available_categories: Diccionario de categorías disponibles {nombre: id}
            
        Returns:
            ID de la categoría sugerida o None
        """
        if not payee_name:
            return None
        
        payee_lower = payee_name.lower()
        
        # Buscar coincidencia en las reglas
        for category_name, keywords in self.categorization_rules.items():
            for keyword in keywords:
                if keyword in payee_lower:
                    # Verificar que la categoría existe en YNAB
                    if category_name in available_categories:
                        return available_categories[category_name]
        
        return None
    
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
    
    def auto_categorize(self, dry_run: bool = True) -> Dict:
        """
        Categoriza automáticamente las transacciones sin categoría
        
        Args:
            dry_run: Si es True, solo muestra lo que haría sin actualizar
            
        Returns:
            Diccionario con estadísticas de categorización
        """
        print("🔍 Obteniendo categorías disponibles...")
        categories = self.get_categories()
        
        print("📥 Buscando transacciones sin categorizar...")
        uncategorized = self.get_uncategorized_transactions()
        
        stats = {
            "total": len(uncategorized),
            "categorized": 0,
            "uncategorized": 0,
            "details": []
        }
        
        print(f"\n📊 Encontradas {len(uncategorized)} transacciones sin categorizar\n")
        
        for transaction in uncategorized:
            payee_name = transaction.get("payee_name", "")
            amount = transaction["amount"] / 1000  # YNAB usa miliunidades
            date = transaction["date"]
            
            category_id = self.categorize_transaction(payee_name, categories)
            
            if category_id:
                # Encontrar nombre de categoría
                category_name = next((name for name, cid in categories.items() if cid == category_id), "Unknown")
                
                if dry_run:
                    print(f"✓ {date} | {payee_name:30} | €{amount:8.2f} → {category_name}")
                else:
                    if self.update_transaction_category(transaction["id"], category_id):
                        print(f"✅ {date} | {payee_name:30} | €{amount:8.2f} → {category_name}")
                        stats["categorized"] += 1
                    else:
                        print(f"❌ Error actualizando: {payee_name}")
                
                stats["details"].append({
                    "payee": payee_name,
                    "amount": amount,
                    "category": category_name,
                    "date": date
                })
            else:
                print(f"⚠️  {date} | {payee_name:30} | €{amount:8.2f} → Sin regla")
                stats["uncategorized"] += 1
        
        if dry_run:
            print(f"\n🔔 MODO SIMULACIÓN: No se actualizaron transacciones")
            print(f"   Para aplicar cambios, ejecuta con dry_run=False")
        
        return stats
    
    def get_weekly_report(self, weeks_back: int = 1) -> Dict:
        """
        Genera un reporte semanal de gastos e ingresos
        
        Args:
            weeks_back: Número de semanas hacia atrás (1 = última semana)
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks_back)
        
        url = f"{self.base_url}/budgets/{self.budget_id}/transactions"
        params = {"since_date": start_date.strftime("%Y-%m-%d")}
        
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        transactions = response.json()["data"]["transactions"]
        
        # Obtener nombres de categorías
        categories = self.get_categories()
        category_names = {cid: name for name, cid in categories.items()}
        
        # Analizar transacciones
        expenses_by_category = defaultdict(float)
        income_by_category = defaultdict(float)
        total_expenses = 0
        total_income = 0
        
        for t in transactions:
            if t.get("deleted"):
                continue
                
            amount = t["amount"] / 1000  # Convertir de miliunidades
            category_id = t.get("category_id")
            category_name = category_names.get(category_id, "Sin categoría")
            
            if amount < 0:  # Gasto
                expenses_by_category[category_name] += abs(amount)
                total_expenses += abs(amount)
            else:  # Ingreso
                income_by_category[category_name] += amount
                total_income += amount
        
        return {
            "period": f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net": total_income - total_expenses,
            "expenses_by_category": dict(sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True)),
            "income_by_category": dict(income_by_category),
            "transaction_count": len([t for t in transactions if not t.get("deleted")])
        }
    
    def print_weekly_report(self, weeks_back: int = 1):
        """Imprime un reporte semanal formateado"""
        report = self.get_weekly_report(weeks_back)
        
        print("\n" + "="*60)
        print(f"📊 REPORTE SEMANAL - {report['period']}")
        print("="*60)
        
        print(f"\n💰 RESUMEN:")
        print(f"   Ingresos:  €{report['total_income']:>10,.2f}")
        print(f"   Gastos:    €{report['total_expenses']:>10,.2f}")
        print(f"   {'─'*30}")
        balance_symbol = "✅" if report['net'] >= 0 else "⚠️"
        print(f"   {balance_symbol} Balance:  €{report['net']:>10,.2f}")
        
        print(f"\n📉 GASTOS POR CATEGORÍA:")
        for category, amount in report['expenses_by_category'].items():
            percentage = (amount / report['total_expenses'] * 100) if report['total_expenses'] > 0 else 0
            bar = "█" * int(percentage / 5)
            print(f"   {category:25} €{amount:>8,.2f} ({percentage:5.1f}%) {bar}")
        
        if report['income_by_category']:
            print(f"\n💵 INGRESOS POR CATEGORÍA:")
            for category, amount in report['income_by_category'].items():
                print(f"   {category:25} €{amount:>8,.2f}")
        
        print(f"\n📝 Total de transacciones: {report['transaction_count']}")
        print("="*60 + "\n")


def main():
    """Función principal de ejemplo"""
    
    # CONFIGURACIÓN - Reemplaza con tus datos
    API_TOKEN = os.getenv("YNAB_API_TOKEN", "TU_TOKEN_AQUI")
    BUDGET_ID = os.getenv("YNAB_BUDGET_ID", "last-used")  # O el ID específico de tu presupuesto
    
    if API_TOKEN == "TU_TOKEN_AQUI":
        print("⚠️  Por favor configura tu YNAB_API_TOKEN")
        print("   Puedes obtenerlo en: https://app.ynab.com/settings/developer")
        print("   Configúralo como variable de entorno o edita este archivo")
        return
    
    # Crear instancia del categorizador
    categorizer = YNABAutoCategorizer(API_TOKEN, BUDGET_ID)
    
    # Menú simple
    print("\n🏦 YNAB Auto-Categorizer")
    print("1. Categorizar transacciones (modo simulación)")
    print("2. Categorizar transacciones (aplicar cambios)")
    print("3. Ver reporte semanal")
    print("4. Ver reporte del último mes")
    
    choice = input("\nElige una opción (1-4): ").strip()
    
    if choice == "1":
        categorizer.auto_categorize(dry_run=True)
    elif choice == "2":
        confirm = input("⚠️  Esto actualizará tus transacciones en YNAB. ¿Continuar? (s/n): ")
        if confirm.lower() == "s":
            categorizer.auto_categorize(dry_run=False)
    elif choice == "3":
        categorizer.print_weekly_report(weeks_back=1)
    elif choice == "4":
        categorizer.print_weekly_report(weeks_back=4)
    else:
        print("Opción no válida")


if __name__ == "__main__":
    main()
