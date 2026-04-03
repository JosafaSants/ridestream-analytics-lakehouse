<!-- Gerado automaticamente pelo DataSentinel em 2026-04-03 15:10 -->

# Metadados da Tabela `fct_rides_cancelled`

| Campo          | Tipo    | Descrição                                                                 |
|----------------|---------|---------------------------------------------------------------------------|
| ride_id        | VARCHAR | Identificador único da corrida cancelada. Utilizado para rastrear a corrida no sistema. |
| driver_id      | VARCHAR | Identificador único do motorista que estava associado à corrida cancelada. Permite identificar o motorista envolvido. |
| passenger_id   | VARCHAR | Identificador único do passageiro que solicitou a corrida cancelada. Usado para rastrear o usuário que fez a solicitação. |
| cancelled_at   | TIMESTAMP | Data e hora em que a corrida foi cancelada. Essencial para análises temporais e de comportamento do usuário. |
| origin_lat     | DOUBLE  | Latitude da localização de origem da corrida. Utilizado para análises geográficas e de demanda. |
| origin_lon     | DOUBLE  | Longitude da localização de origem da corrida. Complementa a latitude para determinar a posição geográfica. |
| year           | BIGINT  | Ano em que a corrida foi cancelada. Facilita a agregação e análise de dados por ano. |
| month          | BIGINT  | Mês em que a corrida foi cancelada. Permite análises mensais de cancelamentos. |
| day            | BIGINT  | Dia em que a corrida foi cancelada. Utilizado para análises diárias e identificação de padrões. |

## Observações de Qualidade

1. **Nulos**: Todos os campos da tabela `fct_rides_cancelled` têm 0% de nulos, o que é esperado e indica que os dados estão completos e prontos para análise. A ausência de nulos é um bom sinal de qualidade dos dados, especialmente em um contexto onde a integridade das informações é crítica para a tomada de decisões.

2. **Campos Numéricos**:
   - **origin_lat** e **origin_lon**: Os valores devem ser verificados para garantir que estão dentro dos limites válidos para coordenadas geográficas (latitude entre -90 e 90, longitude entre -180 e 180). A média, mínimo e máximo devem ser calculados para entender a distribuição geográfica das corridas canceladas.
   - **year**, **month** e **day**: Os valores devem ser consistentes com as datas das corridas. O ano deve estar dentro de um intervalo razoável (por exemplo, anos recentes), e os meses devem variar de 1 a 12, enquanto os dias devem ser válidos para os meses correspondentes.

3. **Análise Estatística**: Para uma análise mais aprofundada, recomenda-se calcular a média, mínimo e máximo dos campos numéricos, especialmente para `origin_lat` e `origin_lon`, a fim de identificar possíveis outliers ou padrões geográficos que possam impactar a operação da empresa.