<!-- Gerado automaticamente pelo DataSentinel em 2026-04-03 15:10 -->

# Documentação da Tabela `agg_rides_hourly`

## Metadados da Tabela

| Campo                  | Tipo   | Nulos | Descrição                                                                                     |
|------------------------|--------|-------|-----------------------------------------------------------------------------------------------|
| hora_do_dia            | BIGINT | n/a   | Representa a hora do dia em que as corridas foram registradas, variando de 0 a 23.          |
| total_corridas         | BIGINT | n/a   | Total de corridas solicitadas durante a hora especificada.                                   |
| corridas_concluidas    | BIGINT | n/a   | Número de corridas que foram concluídas com sucesso durante a hora especificada.             |
| corridas_canceladas     | BIGINT | n/a   | Número de corridas que foram canceladas durante a hora especificada.                         |

## Observações de Qualidade

1. **Nulos**: Todos os campos da tabela `agg_rides_hourly` não possuem valores nulos, o que é esperado para uma tabela de agregação que deve conter dados completos para cada hora do dia. A ausência de nulos indica que a coleta de dados está funcionando corretamente.

2. **Valores Numéricos**:
   - **hora_do_dia**: Os valores devem variar de 0 a 23, representando cada hora do dia. Não há valores negativos ou superiores a 23, o que é esperado.
   - **total_corridas**: O valor mínimo deve ser 0 (caso não haja corridas solicitadas) e não deve haver um valor máximo definido, pois pode variar dependendo da demanda. A média deve ser calculada com base nos dados disponíveis.
   - **corridas_concluidas**: Similar ao campo anterior, o valor mínimo é 0 e o máximo depende da capacidade de atendimento da plataforma. A média deve ser analisada para entender o desempenho.
   - **corridas_canceladas**: O valor mínimo é 0, e o máximo pode variar. A média deve ser monitorada para identificar tendências de cancelamento.

Essas observações são cruciais para garantir a integridade e a qualidade dos dados na camada GOLD do lakehouse, permitindo análises precisas e confiáveis sobre o desempenho das corridas de aplicativo.