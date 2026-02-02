from flask import Flask, render_template_string, request, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Dados fictícios de recall (você pode aumentar depois)
RECALL_DATABASE = {
    "FIAT": {
        "MOBI": ["2020-2022", "Problema no sistema de freios"],
        "ARGO": ["2019-2021", "Retenção de líquido no para-brisa"]
    },
    "VOLKSWAGEN": {
        "GOL": ["2018-2020", "Correia dentada"],
        "POLO": ["2019-2021", "Sensor de combustível"]
    },
    "CHEVROLET": {
        "ONIX": ["2020-2022", "Sistema elétrico"],
        "TRACKER": ["2021-2023", "Suspensão dianteira"]
    }
}

# Checklist base por tipo de veículo
CHECKLIST_TEMPLATES = {
    "CARRO": [
        "Óleo do motor",
        "Filtro de ar",
        "Pastilhas de freio",
        "Pneus (pressão e desgaste)",
        "Bateria",
        "Líquido de arrefecimento",
        "Palhetas do para-brisa",
        "Luzes (faróis, setas, freio)",
        "Alinhamento e balanceamento",
        "Sistema de escapamento"
    ],
    "MOTO": [
        "Óleo do motor",
        "Corrente",
        "Pneus",
        "Freios",
        "Velas",
        "Bateria",
        "Suspensão",
        "Faróis e piscas",
        "Comando de acelerador",
        "Cabos e conexões"
    ]
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Checklist Oficina - Anápolis/GO</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .content {
            padding: 40px;
        }
        
        .form-section {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        .input-group {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .input-field {
            display: flex;
            flex-direction: column;
        }
        
        label {
            font-weight: 600;
            margin-bottom: 8px;
            color: #2c3e50;
        }
        
        input, select {
            padding: 12px 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border 0.3s;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 18px;
            border-radius: 8px;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
            font-weight: 600;
            width: 100%;
            margin-top: 10px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .checklist-section {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 10px;
            padding: 25px;
            margin-top: 30px;
        }
        
        .recall-alert {
            background: #fff3cd;
            border: 2px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }
        
        .checklist-item {
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }
        
        .checklist-item:last-child {
            border-bottom: none;
        }
        
        .checklist-item input[type="checkbox"] {
            margin-right: 15px;
            width: 20px;
            height: 20px;
        }
        
        .print-btn {
            background: #28a745;
            margin-top: 20px;
        }
        
        .whatsapp-btn {
            background: #25D366;
            margin-top: 10px;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.9rem;
            border-top: 1px solid #dee2e6;
            margin-top: 30px;
        }
        
        @media print {
            .no-print { display: none; }
            body { background: white; }
            .container { box-shadow: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Checklist Digital</h1>
            <p>Sistema profissional para oficinas de Anápolis/GO</p>
        </div>
        
        <div class="content">
            <div class="form-section">
                <h2 style="margin-bottom: 25px; color: #2c3e50;">📋 Dados do Veículo</h2>
                
                <form id="vehicleForm">
                    <div class="input-group">
                        <div class="input-field">
                            <label for="placa">Placa do Veículo:</label>
                            <input type="text" id="placa" name="placa" placeholder="AAA-0A00" required 
                                   style="text-transform: uppercase;">
                        </div>
                        
                        <div class="input-field">
                            <label for="marca">Marca:</label>
                            <select id="marca" name="marca" required>
                                <option value="">Selecione...</option>
                                <option value="FIAT">FIAT</option>
                                <option value="VOLKSWAGEN">Volkswagen</option>
                                <option value="CHEVROLET">Chevrolet</option>
                                <option value="FORD">Ford</option>
                                <option value="HONDA">Honda</option>
                                <option value="TOYOTA">Toyota</option>
                                <option value="HYUNDAI">Hyundai</option>
                                <option value="OUTRA">Outra</option>
                            </select>
                        </div>
                        
                        <div class="input-field">
                            <label for="modelo">Modelo:</label>
                            <input type="text" id="modelo" name="modelo" placeholder="Ex: Gol, Onix, etc." required>
                        </div>
                        
                        <div class="input-field">
                            <label for="ano">Ano:</label>
                            <input type="number" id="ano" name="ano" min="1990" max="2024" 
                                   placeholder="2023" required>
                        </div>
                        
                        <div class="input-field">
                            <label for="tipo">Tipo de Veículo:</label>
                            <select id="tipo" name="tipo" required>
                                <option value="CARRO">Carro</option>
                                <option value="MOTO">Moto</option>
                                <option value="CAMINHAO">Caminhão</option>
                                <option value="OUTRO">Outro</option>
                            </select>
                        </div>
                        
                        <div class="input-field">
                            <label for="km">Quilometragem:</label>
                            <input type="number" id="km" name="km" placeholder="Ex: 45000">
                        </div>
                    </div>
                    
                    <button type="submit" class="btn no-print">Gerar Checklist</button>
                </form>
            </div>
            
            <div class="recall-alert" id="recallAlert">
                ⚠️ <strong>ATENÇÃO:</strong> Este veículo possui recall ativo. 
                <span id="recallDetails"></span>
            </div>
            
            <div class="checklist-section" id="checklistSection" style="display: none;">
                <h2 style="margin-bottom: 20px; color: #2c3e50;">
                    📝 Checklist de Serviços
                    <span style="font-size: 14px; color: #666;" id="vehicleInfo"></span>
                </h2>
                
                <div id="checklistItems"></div>
                
                <div style="margin-top: 30px;">
                    <label for="observacoes">Observações Adicionais:</label>
                    <textarea id="observacoes" rows="4" 
                              style="width: 100%; padding: 15px; border: 2px solid #ddd; border-radius: 8px; margin-top: 10px;"
                              placeholder="Anote aqui qualquer observação importante..."></textarea>
                </div>
                
                <div style="margin-top: 30px;">
                    <button onclick="window.print()" class="btn print-btn no-print">
                        🖨️ Imprimir Checklist
                    </button>
                    
                    <button onclick="enviarWhatsApp()" class="btn whatsapp-btn no-print">
                        📱 Enviar por WhatsApp
                    </button>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Desenvolvido para oficinas de Anápolis/GO • Versão 1.0</p>
            <p>Sistema 100% online • Não requer instalação</p>
        </div>
    </div>

    <script>
        document.getElementById('vehicleForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const placa = document.getElementById('placa').value;
            const marca = document.getElementById('marca').value;
            const modelo = document.getElementById('modelo').value;
            const ano = document.getElementById('ano').value;
            const tipo = document.getElementById('tipo').value;
            const km = document.getElementById('km').value;
            
            // Mostrar seção do checklist
            document.getElementById('checklistSection').style.display = 'block';
            
            // Atualizar informações do veículo
            document.getElementById('vehicleInfo').textContent = 
                ` | Placa: ${placa.toUpperCase()} | ${marca} ${modelo} | Ano: ${ano}`;
            
            // Verificar recall
            verificarRecall(marca, modelo, ano);
            
            // Gerar checklist
            gerarChecklist(tipo);
            
            // Rolar até o checklist
            document.getElementById('checklistSection').scrollIntoView({ behavior: 'smooth' });
        });
        
        function verificarRecall(marca, modelo, ano) {
            // Em uma versão real, isso viria de uma API
            // Aqui é apenas simulação
            
            const recallAlert = document.getElementById('recallAlert');
            const recallDetails = document.getElementById('recallDetails');
            
            // Simulação: Checar se tem recall
            const temRecall = Math.random() > 0.7; // 30% de chance para exemplo
            
            if (temRecall) {
                recallAlert.style.display = 'block';
                recallDetails.textContent = ` ${marca} ${modelo} (${ano}) - Verificar sistema de freios.`;
            } else {
                recallAlert.style.display = 'none';
            }
        }
        
        function gerarChecklist(tipo) {
            const container = document.getElementById('checklistItems');
            container.innerHTML = '';
            
            let checklist = [];
            
            if (tipo === 'CARRO') {
                checklist = [
                    "Óleo do motor - Verificar nível e condição",
                    "Filtro de ar - Substituir se necessário",
                    "Pastilhas de freio - Medir espessura",
                    "Pneus - Verificar pressão e desgaste",
                    "Bateria - Testar carga e limpar bornes",
                    "Líquido de arrefecimento - Verificar nível",
                    "Palhetas do para-brisa - Testar eficiência",
                    "Luzes - Faróis, setas, freio e ré",
                    "Alinhamento e balanceamento - Verificar necessidade",
                    "Sistema de escapamento - Verificar vazamentos"
                ];
            } else if (tipo === 'MOTO') {
                checklist = [
                    "Óleo do motor - Trocar se necessário",
                    "Corrente - Verificar tensão e lubrificar",
                    "Pneus - Pressão e desgaste",
                    "Freios - Pastilhas e fluido",
                    "Velas - Verificar e limpar",
                    "Bateria - Testar carga",
                    "Suspensão - Verificar amortecedores",
                    "Faróis e piscas - Funcionamento",
                    "Comando de acelerador - Folga",
                    "Cabos e conexões - Estado geral"
                ];
            } else {
                checklist = [
                    "Verificação geral do veículo",
                    "Sistemas de segurança",
                    "Documentação em dia",
                    "Nível de combustível",
                    "Limpeza interna e externa"
                ];
            }
            
            checklist.forEach((item, index) => {
                const div = document.createElement('div');
                div.className = 'checklist-item';
                div.innerHTML = `
                    <input type="checkbox" id="item${index}" name="item${index}">
                    <label for="item${index}" style="flex: 1; cursor: pointer;">${item}</label>
                `;
                container.appendChild(div);
            });
        }
        
        function enviarWhatsApp() {
            const placa = document.getElementById('placa').value;
            const modelo = document.getElementById('modelo').value;
            
            // Pegar itens marcados
            const itensMarcados = [];
            const checkboxes = document.querySelectorAll('input[type="checkbox"]:checked');
            checkboxes.forEach(cb => {
                const label = cb.nextElementSibling.textContent;
                itensMarcados.push(`✅ ${label}`);
            });
            
            const texto = `Checklist para ${modelo} - Placa: ${placa}%0A%0A${itensMarcados.join('%0A')}`;
            
            // Abrir WhatsApp Web (ajuste o número depois)
            window.open(`https://wa.me/5562999999999?text=${texto}`, '_blank');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/check-recall', methods=['POST'])
def check_recall():
    data = request.json
    marca = data.get('marca', '').upper()
    modelo = data.get('modelo', '').upper()
    ano = data.get('ano', '')
    
    recall_info = RECALL_DATABASE.get(marca, {}).get(modelo, None)
    
    if recall_info and ano:
        anos_recall = recall_info[0]
        if "-" in anos_recall:
            inicio, fim = map(int, anos_recall.split("-"))
            if inicio <= int(ano) <= fim:
                return jsonify({
                    "has_recall": True,
                    "details": recall_info[1]
                })
    
    return jsonify({"has_recall": False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
