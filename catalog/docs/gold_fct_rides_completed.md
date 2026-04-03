<!-- Gerado automaticamente pelo DataSentinel em 2026-04-03 15:10 -->

# Metadados da Tabela `fct_rides_completed`

| Campo           | Descrição                                                                                                                                                     |
|-----------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ride_id         | Identificador único da corrida. Este campo é utilizado para rastrear e referenciar cada corrida individualmente no sistema.                                   |
| driver_id       | Identificador único do motorista que completou a corrida. Este campo permite associar a corrida ao motorista específico que a realizou.                      |
| passenger_id    | Identificador único do passageiro que solicitou a corrida. Este campo é utilizado para associar a corrida ao passageiro que a solicitou.                     |
| completed_at    | Data e hora em que a corrida foi concluída. Este campo é crucial para análises temporais e relatórios de desempenho.                                         |
| valor_corrida   | Valor monetário da corrida, representando o custo que o passageiro pagou. Este campo é importante para análises financeiras e de receita.                     |
| avaliacao       | Avaliação dada pelo passageiro ao motorista após a conclusão da corrida, em uma escala de 1 a 5. Este campo é utilizado para medir a satisfação do cliente. |
| origin_lat      | Latitude do ponto de origem da corrida. Este campo é essencial para geolocalização e análises de rotas.                                                     |
| origin_lon      | Longitude do ponto de origem da corrida. Assim como a latitude, este campo é importante para geolocalização e análises de rotas.                             |
| dest_lat        | Latitude do ponto de destino da corrida. Este campo é utilizado para determinar a localização final da corrida e para análises geográficas.                  |
| dest_lon        | Longitude do ponto de destino da corrida. Este campo complementa a latitude do destino para análises geográficas e de rotas.                                 |
| year            | Ano em que a corrida foi realizada. Este campo é utilizado para análises temporais e relatórios anuais.                                                     |
| month           | Mês em que a corrida foi realizada. Este campo é utilizado para análises mensais e relatórios de desempenho.                                                |
| day             | Dia em que a corrida foi realizada. Este campo é utilizado para análises diárias e relatórios de desempenho.                                                |

## Observações de Qualidade

1. **Nulos**: Todos os campos da tabela `fct_rides_completed` estão com a porcentagem de nulos em 0%. Isso é esperado, pois todos os campos são essenciais para a integridade dos dados e para a realização de análises significativas. A ausência de nulos indica que os dados foram coletados e processados corretamente.

2. **Campos Numéricos**:
   - **valor_corrida**: Os valores podem variar, mas é importante monitorar o mínimo e máximo para garantir que não haja anomalias (como valores negativos ou excessivamente altos). A média deve ser calculada para entender o ticket médio das corridas.
   - **avaliacao**: Os valores devem estar entre 1 e 5. A média deve ser analisada para entender a satisfação do cliente e identificar possíveis problemas com motoristas que têm avaliações consistentemente baixas.

3. **Análise de Valores**: Para uma análise mais aprofundada, recomenda-se calcular os valores mínimos, máximos e a média dos campos numéricos, especialmente `valor_corrida` e `avaliacao`, para identificar tendências e outliers que possam impactar a operação e a experiência do usuário.