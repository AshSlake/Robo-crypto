import google.generativeai as genai
import os


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
                            "Você é um analista de trading altamente especializado, com ampla experiência em mercados financeiros e criptomoedas. "
                            "Seu objetivo é analisar dados técnicos e fornecer estratégias precisas para tomada de decisão. "
                            "Com base nas informações a seguir, analise os dados e forneça uma decisão de compra, "
                            "venda ou manter a posição baseado na posição atual !SOMENTE UMA ESCOLHA JAMAIS MAIS DE UMA!, explicando seus motivos para a escolha. "
                            "Não use muitos caracteres para não ficar muito grande a resposta. "
                            f"Dados para análise:\n{self.dados}"
                        ),
                    }
                ]
            )

            # Envia a mensagem e coleta a resposta
            response = chat.send_message(self.dados, stream=True)

            # Processa a resposta do modelo
            decision = ""
            for chunk in response:
                decision += chunk.text

            return decision.strip()

        except Exception as e:
            raise RuntimeError(f"Erro ao processar os dados com o Gemini: {e}")
