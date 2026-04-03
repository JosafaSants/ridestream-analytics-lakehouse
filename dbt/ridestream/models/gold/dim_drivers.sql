-- Modelo: dim_drivers
-- Camada: Gold
-- Descrição: Dimensão de motoristas com métricas agregadas
-- Cada linha representa um motorista único com seu desempenho histórico
-- Fonte: fct_rides_completed (corridas concluídas já filtradas)

{{
    config(
        materialized='table',
        tags=['gold', 'dimensao', 'motorista']
    )
}}

-- Referencia outro modelo Gold já materializado — o dbt resolve a ordem de execução
with base as (
    select
        driver_id,
        valor_corrida,
        avaliacao
    from {{ ref('fct_rides_completed') }}
),

-- Agrega métricas por motorista: quantas corridas fez, quanto faturou, qual sua nota média
metricas_motorista as (
    select
        driver_id,
        count(*) as total_corridas,
        round(sum(valor_corrida), 2) as receita_total,
        round(avg(valor_corrida), 2) as ticket_medio,
        round(avg(avaliacao), 2) as avaliacao_media
    from base
    group by driver_id
)

select * from metricas_motorista
