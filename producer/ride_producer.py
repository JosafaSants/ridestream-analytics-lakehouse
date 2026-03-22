# =============================================================
# Bibliotecas necessárias para o producer funcionar
# =============================================================

import json  # converte o evento de corrida para texto antes de enviar ao Kafka
import time  # controla o intervalo entre cada evento enviado
import random  # sorteia valores aleatórios para simular corridas reais
import uuid  # gera IDs únicos para cada corrida — como o backend real faria
import os  # lê as variáveis de ambiente do arquivo .env

from datetime import datetime  # registra o momento exato do evento
from faker import Faker  # gera dados falsos mas realistas
from kafka import KafkaProducer  # conecta e envia mensagens para o Kafka
from dotenv import load_dotenv  # carrega as configurações do arquivo .env


# =============================================================
# Carrega as variáveis de ambiente definidas no arquivo .env
# Sem isso, os valores de KAFKA_BOOTSTRAP_SERVERS e KAFKA_TOPIC_RIDES
# não estariam disponíveis para o os.getenv() abaixo
# =============================================================
load_dotenv()

# Endereço do broker Kafka — onde o producer vai se conectar para enviar eventos
# Localmente aponta para o Docker; na AWS apontaria para o MSK
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Nome do tópico onde os eventos de corridas serão publicados
# O Kafka organiza mensagens em tópicos, como "filas" separadas por assunto
KAFKA_TOPIC_RIDES = os.getenv("KAFKA_TOPIC_RIDES", "ride-events")

# Configura o Faker para gerar dados no padrão brasileiro
# pt_BR garante nomes, cidades e telefones realistas do Brasil
fake = Faker("pt_BR")


# =============================================================
# Limites de latitude e longitude da cidade de São Paulo
# Usamos esses valores para gerar coordenadas realistas dentro da cidade
# -23.68 a -23.46 cobre do ABC Paulista até a Zona Norte
# -46.82 a -46.36 cobre de Osasco até o Itaim Paulista
# =============================================================
SP_LAT_MIN, SP_LAT_MAX = -23.68, -23.46
SP_LON_MIN, SP_LON_MAX = -46.82, -46.36


def gerar_evento_corrida() -> dict:
    """Gera um dicionário simulando um evento de corrida de app de transporte."""

    # Lista de status possíveis ao longo do ciclo de vida de uma corrida
    # É a mesma sequência que apps como Uber e 99 usam internamente
    status = random.choice(
        ["requested", "accepted", "arrived", "in_progress", "completed", "cancelled"]
    )

    return {
        # Identificador único da corrida — garante que nenhum evento se repita
        # uuid4 gera um ID aleatório de 128 bits, praticamente impossível de colidir
        "ride_id": str(uuid.uuid4()),
        # Estado atual da corrida no momento do evento
        "status": status,
        # Identificador único do motorista que aceitou a corrida
        "driver_id": str(uuid.uuid4()),
        # Identificador único do passageiro que solicitou a corrida
        "passenger_id": str(uuid.uuid4()),
        # Coordenadas do ponto de partida dentro de São Paulo
        # random.uniform sorteia um número decimal entre os limites da cidade
        "origin_lat": round(random.uniform(SP_LAT_MIN, SP_LAT_MAX), 6),
        "origin_lon": round(random.uniform(SP_LON_MIN, SP_LON_MAX), 6),
        # Coordenadas do destino — independentes da origem para simular qualquer trajeto
        "destination_lat": round(random.uniform(SP_LAT_MIN, SP_LAT_MAX), 6),
        "destination_lon": round(random.uniform(SP_LON_MIN, SP_LON_MAX), 6),
        # Momento exato em que o evento foi gerado, no formato ISO 8601
        # Esse timestamp é o que o Spark vai usar para janelas de tempo no streaming
        "timestamp": datetime.now().isoformat(),
        # Valor da corrida em reais — entre R$8 (corrida curta) e R$120 (corrida longa)
        # round(..., 2) garante no máximo duas casas decimais, como um valor real de app
        "fare": round(random.uniform(8.0, 120.0), 2),
        # Avaliação do passageiro após a corrida (1 a 5 estrelas)
        # Só faz sentido existir quando a corrida foi concluída — nos demais casos é None
        "rating": round(random.uniform(1.0, 5.0), 1) if status == "completed" else None,
    }


def criar_producer() -> KafkaProducer:
    """Instancia e retorna um KafkaProducer conectado ao broker configurado."""
    try:
        producer = KafkaProducer(
            # Endereço do broker — pode ser o Docker local ou o MSK na AWS
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,

            # Serializa o dicionário Python para JSON e depois para bytes
            # O Kafka só trafega bytes — essa função é chamada automaticamente a cada envio
            value_serializer=lambda evento: json.dumps(evento).encode("utf-8"),
        )

        print(f"✅ Producer conectado ao Kafka em {KAFKA_BOOTSTRAP_SERVERS}")
        return producer

    except Exception as erro:
        # Se o Kafka não estiver rodando (ex: Docker parado), o programa para aqui
        # com uma mensagem clara — evita um erro genérico difícil de depurar
        print(f"❌ Erro ao conectar no Kafka: {erro}")
        print("💡 Verifique se o Docker está rodando: docker compose -f infra/docker-compose.yml up -d")
        raise


def main():
    """Conecta ao Kafka e publica eventos de corrida em loop contínuo."""

    # Cria a conexão com o Kafka — se falhar, o erro já é tratado dentro de criar_producer()
    producer = criar_producer()

    print(f"🚀 Iniciando envio de eventos para o tópico '{KAFKA_TOPIC_RIDES}'...")
    print("   Pressione Ctrl+C para encerrar.\n")

    try:
        while True:
            # Gera um novo evento de corrida com dados aleatórios
            evento = gerar_evento_corrida()

            # Publica o evento no tópico do Kafka
            # O value_serializer definido em criar_producer() converte o dict para bytes automaticamente
            producer.send(KAFKA_TOPIC_RIDES, value=evento)

            # Exibe um resumo no terminal para acompanhar o fluxo em tempo real
            print(f"📨 Evento enviado | status: {evento['status']:<12} | ride_id: {evento['ride_id']}")

            # Aguarda 1 segundo antes do próximo evento
            # Simula a cadência de um app real sem sobrecarregar o broker local
            time.sleep(1)

    except KeyboardInterrupt:
        # Ctrl+C capturado — encerra o loop de forma controlada
        print("\n⏹️  Encerramento solicitado pelo usuário.")

    finally:
        # Garante que todas as mensagens em buffer sejam entregues antes de fechar
        # sem o flush(), eventos gerados nos últimos milissegundos poderiam se perder
        producer.flush()
        producer.close()
        print("✅ Producer encerrado com sucesso.")


# Ponto de entrada do script
# Permite importar as funções em outros módulos sem disparar o loop automaticamente
if __name__ == "__main__":
    main()
