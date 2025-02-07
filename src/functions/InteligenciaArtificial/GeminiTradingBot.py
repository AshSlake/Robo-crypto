import google.generativeai as genai
import os
from tabulate import tabulate
import textwrap
from rich.console import Console
from files import palavras_ignorar


class GeminiTradingBot:
    def __init__(self, dados):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.dados = dados

    def geminiTrader(self):
        # Verifica se a chave de API está configurada
        if not self.api_key:
            raise ValueError(
                "A chave de API do Gemini não foi encontrada. Configure GEMINI_API_KEY no ambiente."
            )

        # Valida os dados fornecidos
        if not isinstance(self.dados, str) or not self.dados.strip():
            raise ValueError("Os dados para análise devem ser uma string não vazia.")

        # Configura a API do Gemini
        try:
            genai.configure(api_key=self.api_key)
        except Exception as e:
            raise RuntimeError(f"Erro ao configurar a API do Gemini: {e}")

        try:
            # Inicializa o modelo de chat
            model = genai.GenerativeModel("gemini-1.5-flash")
            chat = model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": (
                            "Você é um analista de trading altamente especializado, com ampla experiência em mercados financeiros e criptomoedas."
                            "Seu objetivo é analisar dados técnicos e fornecer a melhor decisão entre **manter, comprar ou vender**. "
                            "🔹 **IMPORTANTE:**  "
                            " - **Diga a decisão na PRIMEIRA LINHA da resposta, isolada explicações nas demais linhas.**  "
                            " - **Use apenas UMA das palavras: comprar, vender ou manter.**"
                            " - **Não use essas palavras para explicar outros conceitos ou fazer comparações.**"
                            "📊 **Análise Técnica:**"
                            "- Priorize **pontos de entrada estratégicos**, considerando tendências e padrões de candles. "
                            "- Se houver uma reversão clara ou forte tendência, ajuste a decisão conforme necessário. "
                            "- Fique atento a **cruzamento de médias móveis, suporte/resistência, volume e RSI.**  "
                            "- Busque maximizar ganhos identificando **melhores momentos para entrar e sair** da posição."
                            "tente ao maximo fazer holding ao estar comprado"
                            "baseado nos mesmos dados fornecidos um bot trader ira passar a opnião dele de compra,venda ou manter posição,utilize a analise dele como reforço para a sua!"
                            "um modelo machine learning está passando dados de compra,venda ou manter posição leve em consideração os dados dele tambem!"
                            "!!LEVE EM CONSIDERAÇÃO OS DADOS DOS BOT E DO MODELO DE APRENDZADO!!\n"
                            "🔍 **Dados do mercado junto dos dados do bot e do modelo de aprendizado:** "
                            f"{self.dados}"
                        ),
                    }
                ]
            )

            # Envia a mensagem e coleta a resposta
            response = chat.send_message(self.dados, stream=True)
            console = Console()

            # Processa a resposta do modelo
            decision = ""
            for chunk in response:
                decision += chunk.text

            # Formata a resposta para exibição em tabela
            print(f"\n ==> Resposta do modelo sem formatação: '{decision}'")
            formatted_response = self.format_response_as_table(decision)
            try:
                # Converte a decisão para booleano
                decision_bool = self.convert_decision_to_bool(decision)

                # Formata a mensagem para o console
                message = (
                    f"\n ==> Resposta do modelo: '{decision}'\n"
                    f" ==> Resultado: "
                    + (
                        "Compra"
                        if decision_bool is True
                        else "Venda" if decision_bool is False else "Manter"
                    )
                )

                # Exibe no console com estilo apropriado
                console.print(
                    message,
                    style=(
                        "bold green"
                        if decision_bool
                        else "bold red" if decision_bool is False else "bold yellow"
                    ),
                )

            except ValueError as e:
                # Tratamento para erro de decisão inválida
                print(f"Erro ao processar decisão: {e}")
                decision_bool = None

            # Retorna a resposta formatada e o resultado booleano
            return formatted_response, decision_bool

        except Exception as e:
            # Tratamento para erros gerais
            print(f"Erro ao processar os dados com o Gemini: {e}")
            return None, None

    def convert_decision_to_bool(self, decision_text):
        """
        Transforma a decisão de texto em um valor booleano.
        Retorna:
            - True para 'comprar'.
            - False para 'vender'.
            - None para 'manter'.

        Ignora palavras irrelevantes como 'sobrevendido', 'sobrecomprado', etc.
        Levanta ValueError para respostas inválidas ou incompletas.
        """
        # Normaliza a entrada
        decision_text = decision_text.split("\n")[0].lower()

        for palavra in palavras_ignorar.filtrar_palavras_irrelevantes():
            decision_text = decision_text.replace(palavra, "")

        # Verifica padrões de texto para decisões
        if "comprar" in decision_text or "compra" in decision_text:
            return True  # Sinal de compra
        if "vender" in decision_text or "venda" in decision_text:
            return False  # Sinal de venda
        if (
            "manter" in decision_text
            or "segurar" in decision_text
            or "aguardar" in decision_text
            or " Mais observação é necessária antes de assumir uma posição"
            in decision_text
        ):
            return None  # Sinal de manutenção

        # Caso a decisão seja inválida ou desconhecida
        raise ValueError(
            f"Decisão inválida ou incompleta fornecida pelo Gemini: '{decision_text}'"
        )

    @staticmethod
    def format_response_as_table(response, max_line_length=50):
        # Inicializa os insights com valores padrão
        insights = {
            "Decisão": "",
            "Média Rápida": "",
            "Média Lenta": "",
            "RSI": "",
            "Gradiente Rápido": "",
            "Volatilidade": "",
            "Motivo": "",
        }

        # Variáveis auxiliares para captura da decisão
        decision_keywords = ["manter", "comprar", "vender"]
        decision_found = False

        # Parsing da resposta (baseado no texto de exemplo fornecido)
        for line in response.split(". "):  # Divide o texto em frases
            line = line.strip()  # Remove espaços desnecessários
            try:
                # Identifica a decisão principal
                if not decision_found:
                    for keyword in decision_keywords:
                        if keyword in line.lower():
                            insights["Decisão"] = keyword.capitalize()
                            decision_found = True
                            break

                # Agora, captura os outros campos como médias, RSI, gradiente, etc.
                if "média rápida" in line.lower() and "média lenta" in line.lower():
                    if ">" in line and "(" in line and ")" in line:
                        insights["Média Rápida"] = (
                            line.split("(")[1].split(">")[0].strip()
                        )
                        insights["Média Lenta"] = (
                            line.split(">")[1].split(")")[0].strip()
                        )
                elif "RSI" in line and "(" in line and ")" in line:
                    insights["RSI"] = line.split("(")[1].split(")")[0].strip()
                elif "gradiente rápido" in line.lower():
                    if "(" in line and ")" in line:
                        insights["Gradiente Rápido"] = (
                            line.split("(")[1].split(")")[0].strip()
                        )
                elif "volatilidade" in line.lower():
                    if "(" in line and ")" in line:
                        insights["Volatilidade"] = (
                            line.split("(")[1].split(")")[0].strip()
                        )
                else:
                    # Adiciona qualquer outra informação ao motivo
                    if "decisão" not in line.lower():
                        insights["Motivo"] += line.strip() + ". "
            except (IndexError, ValueError) as e:
                # Ignora linhas que não seguem o formato esperado
                insights["Motivo"] += f"(Erro ao processar esta linha: {line}). "

        # Formata a justificativa (campo "Motivo") para quebre de linha
        if insights["Motivo"]:
            insights["Motivo"] = textwrap.fill(
                insights["Motivo"], width=max_line_length
            )

        # Remove entradas vazias ou não preenchidas
        insights = {key: value for key, value in insights.items() if value}

        # Converte os insights em uma tabela
        data = [[key, value] for key, value in insights.items()]
        return tabulate(data, headers=["Campo", "Valor"], tablefmt="grid")
