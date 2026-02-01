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
import webbrowser
from collections import defaultdict
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

    def get_report_data(self, period: str = "month") -> Dict:
        """Genera datos del reporte para un período

        Args:
            period: "week" para semana actual (lunes a hoy), "month" para mes actual
        """
        today = datetime.now()

        if period == "week":
            # Semana actual: desde el lunes hasta hoy
            days_since_monday = today.weekday()  # 0 = lunes
            start_date = today - timedelta(days=days_since_monday)
            end_date = today
        else:  # month
            # Mes actual: desde el día 1 hasta hoy
            start_date = today.replace(day=1)
            end_date = today

        url = f"{self.base_url}/budgets/{self.budget_id}/transactions"
        params = {"since_date": start_date.strftime("%Y-%m-%d")}

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        all_transactions = response.json()["data"]["transactions"]
        categories = self.get_categories()
        category_names = {cid: name for name, cid in categories.items()}

        # Filtrar transacciones dentro del rango exacto
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        transactions = [
            t for t in all_transactions
            if start_str <= t["date"] <= end_str
        ]

        expenses_by_category = defaultdict(float)
        income_by_category = defaultdict(float)
        transactions_by_category = defaultdict(list)
        total_expenses = 0
        total_income = 0

        for t in transactions:
            if t.get("deleted") or t.get("transfer_account_id"):
                continue

            amount = t["amount"] / 1000
            category_id = t.get("category_id")
            category_name = category_names.get(category_id, "Sin categoría")

            # Guardar detalle de transacción
            tx_detail = {
                "date": t["date"],
                "payee": t.get("payee_name", "Sin nombre"),
                "memo": t.get("memo", ""),
                "amount": amount,
                "account": t.get("account_name", "")
            }

            # Guardar todas las transacciones por categoría
            transactions_by_category[category_name].append(tx_detail)

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
            "transactions_by_category": dict(transactions_by_category),
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
        """Genera y abre reporte HTML completo"""
        print("\n🔍 Generando reportes...")

        # Obtener datos
        try:
            monthly_budget = self.get_monthly_budget()
        except:
            monthly_budget = {}

        weekly_report = self.get_report_data(period="week")
        monthly_report = self.get_report_data(period="month")

        # Generar HTML
        html_file = self.generate_html_report(weekly_report, monthly_report, monthly_budget)

        print(f"✅ Reporte generado: {html_file}")
        print("🌐 Abriendo en navegador...")

        # Abrir en navegador
        webbrowser.open(f"file://{html_file}")

    def send_email_report(self, to_email: str = None):
        """Genera y envía el reporte por email"""
        print("\n📧 Preparando envío de reporte por email...")

        # Configuración de email
        smtp_user = os.getenv("GMAIL_USER")
        smtp_pass = os.getenv("GMAIL_APP_PASSWORD")
        recipient = to_email or os.getenv("REPORT_EMAIL", smtp_user)

        if not smtp_user or not smtp_pass:
            print("❌ Error: Configura GMAIL_USER y GMAIL_APP_PASSWORD en .env")
            print("   Para crear una contraseña de aplicación:")
            print("   1. Ve a https://myaccount.google.com/apppasswords")
            print("   2. Crea una contraseña para 'Correo' en 'Mac'")
            return False

        # Generar datos
        try:
            monthly_budget = self.get_monthly_budget()
        except:
            monthly_budget = {}

        weekly_report = self.get_report_data(period="week")
        monthly_report = self.get_report_data(period="month")

        # Generar HTML inline (sin Chart.js para compatibilidad con email)
        html_content = self._generate_email_html(weekly_report, monthly_report, monthly_budget)

        # Crear mensaje
        msg = MIMEMultipart('alternative')
        now = datetime.now()
        msg['Subject'] = f"📊 YNAB Report - Semana {now.strftime('%d/%m/%Y')}"
        msg['From'] = smtp_user
        msg['To'] = recipient

        # Versión texto plano
        text_content = self._generate_text_report(weekly_report, monthly_report)
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))

        # Versión HTML
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        # Enviar
        try:
            print(f"📤 Enviando a {recipient}...")
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            print(f"✅ Reporte enviado correctamente a {recipient}")
            return True
        except Exception as e:
            print(f"❌ Error al enviar: {e}")
            return False

    def _generate_text_report(self, weekly: Dict, monthly: Dict) -> str:
        """Genera versión texto plano del reporte"""
        lines = [
            "═" * 50,
            "📊 YNAB FINANCIAL REPORT",
            "═" * 50,
            "",
            f"📅 RESUMEN SEMANAL ({weekly['period']})",
            f"   Ingresos:  €{weekly['total_income']:,.2f}",
            f"   Gastos:    €{weekly['total_expenses']:,.2f}",
            f"   Balance:   €{weekly['net']:,.2f}",
            "",
            f"📅 RESUMEN MENSUAL ({monthly['period']})",
            f"   Ingresos:  €{monthly['total_income']:,.2f}",
            f"   Gastos:    €{monthly['total_expenses']:,.2f}",
            f"   Balance:   €{monthly['net']:,.2f}",
            "",
            "📉 TOP GASTOS DEL MES:",
        ]

        for cat, amt in list(monthly['expenses_by_category'].items())[:10]:
            pct = (amt / monthly['total_expenses'] * 100) if monthly['total_expenses'] > 0 else 0
            lines.append(f"   {cat:<30} €{amt:>10,.2f} ({pct:.1f}%)")

        lines.extend(["", "─" * 50, "Generado por YNAB Auto-Categorizer"])
        return "\n".join(lines)

    def _generate_email_html(self, weekly: Dict, monthly: Dict, budget: Dict) -> str:
        """Genera HTML optimizado para email con estilo oscuro igual al reporte"""
        now = datetime.now()
        colors = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899',
                  '#f43f5e', '#f97316', '#eab308', '#84cc16', '#22c55e']

        # Generar barras de gastos semanales
        weekly_bars = ""
        max_weekly = max(weekly['expenses_by_category'].values()) if weekly['expenses_by_category'] else 1
        for i, (cat, amt) in enumerate(list(weekly['expenses_by_category'].items())[:10]):
            pct = (amt / max_weekly * 100) if max_weekly > 0 else 0
            color = colors[i % len(colors)]
            weekly_bars += f'''
            <tr>
                <td style="padding: 8px 12px; color: #ccc; font-size: 13px; white-space: nowrap;">{cat}</td>
                <td style="padding: 8px 12px; width: 60%;">
                    <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 20px; overflow: hidden;">
                        <div style="background: {color}; height: 100%; width: {pct:.0f}%; border-radius: 4px;"></div>
                    </div>
                </td>
                <td style="padding: 8px 12px; color: #888; font-size: 13px; text-align: right; font-family: monospace;">€{amt:,.2f}</td>
            </tr>'''

        # Generar barras de gastos mensuales
        monthly_bars = ""
        max_monthly = max(monthly['expenses_by_category'].values()) if monthly['expenses_by_category'] else 1
        for i, (cat, amt) in enumerate(list(monthly['expenses_by_category'].items())[:15]):
            pct = (amt / max_monthly * 100) if max_monthly > 0 else 0
            color = colors[i % len(colors)]
            monthly_bars += f'''
            <tr>
                <td style="padding: 6px 12px; color: #ccc; font-size: 12px; white-space: nowrap;">{cat}</td>
                <td style="padding: 6px 12px; width: 60%;">
                    <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 18px; overflow: hidden;">
                        <div style="background: {color}; height: 100%; width: {pct:.0f}%; border-radius: 4px;"></div>
                    </div>
                </td>
                <td style="padding: 6px 12px; color: #888; font-size: 12px; text-align: right; font-family: monospace;">€{amt:,.2f}</td>
            </tr>'''

        # Generar filas de ingresos
        income_rows = ""
        for cat, amt in monthly['income_by_category'].items():
            if cat != "Sin categoría":
                income_rows += f'''
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #eee;">{cat}</td>
                    <td style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #4ade80; text-align: right; font-family: monospace;">€{amt:,.2f}</td>
                </tr>'''

        # Generar filas de top gastos
        expense_rows = ""
        for cat, amt in list(monthly['expenses_by_category'].items())[:10]:
            pct = (amt / monthly['total_expenses'] * 100) if monthly['total_expenses'] > 0 else 0
            expense_rows += f'''
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #eee;">{cat}</td>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #f87171; text-align: right; font-family: monospace;">€{amt:,.2f}</td>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #888; text-align: right;">{pct:.1f}%</td>
            </tr>'''

        # Generar filas de presupuesto con barra de progreso
        budget_rows = ""
        budget_data = []
        for cat, b in budget.items():
            if (b['activity'] != 0 or b['budgeted'] > 0) and cat not in ["Inflow: Ready to Assign", "Sin categoría"]:
                budget_data.append((cat, b))
        budget_data.sort(key=lambda x: x[1]['activity'])

        for cat, b in budget_data:
            activity = b['activity']
            budgeted = b['budgeted']
            pct = (abs(activity) / budgeted * 100) if budgeted > 0 else 100

            if b['balance'] < 0:
                status_color = "#f87171"
                status_bg = "rgba(248, 113, 113, 0.2)"
                status_text = "Excedido"
                bar_color = "#f87171"
            elif budgeted > 0 and b['balance'] < budgeted * 0.2:
                status_color = "#fbbf24"
                status_bg = "rgba(251, 191, 36, 0.2)"
                status_text = "Bajo"
                bar_color = "#fbbf24"
            else:
                status_color = "#4ade80"
                status_bg = "rgba(74, 222, 128, 0.2)"
                status_text = "OK"
                bar_color = "#4ade80"

            activity_color = "#f87171" if activity < 0 else "#4ade80"
            activity_str = f"−€{abs(activity):,.2f}" if activity < 0 else f"€{activity:,.2f}"
            available_color = "#f87171" if b['balance'] < 0 else "#eee"

            budget_rows += f'''
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #eee;">{cat}</td>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); color: #eee; text-align: right; font-family: monospace;">€{budgeted:,.2f}</td>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); color: {activity_color}; text-align: right; font-family: monospace;">{activity_str}</td>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); color: {available_color}; text-align: right; font-family: monospace;">€{b['balance']:,.2f}</td>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1);">
                    <span style="background: {status_bg}; color: {status_color}; padding: 4px 10px; border-radius: 20px; font-size: 12px;">{status_text}</span>
                </td>
                <td style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.1); width: 100px;">
                    <div style="background: rgba(255,255,255,0.1); border-radius: 3px; height: 6px; overflow: hidden;">
                        <div style="background: {bar_color}; height: 100%; width: {min(pct, 100):.0f}%; border-radius: 3px;"></div>
                    </div>
                </td>
            </tr>'''

        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 20px; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table cellpadding="0" cellspacing="0" width="100%" style="max-width: 900px; margin: 0 auto;">
        <!-- Header -->
        <tr>
            <td style="text-align: center; padding: 30px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">
                <h1 style="color: #eee; margin: 0; font-size: 2em;">📊 YNAB Financial Report</h1>
                <p style="color: #888; margin: 10px 0 0 0; font-size: 1.1em;">{now.strftime('%d de %B de %Y')}</p>
            </td>
        </tr>

        <!-- Summary Cards -->
        <tr>
            <td style="padding: 30px 0;">
                <table cellpadding="0" cellspacing="15" width="100%">
                    <tr>
                        <td style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); text-align: center; width: 25%;">
                            <p style="color: #888; margin: 0 0 10px 0; font-size: 0.9em; text-transform: uppercase;">💰 Ingresos (Mes)</p>
                            <p style="color: #4ade80; margin: 0; font-size: 1.8em; font-weight: bold;">€{monthly['total_income']:,.2f}</p>
                        </td>
                        <td style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); text-align: center; width: 25%;">
                            <p style="color: #888; margin: 0 0 10px 0; font-size: 0.9em; text-transform: uppercase;">💸 Gastos (Mes)</p>
                            <p style="color: #f87171; margin: 0; font-size: 1.8em; font-weight: bold;">€{monthly['total_expenses']:,.2f}</p>
                        </td>
                        <td style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); text-align: center; width: 25%;">
                            <p style="color: #888; margin: 0 0 10px 0; font-size: 0.9em; text-transform: uppercase;">{'✅' if monthly['net'] >= 0 else '⚠️'} Balance (Mes)</p>
                            <p style="color: {'#4ade80' if monthly['net'] >= 0 else '#f87171'}; margin: 0; font-size: 1.8em; font-weight: bold;">€{monthly['net']:,.2f}</p>
                        </td>
                        <td style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); text-align: center; width: 25%;">
                            <p style="color: #888; margin: 0 0 10px 0; font-size: 0.9em; text-transform: uppercase;">📝 Transacciones</p>
                            <p style="color: #eee; margin: 0; font-size: 1.8em; font-weight: bold;">{monthly['transaction_count']}</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>

        <!-- Charts Row -->
        <tr>
            <td>
                <table cellpadding="0" cellspacing="15" width="100%">
                    <tr>
                        <!-- Weekly Chart -->
                        <td style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); width: 50%; vertical-align: top;">
                            <h2 style="color: #eee; margin: 0 0 5px 0; font-size: 1.2em;">📈 Gastos Semanales</h2>
                            <p style="color: #888; margin: 0 0 15px 0; font-size: 0.9em;">{weekly['period']} • €{weekly['total_expenses']:,.2f} total</p>
                            <table cellpadding="0" cellspacing="0" width="100%">
                                {weekly_bars}
                            </table>
                        </td>
                        <!-- Monthly Chart -->
                        <td style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); width: 50%; vertical-align: top;">
                            <h2 style="color: #eee; margin: 0 0 5px 0; font-size: 1.2em;">📊 Gastos Mensuales</h2>
                            <p style="color: #888; margin: 0 0 15px 0; font-size: 0.9em;">{monthly['period']} • €{monthly['total_expenses']:,.2f} total</p>
                            <table cellpadding="0" cellspacing="0" width="100%">
                                {monthly_bars}
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>

        <!-- Income & Expenses Tables -->
        <tr>
            <td style="padding-top: 15px;">
                <table cellpadding="0" cellspacing="15" width="100%">
                    <tr>
                        <!-- Income -->
                        <td style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); width: 50%; vertical-align: top;">
                            <h2 style="color: #eee; margin: 0 0 20px 0; font-size: 1.2em;">💵 Ingresos por Categoría</h2>
                            <table cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <th style="padding: 12px; text-align: left; color: #888; font-size: 0.85em; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1);">Categoría</th>
                                    <th style="padding: 12px; text-align: right; color: #888; font-size: 0.85em; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1);">Importe</th>
                                </tr>
                                {income_rows}
                            </table>
                        </td>
                        <!-- Top Expenses -->
                        <td style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); width: 50%; vertical-align: top;">
                            <h2 style="color: #eee; margin: 0 0 20px 0; font-size: 1.2em;">📉 Top Gastos del Mes</h2>
                            <table cellpadding="0" cellspacing="0" width="100%">
                                <tr>
                                    <th style="padding: 12px; text-align: left; color: #888; font-size: 0.85em; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1);">Categoría</th>
                                    <th style="padding: 12px; text-align: right; color: #888; font-size: 0.85em; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1);">Importe</th>
                                    <th style="padding: 12px; text-align: right; color: #888; font-size: 0.85em; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1);">%</th>
                                </tr>
                                {expense_rows}
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>

        <!-- Budget vs Activity -->
        <tr>
            <td style="padding-top: 15px;">
                <div style="background: rgba(255,255,255,0.05); padding: 25px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1);">
                    <h2 style="color: #eee; margin: 0 0 20px 0; font-size: 1.2em;">💳 Presupuesto vs Actividad</h2>
                    <table cellpadding="0" cellspacing="0" width="100%">
                        <tr>
                            <th style="padding: 12px; text-align: left; color: #888; font-size: 0.85em; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1);">Categoría</th>
                            <th style="padding: 12px; text-align: right; color: #888; font-size: 0.85em; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1);">Asignado</th>
                            <th style="padding: 12px; text-align: right; color: #888; font-size: 0.85em; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1);">Actividad</th>
                            <th style="padding: 12px; text-align: right; color: #888; font-size: 0.85em; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1);">Disponible</th>
                            <th style="padding: 12px; text-align: left; color: #888; font-size: 0.85em; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1);">Estado</th>
                            <th style="padding: 12px; text-align: left; color: #888; font-size: 0.85em; text-transform: uppercase; border-bottom: 1px solid rgba(255,255,255,0.1); width: 100px;">Progreso</th>
                        </tr>
                        {budget_rows}
                    </table>
                </div>
            </td>
        </tr>

        <!-- Footer -->
        <tr>
            <td style="text-align: center; padding: 30px 0; color: #666; font-size: 0.9em;">
                <p style="margin: 0;">YNAB Auto-Categorizer • Reporte generado automáticamente</p>
            </td>
        </tr>
    </table>
</body>
</html>'''

    def generate_html_report(self, weekly: Dict, monthly: Dict, budget: Dict) -> str:
        """Genera reporte HTML con gráficos"""
        now = datetime.now()
        report_file = Path(__file__).parent / f"reporte_ynab_{now.strftime('%Y%m%d_%H%M')}.html"

        # Preparar datos para gráficos
        weekly_categories = list(weekly['expenses_by_category'].keys())[:10]
        weekly_amounts = [weekly['expenses_by_category'][c] for c in weekly_categories]

        monthly_categories = list(monthly['expenses_by_category'].keys())[:15]
        monthly_amounts = [monthly['expenses_by_category'][c] for c in monthly_categories]

        # Preparar transacciones para el modal (combinar weekly y monthly)
        all_transactions = {}
        for cat, txs in weekly.get('transactions_by_category', {}).items():
            all_transactions[cat] = txs
        for cat, txs in monthly.get('transactions_by_category', {}).items():
            if cat not in all_transactions:
                all_transactions[cat] = txs
            else:
                # Combinar sin duplicados (por fecha y monto)
                existing = {(t['date'], t['amount']) for t in all_transactions[cat]}
                for tx in txs:
                    if (tx['date'], tx['amount']) not in existing:
                        all_transactions[cat].append(tx)

        # Ordenar transacciones por fecha
        for cat in all_transactions:
            all_transactions[cat].sort(key=lambda x: x['date'], reverse=True)

        # Datos de presupuesto vs actividad (usar datos directos del presupuesto)
        budget_data = []
        for cat, b in budget.items():
            # Solo incluir categorías con actividad o presupuesto
            if (b['activity'] != 0 or b['budgeted'] > 0) and cat not in ["Inflow: Ready to Assign", "Sin categoría"]:
                budget_data.append({
                    "category": cat,
                    "budgeted": b['budgeted'],
                    "activity": b['activity'],  # Mantener el signo original
                    "available": b['balance'],
                    "status": "over" if b['balance'] < 0 else ("low" if b['budgeted'] > 0 and b['balance'] < b['budgeted'] * 0.2 else "ok")
                })
        # Ordenar por actividad (más gasto primero, valores más negativos)
        budget_data.sort(key=lambda x: x['activity'])

        html = f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YNAB Report - {now.strftime('%d/%m/%Y')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }}
        header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        header p {{ color: #888; font-size: 1.1em; }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .card h3 {{ color: #888; font-size: 0.9em; text-transform: uppercase; margin-bottom: 10px; }}
        .card .value {{ font-size: 2em; font-weight: bold; }}
        .card .value.positive {{ color: #4ade80; }}
        .card .value.negative {{ color: #f87171; }}
        .card .period {{ color: #666; font-size: 0.85em; margin-top: 5px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 30px; margin-bottom: 30px; }}
        .section {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .section h2 {{ margin-bottom: 20px; font-size: 1.3em; display: flex; align-items: center; gap: 10px; }}
        .chart-container {{ position: relative; height: 300px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }}
        th {{ color: #888; font-weight: 500; font-size: 0.85em; text-transform: uppercase; }}
        .status {{ padding: 4px 10px; border-radius: 20px; font-size: 0.8em; font-weight: 500; }}
        .status.ok {{ background: rgba(74, 222, 128, 0.2); color: #4ade80; }}
        .status.low {{ background: rgba(251, 191, 36, 0.2); color: #fbbf24; }}
        .status.over {{ background: rgba(248, 113, 113, 0.2); color: #f87171; }}
        .amount {{ font-family: 'SF Mono', Monaco, monospace; }}
        .amount.negative {{ color: #f87171; }}
        .amount.positive {{ color: #4ade80; }}
        .progress-bar {{
            height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 5px;
        }}
        .progress-fill {{
            height: 100%;
            border-radius: 3px;
            transition: width 0.3s ease;
        }}
        .progress-fill.ok {{ background: #4ade80; }}
        .progress-fill.low {{ background: #fbbf24; }}
        .progress-fill.over {{ background: #f87171; }}
        footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.9em;
        }}
        /* Modal styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(5px);
        }}
        .modal-content {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            margin: 5% auto;
            padding: 30px;
            border-radius: 15px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            border: 1px solid rgba(255,255,255,0.1);
            animation: modalSlide 0.3s ease;
        }}
        @keyframes modalSlide {{
            from {{ transform: translateY(-50px); opacity: 0; }}
            to {{ transform: translateY(0); opacity: 1; }}
        }}
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .modal-header h2 {{ font-size: 1.5em; }}
        .modal-close {{
            background: none;
            border: none;
            color: #888;
            font-size: 2em;
            cursor: pointer;
            transition: color 0.2s;
        }}
        .modal-close:hover {{ color: #fff; }}
        .modal-total {{
            font-size: 1.2em;
            color: #888;
            margin-bottom: 20px;
        }}
        .modal-total span {{ color: #f87171; font-weight: bold; }}
        .tx-table {{ width: 100%; }}
        .tx-table th {{ text-align: left; padding: 10px; color: #888; font-size: 0.85em; }}
        .tx-table td {{ padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .tx-table tr:hover {{ background: rgba(255,255,255,0.05); }}
        .clickable-row {{ cursor: pointer; transition: background 0.2s; }}
        .clickable-row:hover {{ background: rgba(255,255,255,0.08); }}
        .hint {{ text-align: center; color: #666; font-size: 0.85em; margin-top: 15px; }}
        @media (max-width: 768px) {{
            .grid {{ grid-template-columns: 1fr; }}
            header h1 {{ font-size: 1.8em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 YNAB Financial Report</h1>
            <p>Generado el {now.strftime('%d de %B de %Y a las %H:%M')}</p>
        </header>

        <div class="summary-cards">
            <div class="card">
                <h3>💰 Ingresos (Mes)</h3>
                <div class="value positive">€{monthly['total_income']:,.2f}</div>
                <div class="period">{monthly['period']}</div>
            </div>
            <div class="card">
                <h3>💸 Gastos (Mes)</h3>
                <div class="value negative">€{monthly['total_expenses']:,.2f}</div>
                <div class="period">{monthly['period']}</div>
            </div>
            <div class="card">
                <h3>{'✅' if monthly['net'] >= 0 else '⚠️'} Balance (Mes)</h3>
                <div class="value {'positive' if monthly['net'] >= 0 else 'negative'}">€{monthly['net']:,.2f}</div>
                <div class="period">{monthly['period']}</div>
            </div>
            <div class="card">
                <h3>📝 Transacciones</h3>
                <div class="value">{monthly['transaction_count']}</div>
                <div class="period">Este mes</div>
            </div>
        </div>

        <div class="grid">
            <div class="section">
                <h2>📈 Gastos Semanales</h2>
                <p style="color:#888; margin-bottom:15px;">{weekly['period']} • €{weekly['total_expenses']:,.2f} total</p>
                <div class="chart-container">
                    <canvas id="weeklyChart"></canvas>
                </div>
            </div>
            <div class="section">
                <h2>📊 Gastos Mensuales</h2>
                <p style="color:#888; margin-bottom:15px;">{monthly['period']} • €{monthly['total_expenses']:,.2f} total</p>
                <div class="chart-container">
                    <canvas id="monthlyChart"></canvas>
                </div>
            </div>
        </div>

        <div class="grid">
            <div class="section">
                <h2>💵 Ingresos por Categoría</h2>
                <table>
                    <thead><tr><th>Categoría</th><th>Importe</th></tr></thead>
                    <tbody>
                        {''.join(self._generate_clickable_row(cat, f"€{amt:,.2f}") for cat, amt in monthly['income_by_category'].items() if cat != "Sin categoría")}
                    </tbody>
                </table>
            </div>
            <div class="section">
                <h2>📉 Top Gastos del Mes</h2>
                <table>
                    <thead><tr><th>Categoría</th><th>Importe</th><th>%</th></tr></thead>
                    <tbody>
                        {''.join(self._generate_clickable_row(cat, f"€{amt:,.2f}", f"{(amt/monthly['total_expenses']*100) if monthly['total_expenses'] > 0 else 0:.1f}%") for cat, amt in list(monthly['expenses_by_category'].items())[:10])}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section" style="margin-bottom: 30px;">
            <h2>💳 Presupuesto vs Actividad</h2>
            <table>
                <thead>
                    <tr>
                        <th>Categoría</th>
                        <th>Asignado</th>
                        <th>Actividad</th>
                        <th>Disponible</th>
                        <th>Estado</th>
                        <th style="width: 150px;">Progreso</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(self._generate_budget_row(item, all_transactions) for item in budget_data)}
                </tbody>
            </table>
        </div>

        <footer>
            <p>YNAB Auto-Categorizer • Reporte generado automáticamente</p>
            <p class="hint">💡 Clic en cualquier categoría para ver el detalle de transacciones</p>
        </footer>
    </div>

    <!-- Modal para detalle de transacciones -->
    <div id="txModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Transacciones</h2>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-total">Total: <span id="modalTotal">€0.00</span></div>
            <table class="tx-table">
                <thead>
                    <tr><th>Fecha</th><th>Comercio</th><th>Cuenta</th><th>Importe</th></tr>
                </thead>
                <tbody id="modalBody"></tbody>
            </table>
        </div>
    </div>

    <script>
        // Datos de transacciones por categoría
        const transactionsData = {json.dumps(all_transactions, ensure_ascii=False)};

        function showTransactions(category) {{
            const modal = document.getElementById('txModal');
            const title = document.getElementById('modalTitle');
            const body = document.getElementById('modalBody');
            const total = document.getElementById('modalTotal');

            const txs = transactionsData[category] || [];

            title.textContent = category;

            let totalAmount = 0;
            let html = '';

            txs.forEach(tx => {{
                totalAmount += tx.amount;
                const amountClass = tx.amount < 0 ? 'negative' : 'positive';
                const amountStr = tx.amount < 0
                    ? '−€' + Math.abs(tx.amount).toLocaleString('es-ES', {{minimumFractionDigits: 2}})
                    : '€' + tx.amount.toLocaleString('es-ES', {{minimumFractionDigits: 2}});
                html += `<tr>
                    <td>${{tx.date}}</td>
                    <td>${{tx.payee}}</td>
                    <td>${{tx.account || '-'}}</td>
                    <td class="amount ${{amountClass}}">${{amountStr}}</td>
                </tr>`;
            }});

            body.innerHTML = html || '<tr><td colspan="4" style="text-align:center;color:#888;">No hay transacciones</td></tr>';

            const totalStr = totalAmount < 0
                ? '−€' + Math.abs(totalAmount).toLocaleString('es-ES', {{minimumFractionDigits: 2}})
                : '€' + totalAmount.toLocaleString('es-ES', {{minimumFractionDigits: 2}});
            total.textContent = totalStr;

            modal.style.display = 'block';
        }}

        function closeModal() {{
            document.getElementById('txModal').style.display = 'none';
        }}

        // Cerrar modal al hacer clic fuera
        window.onclick = function(event) {{
            const modal = document.getElementById('txModal');
            if (event.target === modal) {{
                modal.style.display = 'none';
            }}
        }}

        // Cerrar con Escape
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') closeModal();
        }});

        const colors = [
            '#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899',
            '#f43f5e', '#f97316', '#eab308', '#84cc16', '#22c55e',
            '#14b8a6', '#06b6d4', '#0ea5e9', '#3b82f6', '#6366f1'
        ];

        const weeklyChart = new Chart(document.getElementById('weeklyChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(weekly_categories)},
                datasets: [{{
                    label: 'Gastos €',
                    data: {json.dumps(weekly_amounts)},
                    backgroundColor: colors.slice(0, {len(weekly_categories)}),
                    borderRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ grid: {{ color: 'rgba(255,255,255,0.1)' }}, ticks: {{ color: '#888' }} }},
                    y: {{ grid: {{ display: false }}, ticks: {{ color: '#888' }} }}
                }}
            }}
        }});

        const monthlyChart = new Chart(document.getElementById('monthlyChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(monthly_categories)},
                datasets: [{{
                    label: 'Gastos €',
                    data: {json.dumps(monthly_amounts)},
                    backgroundColor: colors.slice(0, {len(monthly_categories)}),
                    borderRadius: 5
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    x: {{ grid: {{ color: 'rgba(255,255,255,0.1)' }}, ticks: {{ color: '#888' }} }},
                    y: {{ grid: {{ display: false }}, ticks: {{ color: '#888' }} }}
                }}
            }}
        }});

        // Clic en gráfico semanal
        document.getElementById('weeklyChart').addEventListener('click', function(evt) {{
            const points = weeklyChart.getElementsAtEventForMode(evt, 'nearest', {{ intersect: true }}, true);
            if (points.length) {{
                const category = weeklyChart.data.labels[points[0].index];
                showTransactions(category);
            }}
        }});

        // Clic en gráfico mensual
        document.getElementById('monthlyChart').addEventListener('click', function(evt) {{
            const points = monthlyChart.getElementsAtEventForMode(evt, 'nearest', {{ intersect: true }}, true);
            if (points.length) {{
                const category = monthlyChart.data.labels[points[0].index];
                showTransactions(category);
            }}
        }});
    </script>
</body>
</html>'''

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)

        return str(report_file.absolute())

    def _generate_clickable_row(self, category: str, *columns) -> str:
        """Genera una fila clickable para las tablas"""
        cat_escaped = category.replace("'", "\\'")
        cols_html = ''.join(f'<td class="amount">{col}</td>' if col.startswith('€') or col.endswith('%') else f'<td>{col}</td>' for col in columns)
        return f'<tr class="clickable-row" onclick="showTransactions(\'{cat_escaped}\')" title="Clic para ver detalle"><td>{category}</td>{cols_html}</tr>'

    def _generate_budget_row(self, item: Dict, transactions: Dict) -> str:
        """Genera una fila de la tabla de presupuesto"""
        activity = item['activity']
        budgeted = item['budgeted']
        category = item['category']
        pct = (abs(activity) / budgeted * 100) if budgeted > 0 else 100
        status_text = {"ok": "OK", "low": "Bajo", "over": "Excedido"}[item['status']]

        # Formatear actividad (solo signo negativo)
        activity_class = "negative" if activity < 0 else "positive" if activity > 0 else ""
        if activity < 0:
            activity_str = f"−{abs(activity):,.2f}"  # Signo menos tipográfico
        else:
            activity_str = f"{activity:,.2f}"  # Sin signo para positivos

        # Escapar comillas en el nombre de categoría para JavaScript
        cat_escaped = category.replace("'", "\\'")
        has_transactions = category in transactions and len(transactions[category]) > 0
        clickable_class = "clickable-row" if has_transactions else ""
        onclick = f'onclick="showTransactions(\'{cat_escaped}\')"' if has_transactions else ""
        title = 'title="Clic para ver detalle"' if has_transactions else ""

        return f'''<tr class="{clickable_class}" {onclick} {title}>
            <td>{category}</td>
            <td class="amount">€{budgeted:,.2f}</td>
            <td class="amount {activity_class}">€{activity_str}</td>
            <td class="amount {'negative' if item['available'] < 0 else ''}">€{item['available']:,.2f}</td>
            <td><span class="status {item['status']}">{status_text}</span></td>
            <td>
                <div class="progress-bar">
                    <div class="progress-fill {item['status']}" style="width: {min(pct, 100):.0f}%"></div>
                </div>
            </td>
        </tr>'''


def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="🏦 YNAB Auto-Categorizer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modos de ejecución:
  categorize    Categorización interactiva de transacciones
  report        Mostrar reportes semanal y mensual
  email         Enviar reporte por correo electrónico

Ejemplos:
  python3 ynab_auto_categorizer.py categorize
  python3 ynab_auto_categorizer.py report
  python3 ynab_auto_categorizer.py email
        """
    )

    parser.add_argument(
        'mode',
        nargs='?',
        choices=['categorize', 'report', 'email'],
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
        print("3. Enviar reporte por email")
        print("="*40)

        choice = input("\nElige una opción (1-3): ").strip()

        if choice == "1":
            args.mode = "categorize"
        elif choice == "2":
            args.mode = "report"
        elif choice == "3":
            args.mode = "email"
        else:
            print("Opción no válida")
            sys.exit(1)

    # Ejecutar modo seleccionado
    if args.mode == "categorize":
        categorizer.interactive_categorize()

    elif args.mode == "report":
        categorizer.show_full_report()

    elif args.mode == "email":
        categorizer.send_email_report()


if __name__ == "__main__":
    main()
