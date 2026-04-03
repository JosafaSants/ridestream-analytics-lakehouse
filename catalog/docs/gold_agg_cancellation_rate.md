<!-- Gerado automaticamente pelo DataSentinel em 2026-04-03 15:10 -->

# Metadados da Tabela `agg_cancellation_rate`

| Campo                   | Tipo    | Descrição                                                                                                                                                      |
|-------------------------|---------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| year                    | BIGINT  | Representa o ano em que os dados foram coletados. É fundamental para análise temporal das taxas de cancelamento.                                              |
| month                   | BIGINT  | Representa o mês em que os dados foram coletados. Permite a análise mensal das taxas de cancelamento, facilitando a identificação de tendências sazonais.    |
| day                     | BIGINT  | Representa o dia do mês em que os dados foram coletados. Essencial para análises diárias e identificação de padrões de cancelamento em dias específicos.     |
| total_eventos           | BIGINT  | Total de eventos registrados no período, que podem incluir corridas, cancelamentos e outras interações. Ajuda a entender o volume total de atividades.       |
| total_corridas          | BIGINT  | Total de corridas realizadas no período. Este campo é crucial para calcular a taxa de cancelamento e avaliar a performance do serviço.                       |
| total_cancelamentos      | BIGINT  | Total de corridas que foram canceladas no período. Permite calcular a taxa de cancelamento e entender a insatisfação dos usuários.                           |
| taxa_cancelamento_pct    | DOUBLE  | Percentual de cancelamentos em relação ao total de corridas. Este campo é um indicador chave de desempenho (KPI) para a operação, refletindo a eficiência do serviço. |

## Observações de Qualidade

1. **Nulos**: Todos os campos têm nulos em 0%, o que é esperado para esta tabela, pois todos os dados são essenciais para a análise da taxa de cancelamento. A ausência de nulos indica que a coleta de dados foi realizada de forma completa e consistente.

2. **Valores Numéricos**:
   - `total_eventos`: O valor mínimo e máximo deve ser verificado no contexto de dados, mas espera-se que o total de eventos seja um número positivo, refletindo a atividade do serviço.
   - `total_corridas`: Similarmente, deve ser um número positivo. A média deve ser analisada em relação ao volume de usuários e à frequência de uso do aplicativo.
   - `total_cancelamentos`: Este campo deve ser menor ou igual ao total de corridas. A média deve ser monitorada para identificar tendências de cancelamento.
   - `taxa_cancelamento_pct`: Este valor deve estar entre 0 e 100, representando a porcentagem de cancelamentos. A média deve ser analisada em comparação com benchmarks do setor para avaliar a performance.

Essas observações são cruciais para garantir a integridade e a utilidade dos dados na análise de desempenho do serviço de ride-hailing.