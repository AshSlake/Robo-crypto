import pandas as pd
from rich.console import Console
import os


class DataCollector:
    def __init__(self, min_data_size=10):
        """
        Armazena os dados em um DataFrame até atingir um número mínimo de registros.
        - min_data_size: Número mínimo de registros necessários para treinamento
        - file_path: Caminho do arquivo CSV para salvar e carregar os dados
        """
        self.min_data_size = min_data_size
        self.console = Console()

        log_dir = "dataFrame"
        os.makedirs(log_dir, exist_ok=True)
        dfTraine = os.path.join(log_dir, "dfTraine")
        self.file_path = dfTraine + ".csv"

        # Se o arquivo existir, carregamos os dados; caso contrário, criamos um DataFrame vazio
        if os.path.exists(self.file_path):
            self.data_buffer = pd.read_csv(self.file_path)
            self.console.print(
                f"[bold green]Dados carregados do arquivo ({len(self.data_buffer)} registros).[/bold green]"
            )
        else:
            self.data_buffer = pd.DataFrame()

    def get_data(self):
        """Retorna os dados armazenados no DataFrame."""
        return self.data_buffer.copy()

    def check_data_availability(self):
        """Verifica se há o mínimo de dados necessários para treinamento."""
        if len(self.data_buffer) < self.min_data_size:
            self.console.print(
                f"[bold red]Ainda não há dados suficientes para treinamento. Temos {len(self.data_buffer)} dados.[/bold red]"
            )
        else:
            self.console.print(
                f"[bold green]Dados suficientes para treinamento ({len(self.data_buffer)} registros).[/bold green]"
            )

        return len(self.data_buffer) >= self.min_data_size

    def add_data(self, new_data):
        """Adiciona novos dados ao DataFrame e salva no arquivo."""
        if isinstance(new_data, dict):
            new_data_df = pd.DataFrame([new_data])
        elif isinstance(new_data, pd.DataFrame):
            new_data_df = new_data
        else:
            raise ValueError("Os dados precisam ser um dicionário ou um DataFrame.")

        self.data_buffer = pd.concat([self.data_buffer, new_data_df], ignore_index=True)

        # Salvar no arquivo para persistência
        self.data_buffer.to_csv(self.file_path, index=False)

        self.console.print(
            f"[bold green]Adicionado {len(new_data_df)} registros ao buffer. Total de registros: {len(self.data_buffer)}[/bold green]"
        )
