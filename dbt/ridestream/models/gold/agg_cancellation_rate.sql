-- Modelo: agg_cancellation_rate
-- Camada: Gold
-- Descrição: Taxa de cancelamento por dia
-- Responde: a operação está saudável? Cancelamentos estão aumentando?
-- Fonte: Silver layer

{{
    config(
        materialized='table',
        tags=['gold', 'agregacao', 'qualidade']
    )
}}

with corridas_silver as (
    select *
    from read_parquet(
        'C:/Users/JosafaBarbosadosSant/ridestream-analytics-lakehouse/data/silver/ride_events/**/*.parquet',
        hive_partitioning = true
    )
),

-- Conta totais por dia e calcula a taxa de cancelamento
taxa_por_dia as (
    select
        year,
        month,
        day,
        count(*) as total_eventos,
        count(distinct ride_id) as total_corridas,
        count(case when status = 'cancelled' then 1 end) as total_cancelamentos,
        round(
            count(case when status = 'cancelled' then 1 end) * 100.0 / count(distinct ride_id),
            2
        ) as taxa_cancelamento_pct
    from corridas_silver
    group by year, month, day
    order by year, month, day
)

select * from taxa_por_dia
