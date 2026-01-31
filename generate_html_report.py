#!/usr/bin/env python3
"""
Generador de Reportes HTML para YNAB
Crea reportes visuales en HTML con gráficos y estadísticas
"""

import os
from datetime import datetime
from ynab_auto_categorizer import YNABAutoCategorizer

def generate_html_report(api_token: str, weeks_back: int = 1):
    """Genera un reporte HTML del período especificado"""
    
    categorizer = YNABAutoCategorizer(api_token)
    report = categorizer.get_weekly_report(weeks_back)
    
    # Calcular datos para gráfico
    categories = list(report['expenses_by_category'].keys())[:10]  # Top 10
    amounts = [report['expenses_by_category'][cat] for cat in categories]
    
    # Calcular porcentajes
    percentages = []
    if report['total_expenses'] > 0:
        percentages = [(amount / report['total_expenses'] * 100) for amount in amounts]
    
    html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte YNAB - {report['period']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        
        h1 {{
            color: #2d3748;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .period {{
            color: #718096;
            font-size: 1.1em;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .card h2 {{
            color: #4a5568;
            font-size: 1em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 15px;
        }}
        
        .amount {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .amount.income {{
            color: #48bb78;
        }}
        
        .amount.expense {{
            color: #f56565;
        }}
        
        .amount.balance {{
            color: #667eea;
        }}
        
        .amount.balance.negative {{
            color: #f56565;
        }}
        
        .category-list {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .category-item {{
            display: flex;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .category-item:last-child {{
            border-bottom: none;
        }}
        
        .category-name {{
            flex: 1;
            font-weight: 600;
            color: #2d3748;
        }}
        
        .category-amount {{
            margin: 0 20px;
            font-weight: bold;
            color: #4a5568;
        }}
        
        .category-bar {{
            flex: 1;
            max-width: 300px;
            height: 30px;
            background: #edf2f7;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }}
        
        .category-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: white;
            font-size: 0.85em;
            font-weight: bold;
            transition: width 0.5s ease;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.9;
        }}
        
        .transaction-count {{
            background: white;
            border-radius: 15px;
            padding: 20px 30px;
            margin-top: 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        
        .transaction-count .number {{
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .transaction-count .label {{
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Reporte Financiero YNAB</h1>
            <p class="period">{report['period']}</p>
        </div>
        
        <div class="summary">
            <div class="card">
                <h2>💰 Ingresos</h2>
                <div class="amount income">€{report['total_income']:,.2f}</div>
            </div>
            
            <div class="card">
                <h2>💸 Gastos</h2>
                <div class="amount expense">€{report['total_expenses']:,.2f}</div>
            </div>
            
            <div class="card">
                <h2>📈 Balance</h2>
                <div class="amount balance {'negative' if report['net'] < 0 else ''}">
                    €{report['net']:,.2f}
                </div>
                <p style="color: #718096; font-size: 0.9em;">
                    {'⚠️ Déficit' if report['net'] < 0 else '✅ Superávit'}
                </p>
            </div>
        </div>
        
        <div class="category-list">
            <h2 style="margin-bottom: 25px; color: #2d3748; font-size: 1.5em;">
                Gastos por Categoría
            </h2>
"""
    
    # Añadir categorías
    for i, category in enumerate(categories):
        amount = amounts[i]
        percentage = percentages[i] if percentages else 0
        
        html += f"""
            <div class="category-item">
                <div class="category-name">{category}</div>
                <div class="category-amount">€{amount:,.2f}</div>
                <div class="category-bar">
                    <div class="category-bar-fill" style="width: {percentage}%">
                        {percentage:.1f}%
                    </div>
                </div>
            </div>
"""
    
    html += f"""
        </div>
        
        <div class="transaction-count">
            <div class="number">{report['transaction_count']}</div>
            <div class="label">Transacciones totales</div>
        </div>
        
        <div class="footer">
            <p>Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}</p>
            <p>YNAB Auto-Categorizer 🏦</p>
        </div>
    </div>
    
    <script>
        // Animación de las barras al cargar
        window.addEventListener('load', function() {{
            const bars = document.querySelectorAll('.category-bar-fill');
            bars.forEach(bar => {{
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {{
                    bar.style.width = width;
                }}, 100);
            }});
        }});
    </script>
</body>
</html>
"""
    
    return html


def main():
    """Función principal"""
    API_TOKEN = os.getenv("YNAB_API_TOKEN", "TU_TOKEN_AQUI")
    
    if API_TOKEN == "TU_TOKEN_AQUI":
        print("⚠️  Por favor configura tu YNAB_API_TOKEN")
        print("   Puedes obtenerlo en: https://app.ynab.com/settings/developer")
        return
    
    print("🎨 Generando reporte HTML...")
    
    # Generar reporte de la última semana
    html = generate_html_report(API_TOKEN, weeks_back=1)
    
    # Guardar archivo
    filename = f"reporte_ynab_{datetime.now().strftime('%Y%m%d')}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Reporte generado: {filename}")
    print(f"   Abre el archivo en tu navegador para verlo")
    
    # Intentar abrir automáticamente
    import webbrowser
    try:
        webbrowser.open(filename)
        print(f"🌐 Abriendo en tu navegador...")
    except:
        pass


if __name__ == "__main__":
    main()
