<!-- Gerado automaticamente pelo DataSentinel em 2026-04-03 15:09 -->

# Metadados da Tabela `silver_ride_events`

| Campo         | Descrição                                                                                                                                                                                                 |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ride_id`     | Identificador único da corrida. Este campo é essencial para rastrear cada corrida individualmente no sistema.                                                                                             |
| `status`      | Status atual da corrida (ex: "completada", "cancelada", "em andamento"). Este campo é importante para entender a situação da corrida e para análises de desempenho.                                      |
| `timestamp`   | Data e hora em que a corrida foi registrada. Este campo permite a análise temporal das corridas, possibilitando insights sobre padrões de uso ao longo do tempo.                                          |
| `driver_id`   | Identificador único do motorista que realizou a corrida. Este campo é fundamental para associar corridas a motoristas específicos e para análises de desempenho de motoristas.                             |
| `passenger_id`| Identificador único do passageiro que solicitou a corrida. Assim como o `driver_id`, este campo é importante para associar corridas a passageiros e realizar análises de comportamento de usuários.      |
| `origin_lat`  | Latitude do ponto de origem da corrida. Este campo é crucial para determinar a localização inicial da corrida e para análises geoespaciais.                                                               |
| `origin_lon`  | Longitude do ponto de origem da corrida. Assim como `origin_lat`, este campo é essencial para a localização geográfica da corrida.                                                                         |
| `dest_lat`    | Latitude do ponto de destino da corrida. Este campo está com 100% de nulos, o que indica que não há informações de destino disponíveis. Isso pode ser um problema, pois limita a análise de trajetos.     |
| `dest_lon`    | Longitude do ponto de destino da corrida. Assim como `dest_lat`, este campo apresenta 100% de nulos, o que é um problema significativo para a análise de rotas e destinos das corridas.                  |
| `fare`        | Valor da corrida. Este campo é importante para análises financeiras e de receita, permitindo entender a variação de preços das corridas. Os valores variam de 8.01 a 120.0, com uma média de 65.8.       |
| `rating`      | Avaliação dada pelo passageiro ao motorista após a corrida. Com 83.47% de nulos, esse campo apresenta um problema, pois a falta de avaliações limita a análise de qualidade do serviço prestado.          |
| `year`        | Ano em que a corrida ocorreu. Este campo é consistente, com todos os registros em 2026, o que pode indicar um período específico de análise ou um erro na coleta de dados.                               |
| `month`       | Mês em que a corrida ocorreu. Todos os registros estão no mês de março, o que pode indicar um erro na coleta de dados ou uma análise restrita a um período específico.                                    |
| `day`         | Dia em que a corrida ocorreu. Todos os registros estão no dia 26, o que reforça a possibilidade de um erro na coleta de dados ou uma análise limitada a um único dia.                                    |

## Observações de Qualidade

1. **Campos com Nulos Altos**:
   - Os campos `dest_lat` e `dest_lon` apresentam 100% de nulos, o que é um problema significativo, pois impede a análise de trajetos e destinos das corridas. É necessário investigar a origem desses dados e implementar uma estratégia para coletar essas informações.
   - O campo `rating` possui 83.47% de nulos, o que também é preocupante, pois limita a capacidade de avaliar a qualidade do serviço. É importante entender por que as avaliações não estão sendo registradas e considerar a implementação de um processo para garantir que os passageiros avaliem as corridas.

2. **Valores Numéricos**:
   - Os campos `origin_lat` e `origin_lon` têm valores que fazem sentido geograficamente, com a latitude variando de -23.679949 a -23.460095 e a longitude de -46.81999 a -46.360209, com uma média que está dentro do esperado para a região metropolitana de São Paulo.
   - O campo `fare` apresenta uma variação de 8.01 a 120.0, com uma média de 65.8, o que sugere uma diversidade de preços, possivelmente refletindo diferentes tipos de corridas ou distâncias.
   - Os campos `year`, `month` e `day` estão todos com valores fixos, o que pode indicar um erro na coleta de dados ou uma limitação na análise temporal. É necessário revisar a origem desses dados para garantir que representem um conjunto de dados mais amplo.